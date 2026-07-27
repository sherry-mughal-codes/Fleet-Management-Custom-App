"""
Unit tests for automatic vehicle status updates upon Maintenance Work Order lifecycle transitions.
"""

from unittest.mock import MagicMock, patch

from fleet_management.enums import MaintenanceStatus, VehicleStatus
from fleet_management.services.maintenance_service import MaintenanceService
from fleet_management.services.vehicle_service import (
	is_vehicle_assigned,
	update_vehicle_status_on_maintenance_change,
)


def test_is_vehicle_assigned():
	"""Test helper returns True when vehicle is assigned, False otherwise."""
	with patch("frappe.db.exists") as mock_exists, patch("frappe.db.get_value") as mock_get_value:
		mock_exists.return_value = True

		# 1. Assigned via current_employee
		mock_get_value.side_effect = lambda dt, name, field: "EMP-001" if field == "current_employee" else None
		assert is_vehicle_assigned("VEH-001") is True

		# 2. Assigned via current_assignment_status
		mock_get_value.side_effect = lambda dt, name, field: "Assigned" if field == "current_assignment_status" else None
		assert is_vehicle_assigned("VEH-001") is True

		# 3. Assigned via active Vehicle Assignment record
		mock_get_value.side_effect = lambda dt, name, field: None
		mock_exists.side_effect = lambda dt, filters: True if dt == "Vehicle" or dt == "Vehicle Assignment" else False
		assert is_vehicle_assigned("VEH-001") is True

		# 4. Unassigned
		mock_get_value.side_effect = lambda dt, name, field: None
		mock_exists.side_effect = lambda dt, filters: True if dt == "Vehicle" else False
		assert is_vehicle_assigned("VEH-001") is False


def test_work_order_creation_sets_under_maintenance():
	"""Verify work order creation against an Available/Maintenance Due vehicle sets status to Under Maintenance."""
	with patch("frappe.db.exists", return_value=True), \
		 patch("frappe.db.get_value", return_value=VehicleStatus.AVAILABLE), \
		 patch("fleet_management.services.vehicle_service.VehicleService.change_status") as mock_change_status:

		doc = MagicMock()
		doc.vehicle = "VEH-001"
		doc.name = "MWO-0001"
		doc.status = MaintenanceStatus.DRAFT

		update_vehicle_status_on_maintenance_change(doc)

		mock_change_status.assert_called_once_with(
			"VEH-001",
			VehicleStatus.UNDER_MAINTENANCE,
			reason="Maintenance Work Order 'MWO-0001' created/active"
		)


def test_completed_work_order_unassigned_vehicle_sets_available():
	"""Verify completed work order against unassigned vehicle in Under Maintenance sets status to Available."""
	with patch("frappe.db.exists", return_value=True), \
		 patch("frappe.db.get_value", side_effect=lambda dt, name, field=None: VehicleStatus.UNDER_MAINTENANCE if dt == "Vehicle" and field == "status" else None), \
		 patch("fleet_management.services.vehicle_service.is_vehicle_assigned", return_value=False), \
		 patch("fleet_management.services.vehicle_service.VehicleService.change_status") as mock_change_status, \
		 patch("frappe.db.set_value") as mock_set_value:

		doc = MagicMock()
		doc.vehicle = "VEH-001"
		doc.name = "MWO-0001"
		doc.status = MaintenanceStatus.COMPLETED

		update_vehicle_status_on_maintenance_change(doc)

		mock_change_status.assert_called_once_with(
			"VEH-001",
			VehicleStatus.AVAILABLE,
			reason="Maintenance Work Order 'MWO-0001' completed"
		)
		mock_set_value.assert_called_with("Vehicle", "VEH-001", "current_assignment_status", "Unassigned")


def test_completed_work_order_assigned_vehicle_sets_assigned():
	"""Verify completed work order against assigned vehicle in Under Maintenance sets status to Assigned."""
	with patch("frappe.db.exists", return_value=True), \
		 patch("frappe.db.get_value", side_effect=lambda dt, name, field=None: VehicleStatus.UNDER_MAINTENANCE if dt == "Vehicle" and field == "status" else None), \
		 patch("fleet_management.services.vehicle_service.is_vehicle_assigned", return_value=True), \
		 patch("fleet_management.services.vehicle_service.VehicleService.change_status") as mock_change_status, \
		 patch("frappe.db.set_value") as mock_set_value:

		doc = MagicMock()
		doc.vehicle = "VEH-001"
		doc.name = "MWO-0001"
		doc.status = MaintenanceStatus.COMPLETED

		update_vehicle_status_on_maintenance_change(doc)

		mock_change_status.assert_called_once_with(
			"VEH-001",
			VehicleStatus.ASSIGNED,
			reason="Maintenance Work Order 'MWO-0001' completed"
		)
		mock_set_value.assert_called_with("Vehicle", "VEH-001", "current_assignment_status", "Assigned")


def test_cancelled_work_order_restores_vehicle_status():
	"""Verify cancelling work order for an assigned vehicle under maintenance restores status to Assigned."""
	with patch("frappe.db.exists", return_value=True), \
		 patch("frappe.db.get_value", side_effect=lambda dt, name, field=None: VehicleStatus.UNDER_MAINTENANCE if dt == "Vehicle" and field == "status" else None), \
		 patch("fleet_management.services.vehicle_service.is_vehicle_assigned", return_value=True), \
		 patch("fleet_management.services.vehicle_service.VehicleService.change_status") as mock_change_status, \
		 patch("frappe.db.set_value") as mock_set_value:

		doc = MagicMock()
		doc.vehicle = "VEH-001"
		doc.name = "MWO-0001"
		doc.status = MaintenanceStatus.CANCELLED

		update_vehicle_status_on_maintenance_change(doc)

		mock_change_status.assert_called_once_with(
			"VEH-001",
			VehicleStatus.ASSIGNED,
			reason="Maintenance Work Order 'MWO-0001' cancelled"
		)
		mock_set_value.assert_called_with("Vehicle", "VEH-001", "current_assignment_status", "Assigned")
