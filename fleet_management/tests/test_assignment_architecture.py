"""
Unit Tests for Assignment Domain Architecture
Fleet Management System
"""

import pytest
from fleet_management.enums import AssignmentStatus, AssignmentEventType
from fleet_management.validators.assignment_validator import AssignmentValidator
from fleet_management.permissions.assignment_permission import AssignmentPermissionEvaluator
from fleet_management.business_rules.assignment_rules import (
	AssignmentVehicleAvailabilityRule,
	AssignmentOdometerRule,
	AssignmentOverlapRule,
	AssignmentCompanyIsolationRule,
)
from fleet_management.utils.exceptions import FleetBusinessLogicError


def test_assignment_status_lifecycle_enum():
	assert len(AssignmentStatus) == 8
	assert AssignmentStatus.DRAFT == "Draft"
	assert AssignmentStatus.PENDING_APPROVAL == "Pending Approval"
	assert AssignmentStatus.APPROVED == "Approved"
	assert AssignmentStatus.ASSIGNED == "Assigned"
	assert AssignmentStatus.IN_USE == "In Use"
	assert AssignmentStatus.RETURNED == "Returned"
	assert AssignmentStatus.CLOSED == "Closed"
	assert AssignmentStatus.CANCELLED == "Cancelled"


def test_assignment_validator_valid():
	payload = {
		"vehicle": "PROD-V-101",
		"employee": "EMP-001",
		"company": "Fleet Corp",
		"opening_odometer": 1000.0,
		"closing_odometer": 1200.0,
		"start_date": "2026-01-01",
		"end_date": "2026-01-05",
		"current_status": "Approved",
		"target_status": "Assigned"
	}
	validator = AssignmentValidator(payload)
	assert validator.validate() is True
	assert len(validator.errors) == 0


def test_assignment_validator_invalid_odometer_and_dates():
	payload = {
		"vehicle": "PROD-V-101",
		"employee": "EMP-001",
		"company": "Fleet Corp",
		"opening_odometer": 1000.0,
		"closing_odometer": 800.0,  # Invalid: Closing < Opening
		"start_date": "2026-06-01",
		"end_date": "2026-01-01"   # Invalid: End < Start
	}
	validator = AssignmentValidator(payload)
	assert validator.validate() is False
	assert any("ASN-004" in err or "ASSIGN-005" in err for err in validator.errors)
	assert any("ASN-007" in err or "ASSIGN-007" in err for err in validator.errors)




def test_rule_asn_001_vehicle_availability():
	avail_rule = AssignmentVehicleAvailabilityRule({"vehicle_status": "Available"})
	assert avail_rule.evaluate() is True

	unavail_rule = AssignmentVehicleAvailabilityRule({"vehicle_status": "Under Maintenance"})
	assert unavail_rule.evaluate() is False


def test_rule_asn_003_004_odometer_checks():
	valid_odometer = AssignmentOdometerRule({
		"opening_odometer": 1000.0,
		"closing_odometer": 1500.0,
		"current_vehicle_odometer": 900.0
	})
	assert valid_odometer.evaluate() is True

	invalid_opening = AssignmentOdometerRule({
		"opening_odometer": 500.0,
		"closing_odometer": 1500.0,
		"current_vehicle_odometer": 900.0
	})
	assert invalid_opening.evaluate() is False


def test_rule_asn_005_overlap_check():
	no_overlap = AssignmentOverlapRule({"active_assignments_count": 0})
	assert no_overlap.evaluate() is True

	has_overlap = AssignmentOverlapRule({"active_assignments_count": 1})
	assert has_overlap.evaluate() is False
