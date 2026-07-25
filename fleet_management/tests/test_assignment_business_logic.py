"""
Unit Tests for Assignment Business Logic, Handover & Return
Fleet Management System
"""

import pytest

from fleet_management.business_rules.assignment_rules import (
	AssignmentActiveDuplicateRule,
	AssignmentOdometerIntegrityRule,
	AssignmentReadOnlyClosedRule,
)
from fleet_management.enums import AssignmentStatus
from fleet_management.utils.exceptions import FleetBusinessLogicError
from fleet_management.validators.assignment_validator import AssignmentValidator


def test_handover_and_return_validation():
	"""Verify Handover and Return odometer integrity validations."""
	# Opening Odometer validation (ASSIGN-004)
	val = AssignmentValidator({
		"vehicle": "V-101",
		"employee": "EMP-001",
		"company": "Fleet Corp",
		"opening_odometer": -100
	})
	assert val.validate() is False
	assert any("ASSIGN-004" in err for err in val.errors)

	# Closing Odometer < Opening Odometer check (ASSIGN-005)
	val2 = AssignmentValidator({
		"vehicle": "V-101",
		"employee": "EMP-001",
		"company": "Fleet Corp",
		"opening_odometer": 1000.0,
		"closing_odometer": 900.0
	})
	assert val2.validate() is False
	assert any("ASSIGN-005" in err for err in val2.errors)


def test_duplicate_active_assignment_rule():
	"""Verify ASSIGN-001 duplicate active assignment rule."""
	rule_clean = AssignmentActiveDuplicateRule({"active_assignments_count": 0})
	assert rule_clean.evaluate() is True

	rule_blocked = AssignmentActiveDuplicateRule({"active_assignments_count": 1})
	assert rule_blocked.evaluate() is False
	with pytest.raises(FleetBusinessLogicError):
		rule_blocked.raise_if_violated()


def test_closed_assignment_read_only_rule():
	"""Verify ASSIGN-008 read-only rule for Closed/Cancelled assignments."""
	closed_rule = AssignmentReadOnlyClosedRule({"status": AssignmentStatus.CLOSED})
	assert closed_rule.evaluate() is False

	cancelled_rule = AssignmentReadOnlyClosedRule({"status": AssignmentStatus.CANCELLED})
	assert cancelled_rule.evaluate() is False

	draft_rule = AssignmentReadOnlyClosedRule({"status": AssignmentStatus.DRAFT})
	assert draft_rule.evaluate() is True


def test_odometer_integrity_mileage_increase():
	"""Verify odometer rule prevents mileage decrease."""
	rule = AssignmentOdometerIntegrityRule({
		"opening_odometer": 5000.0,
		"closing_odometer": 4500.0,
		"current_vehicle_odometer": 4800.0
	})
	assert rule.evaluate() is False
