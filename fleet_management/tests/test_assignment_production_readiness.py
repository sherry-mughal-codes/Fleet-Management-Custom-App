"""
Master Production Readiness Integration Test Suite for Assignment Domain Subsystem
Fleet Management System
"""

import pytest
from fleet_management.enums import AssignmentStatus, VehicleStatus
from fleet_management.fleet_management.doctype.vehicle_assignment.vehicle_assignment import VehicleAssignment
from fleet_management.fleet_management.doctype.vehicle.vehicle import Vehicle
from fleet_management.services.assignment_service import AssignmentService
from fleet_management.validators.assignment_validator import AssignmentValidator
from fleet_management.permissions.assignment_permission import AssignmentPermissionEvaluator
from fleet_management.utils.exceptions import FleetValidationError, FleetBusinessLogicError, FleetPermissionError


def test_master_assignment_creation_and_autofetch():
	"""Verify Category A minimal field creation & auto-fetch cascade."""
	payload = {
		"vehicle": "PROD-V-101",
		"employee": "Administrator",
		"company": "Fleet Corp",
		"assignment_date": "2026-07-01",
		"expected_return_date": "2026-07-10"
	}
	doc = VehicleAssignment(payload)
	doc.before_validate_hook()

	assert doc.vehicle == "PROD-V-101"
	assert doc.employee == "Administrator"
	assert doc.company == "Fleet Corp"
	assert doc.status == "Draft"
	assert doc.naming_series == "ASSIGN-.YYYY.-.#####"


def test_master_assignment_lifecycle_state_machine():
	"""Verify all 8 assignment lifecycle states exist."""
	statuses = [
		AssignmentStatus.DRAFT,
		AssignmentStatus.PENDING_APPROVAL,
		AssignmentStatus.APPROVED,
		AssignmentStatus.ASSIGNED,
		AssignmentStatus.IN_USE,
		AssignmentStatus.RETURNED,
		AssignmentStatus.CLOSED,
		AssignmentStatus.CANCELLED
	]
	assert len(statuses) == 8


def test_master_odometer_integrity_and_mileage_protection():
	"""Verify Rule IDs ASSIGN-004 & ASSIGN-005 prevent odometer rollback."""
	# ASSIGN-004: Opening Odometer negative check
	val_negative = AssignmentValidator({
		"vehicle": "V-101",
		"employee": "EMP-001",
		"company": "Fleet Corp",
		"opening_odometer": -50.0
	})
	assert val_negative.validate() is False

	# ASSIGN-005: Closing Odometer < Opening Odometer
	val_decrease = AssignmentValidator({
		"vehicle": "V-101",
		"employee": "EMP-001",
		"company": "Fleet Corp",
		"opening_odometer": 1200.0,
		"closing_odometer": 1000.0
	})
	assert val_decrease.validate() is False


def test_master_assignment_service_analytics_helpers():
	"""Verify analytics helper methods in AssignmentService."""
	service = AssignmentService()
	active_count = service.get_active_assignments_count()
	assert isinstance(active_count, int)

	util_stats = service.get_vehicle_utilization_stats("PROD-V-101")
	assert util_stats["vehicle"] == "PROD-V-101"
	assert "total_distance_travelled" in util_stats

	compliance = service.get_return_compliance_stats()
	assert "total_assignments" in compliance


def test_master_assignment_permissions():
	"""Verify role-based access control evaluator for assignments."""
	can_create = AssignmentPermissionEvaluator.can_create_assignment("Administrator")
	assert can_create is True

	can_approve = AssignmentPermissionEvaluator.can_approve_assignment("Administrator")
	assert can_approve is True
