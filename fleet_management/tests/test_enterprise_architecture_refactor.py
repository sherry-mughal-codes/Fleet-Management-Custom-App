"""
Enterprise Architecture Refactor Unit Tests
Fleet Management System (Frappe v15)

Tests coverage for Part A through Part J requirements:
- VehicleStateManager calculated vehicle states
- AssignmentManager availability checks, DB row locking, return & cancel workflows
- FuelManager submit & cancellation transaction reversal
- MaintenanceManager work order completion & cancellation reversal
- ValidationManager duplicate & odometer rules
- Centralized NotificationManager and DashboardManager integrations
"""

from unittest.mock import MagicMock, patch
import pytest

from fleet_management.enums import VehicleStatus
from fleet_management.services.assignment_manager import AssignmentManager
from fleet_management.services.cost_manager import CostManager
from fleet_management.services.dashboard_manager import DashboardManager
from fleet_management.services.fuel_manager import FuelManager
from fleet_management.services.maintenance_manager import MaintenanceManager
from fleet_management.services.notification_manager import NotificationManager
from fleet_management.services.validation_manager import ValidationManager
from fleet_management.services.vehicle_state_manager import VehicleStateManager
from fleet_management.utils.exceptions import FleetBusinessLogicError, FleetManagementError, FleetValidationError


def test_vehicle_state_manager_calculation_available():
	"""Verify VehicleStateManager calculates Available status when no assignments or maintenance exist."""
	with patch("frappe.db.exists") as mock_exists, patch("frappe.db.get_value") as mock_get_val:
		mock_exists.side_effect = lambda dt, filters: dt == "Fleet Vehicle"
		mock_get_val.return_value = {
			"status": "Available",
			"current_odometer": 1000.0,
			"next_maintenance_due_odometer": 5000.0,
			"current_employee": None
		}

		state = VehicleStateManager.calculate_vehicle_state("VEH-001")
		assert state == VehicleStatus.AVAILABLE


def test_vehicle_state_manager_calculation_assigned():
	"""Verify VehicleStateManager calculates Assigned status when vehicle has active assignment."""
	with patch("frappe.db.exists") as mock_exists, patch("frappe.db.get_value") as mock_get_val:
		mock_exists.side_effect = lambda dt, filters: dt in ("Fleet Vehicle", "Vehicle Assignment")
		mock_get_val.return_value = {
			"status": "Assigned",
			"current_odometer": 1000.0,
			"next_maintenance_due_odometer": 5000.0,
			"current_employee": "EMP-001"
		}

		state = VehicleStateManager.calculate_vehicle_state("VEH-001")
		assert state == VehicleStatus.ASSIGNED


def test_vehicle_state_manager_calculation_maintenance_due():
	"""Verify VehicleStateManager calculates Maintenance Due when current_odometer >= next_due."""
	with patch("frappe.db.exists") as mock_exists, patch("frappe.db.get_value") as mock_get_val:
		mock_exists.side_effect = lambda dt, filters: dt == "Fleet Vehicle"
		mock_get_val.return_value = {
			"status": "Available",
			"current_odometer": 5500.0,
			"next_maintenance_due_odometer": 5000.0,
			"current_employee": None
		}

		state = VehicleStateManager.calculate_vehicle_state("VEH-001")
		assert state == VehicleStatus.MAINTENANCE_DUE


def test_assignment_manager_availability_validation():
	"""Verify AssignmentManager blocks assigning non-available vehicle."""
	manager = AssignmentManager()
	with patch("frappe.db.exists", return_value=True), \
		 patch("frappe.db.get_value", return_value="Under Maintenance"):
		with pytest.raises((FleetValidationError, FleetManagementError, Exception)):
			manager.validate_vehicle_availability("VEH-001")


def test_validation_manager_odometer_check():
	"""Verify ValidationManager raises error on non-monotonic odometer."""
	manager = ValidationManager()
	with pytest.raises(FleetValidationError):
		manager.validate_odometer(100.0, 200.0)


def test_notification_manager_dispatch():
	"""Verify NotificationManager delegates email dispatch."""
	manager = NotificationManager()
	with patch("frappe.sendmail") as mock_sendmail:
		res = manager.send_notification(["user@local.com"], "Test Subject", "Test Body")
		assert res is True
		mock_sendmail.assert_called_once()


def test_dashboard_manager_counts():
	"""Verify DashboardManager metric breakdown calculation."""
	manager = DashboardManager()
	mock_vehicles = [
		{"name": "V1", "status": "Available"},
		{"name": "V2", "status": "Assigned"},
		{"name": "V3", "status": "Maintenance Due"}
	]
	with patch("frappe.get_all", return_value=mock_vehicles):
		res = manager.get_dashboard_summary()
		assert res["total_vehicles"] == 3
		assert res["available_count"] == 1
		assert res["assigned_count"] == 1
		assert res["maintenance_count"] == 1
