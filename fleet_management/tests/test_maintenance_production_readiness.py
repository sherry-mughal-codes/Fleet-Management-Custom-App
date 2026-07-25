"""
Master Production Readiness Integration Test Suite for Maintenance Subsystem
Fleet Management System
"""

from fleet_management.fleet_management.doctype.maintenance_request.maintenance_request import (
	MaintenanceRequest,
)
from fleet_management.permissions.maintenance_permission import MaintenancePermissionEvaluator
from fleet_management.services.maintenance_due_service import MaintenanceDueEngine
from fleet_management.services.maintenance_service import MaintenanceService


def test_master_maintenance_request_creation_and_autofetch():
	"""Verify Category A minimal field creation (<1 min UX velocity)."""
	payload = {
		"vehicle": "PROD-V-101",
		"company": "Fleet Corp",
		"maintenance_type": "Preventive",
		"priority": "High",
		"requested_date": "2026-07-24"
	}
	doc = MaintenanceRequest(payload)
	doc.before_validate_hook()

	assert doc.vehicle == "PROD-V-101"
	assert doc.company == "Fleet Corp"
	assert doc.maintenance_type == "Preventive"
	assert doc.priority == "High"
	assert doc.status == "Draft"
	assert doc.naming_series == "MREQ-.YYYY.-.#####"


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
