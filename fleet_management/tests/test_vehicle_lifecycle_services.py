"""
Unit Tests for Vehicle Lifecycle Engine & Domain Services
Fleet Management System
"""

import pytest
from fleet_management.enums import VehicleStatus
from fleet_management.services.vehicle_service import VehicleService
from fleet_management.business_rules.vehicle_rules import (
	VehicleAvailabilityRule,
	VehicleFuelingMaintenanceRule,
	VehicleArchivalAssignmentRule,
	VehicleScrapAssignmentRule,
)
from fleet_management.utils.exceptions import FleetValidationError, FleetBusinessLogicError


def test_13_state_lifecycle_enum():
	assert len(VehicleStatus) == 12

	assert VehicleStatus.DRAFT == "Draft"
	assert VehicleStatus.AVAILABLE == "Available"
	assert VehicleStatus.RESERVED == "Reserved"
	assert VehicleStatus.ASSIGNED == "Assigned"
	assert VehicleStatus.MAINTENANCE_DUE == "Maintenance Due"
	assert VehicleStatus.UNDER_MAINTENANCE == "Under Maintenance"
	assert VehicleStatus.INSPECTION == "Inspection"
	assert VehicleStatus.OUT_OF_SERVICE == "Out of Service"
	assert VehicleStatus.INACTIVE == "Inactive"
	assert VehicleStatus.SOLD == "Sold"
	assert VehicleStatus.SCRAPPED == "Scrapped"
	assert VehicleStatus.ARCHIVED == "Archived"


def test_rule_veh_001_assignment_eligibility():
	avail_rule = VehicleAvailabilityRule({"status": VehicleStatus.AVAILABLE})
	assert avail_rule.evaluate() is True

	maint_rule = VehicleAvailabilityRule({"status": VehicleStatus.UNDER_MAINTENANCE})
	assert maint_rule.evaluate() is False
	with pytest.raises(FleetBusinessLogicError):
		maint_rule.raise_if_violated()


def test_rule_veh_002_fueling_maintenance():
	active_rule = VehicleFuelingMaintenanceRule({"status": VehicleStatus.AVAILABLE})
	assert active_rule.evaluate() is True

	under_maint = VehicleFuelingMaintenanceRule({"status": VehicleStatus.UNDER_MAINTENANCE})
	assert under_maint.evaluate() is False


def test_rule_veh_004_archival_assignment():
	valid_archive = VehicleArchivalAssignmentRule({"status": VehicleStatus.INACTIVE, "target_status": VehicleStatus.ARCHIVED})
	assert valid_archive.evaluate() is True

	invalid_archive = VehicleArchivalAssignmentRule({"status": VehicleStatus.ASSIGNED, "target_status": VehicleStatus.ARCHIVED})
	assert invalid_archive.evaluate() is False


def test_vehicle_service_dashboard_summary():
	svc = VehicleService()
	res = svc.get_dashboard_summary()
	assert "total_vehicles" in res
	assert "available_count" in res
	assert "assigned_count" in res
	assert "maintenance_count" in res
