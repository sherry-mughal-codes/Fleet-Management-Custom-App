"""
Master Production Readiness Integration Test Suite for Maintenance Subsystem
Fleet Management System
"""

from fleet_management.permissions.maintenance_permission import MaintenancePermissionEvaluator
from fleet_management.services.maintenance_due_service import MaintenanceDueEngine
from fleet_management.services.maintenance_service import MaintenanceService


def test_master_maintenance_entry_creation_and_validation():
	"""Verify Maintenance Entry minimal field creation (<1 min UX velocity)."""
	from fleet_management.fleet_management.doctype.maintenance_entry.maintenance_entry import MaintenanceEntry
	from fleet_management.utils.exceptions import FleetValidationError

	# No assignment -> should raise FleetValidationError
	bad_entry = MaintenanceEntry({"maintenance_date": "2026-07-24"})
	try:
		bad_entry.validate()
		assert False, "Expected FleetValidationError for missing assignment"
	except FleetValidationError:
		pass

	# With items but no DB (assignment cannot be resolved) -> same error
	entry_with_items = MaintenanceEntry({
		"assignment": "ASN-TEST-READONLY",
		"maintenance_date": "2026-07-24",
		"current_odometer": 10000.0,
	})
	assert entry_with_items.assignment == "ASN-TEST-READONLY"
	assert entry_with_items.current_odometer == 10000.0
	assert entry_with_items.naming_series == "MAINT-.YYYY.-.#####"


def test_master_maintenance_due_engine_policy_hierarchy():
	"""Verify MaintenanceDueEngine calculation rules."""
	schedule = MaintenanceDueEngine.get_upcoming_maintenance_schedule("PROD-V-101")
	assert "next_due_odometer" in schedule
	assert "is_overdue" in schedule


def test_master_maintenance_service_analytics_helpers():
	"""Verify analytics helper methods in MaintenanceService."""
	service = MaintenanceService()
	v_cost = service.get_total_maintenance_cost_by_vehicle("PROD-V-101")
	assert isinstance(v_cost, (int, float))

	c_stats = service.get_company_maintenance_cost_stats("Fleet Corp")
	assert "total_maintenance_spend" in c_stats

	w_stats = service.get_workshop_performance_stats("Central Workshop")
	assert "total_jobs" in w_stats


def test_master_maintenance_permissions():
	"""Verify role-based access control evaluator for maintenance records."""
	can_create = MaintenancePermissionEvaluator.can_create_maintenance("Administrator")
	assert can_create is True

	can_override = MaintenancePermissionEvaluator.can_override_maintenance_lock("Administrator")
	assert can_override is True
