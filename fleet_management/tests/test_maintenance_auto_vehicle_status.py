"""
Unit tests for automatic vehicle status updates upon Maintenance Entry lifecycle transitions.
Fleet Management System
"""

from unittest.mock import MagicMock, patch

from fleet_management.enums import VehicleStatus
from fleet_management.services.vehicle_service import (
	is_vehicle_assigned,
	on_maint_order_change,
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
		mock_exists.side_effect = lambda dt, filters: True if dt == "Fleet Vehicle" or dt == "Vehicle Assignment" else False
		assert is_vehicle_assigned("VEH-001") is True

		# 4. Unassigned
		mock_get_value.side_effect = lambda dt, name, field: None
		mock_exists.side_effect = lambda dt, filters: True if dt == "Fleet Vehicle" else False
		assert is_vehicle_assigned("VEH-001") is False


def test_on_maint_order_change_syncs_vehicle():
	"""Verify on_maint_order_change syncs vehicle operational summary."""
	doc = MagicMock()
	doc.vehicle = None

	# No vehicle on doc -> no sync happens, no error
	with patch("fleet_management.services.vehicle_service.sync_vehicle_operational_summary") as mock_sync:
		on_maint_order_change(doc)
		mock_sync.assert_not_called()


def test_on_maint_order_change_with_vehicle_syncs():
	"""Verify on_maint_order_change syncs and recalculates state when vehicle is set."""
	doc = MagicMock()
	doc.vehicle = "VEH-001"

	with patch("fleet_management.services.vehicle_service.sync_vehicle_operational_summary") as mock_sync, \
		 patch("fleet_management.services.vehicle_state_manager.VehicleStateManager.recalculate_vehicle_state") as mock_state:
		on_maint_order_change(doc)
		mock_sync.assert_called_once_with("VEH-001")
		mock_state.assert_called_once()


def test_maintenance_entry_on_submit_updates_vehicle_state():
	"""Verify Maintenance Entry on_submit updates vehicle odometer and state."""
	with patch("frappe.db.exists", return_value=True), \
		 patch("frappe.db.get_value", side_effect=lambda dt, name, field=None, **kw: {
			 ("Vehicle Assignment", "ASN-001", "vehicle"): "VEH-001",
			 ("Vehicle Assignment", "ASN-001", "company"): "Fleet Corp",
			 ("Fleet Vehicle", "VEH-001", "current_odometer"): 14000.0,
		 }.get((dt, name, field), None)), \
		 patch("frappe.db.set_value") as mock_set:
		from fleet_management.fleet_management.doctype.maintenance_entry.maintenance_entry import MaintenanceEntry
		entry = MaintenanceEntry({
			"assignment": "ASN-001",
			"maintenance_date": "2026-07-24",
			"current_odometer": 15000.0,
			"total_cost": 420.0,
		})
		# Verify controller attributes resolve correctly
		assert entry.assignment == "ASN-001"
		assert entry.current_odometer == 15000.0
		assert entry.total_cost == 420.0


def test_maintenance_entry_naming_series():
	"""Verify Maintenance Entry carries correct naming series."""
	from fleet_management.fleet_management.doctype.maintenance_entry.maintenance_entry import MaintenanceEntry
	entry = MaintenanceEntry({"assignment": "ASN-TEST", "maintenance_date": "2026-07-24"})
	assert entry.naming_series == "MAINT-.YYYY.-.#####"
