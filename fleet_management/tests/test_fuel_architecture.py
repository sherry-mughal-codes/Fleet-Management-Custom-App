"""
Unit Tests for Fuel Domain Architecture
Fleet Management System
"""

import pytest
from fleet_management.enums import FuelEntryStatus, FuelEventType
from fleet_management.validators.fuel_validator import FuelValidator
from fleet_management.permissions.fuel_permission import FuelPermissionEvaluator
from fleet_management.business_rules.fuel_rules import (
	FuelVehicleRequiredRule,
	FuelQuantityPositiveRule,
	FuelOdometerAdvancementRule,
	FuelMaintenanceLockRule,
	FuelDuplicateRule,
	FuelCompanyIsolationRule,
)
from fleet_management.utils.exceptions import FleetBusinessLogicError


def test_fuel_entry_status_and_event_enums():
	assert FuelEntryStatus.DRAFT == "Draft"
	assert FuelEntryStatus.SUBMITTED == "Submitted"
	assert FuelEntryStatus.VERIFIED == "Verified"
	assert FuelEntryStatus.CANCELLED == "Cancelled"

	assert FuelEventType.CREATED == "Fuel Entry Created"
	assert FuelEventType.SUBMITTED == "Fuel Entry Submitted"
	assert FuelEventType.VERIFIED == "Fuel Entry Verified"


def test_fuel_validator_valid():
	payload = {
		"vehicle": "PROD-V-101",
		"company": "Fleet Corp",
		"fuel_qty": 45.5,
		"odometer": 12500.0,
		"total_cost": 90.0
	}
	validator = FuelValidator(payload)
	assert validator.validate() is True
	assert len(validator.errors) == 0


def test_fuel_validator_invalid_qty_and_odometer():
	payload = {
		"vehicle": "PROD-V-101",
		"company": "Fleet Corp",
		"fuel_qty": -10.0,  # Invalid: Qty <= 0
		"odometer": -50.0   # Invalid: Negative
	}
	validator = FuelValidator(payload)
	assert validator.validate() is False
	assert any("FUEL-003" in err for err in validator.errors)
	assert any("FUEL-004" in err for err in validator.errors)


def test_rule_fuel_001_vehicle_required():
	valid_rule = FuelVehicleRequiredRule({"vehicle": "PROD-V-101"})
	assert valid_rule.evaluate() is True

	invalid_rule = FuelVehicleRequiredRule({"vehicle": None})
	assert invalid_rule.evaluate() is False


def test_rule_fuel_004_odometer_advancement():
	valid_rule = FuelOdometerAdvancementRule({"odometer": 15000.0, "previous_odometer": 14500.0})
	assert valid_rule.evaluate() is True

	invalid_rule = FuelOdometerAdvancementRule({"odometer": 14000.0, "previous_odometer": 14500.0})
	assert invalid_rule.evaluate() is False


def test_rule_fuel_005_maintenance_lock():
	unlocked = FuelMaintenanceLockRule({"vehicle_status": "Available"})
	assert unlocked.evaluate() is True

	locked = FuelMaintenanceLockRule({"vehicle_status": "Under Maintenance"})
	assert locked.evaluate() is False


def test_rule_fuel_010_company_isolation():
	match = FuelCompanyIsolationRule({"vehicle_company": "Fleet Corp", "fuel_company": "Fleet Corp"})
	assert match.evaluate() is True

	mismatch = FuelCompanyIsolationRule({"vehicle_company": "Fleet Corp", "fuel_company": "Other Corp"})
	assert mismatch.evaluate() is False
