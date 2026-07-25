"""
Unit Tests for Vehicle Domain Architecture
Fleet Management System
"""

import pytest

from fleet_management.business_rules.vehicle_rules import (
	VehicleAvailabilityRule,
	VehicleCompanyIsolationRule,
	VehicleVINValidationRule,
)
from fleet_management.enums import VehicleDocumentType, VehicleStatus
from fleet_management.utils.exceptions import FleetBusinessLogicError
from fleet_management.validators.vehicle_validator import VehicleValidator


def test_vehicle_status_lifecycle_enum():
	assert len(VehicleStatus) == 12
	assert VehicleStatus.DRAFT == "Draft"
	assert VehicleStatus.AVAILABLE == "Available"
	assert VehicleStatus.ASSIGNED == "Assigned"
	assert VehicleStatus.UNDER_MAINTENANCE == "Under Maintenance"
	assert VehicleStatus.OUT_OF_SERVICE == "Out of Service"
	assert VehicleStatus.RESERVED == "Reserved"
	assert VehicleStatus.INACTIVE == "Inactive"
	assert VehicleStatus.SOLD == "Sold"
	assert VehicleStatus.SCRAPPED == "Scrapped"
	assert VehicleStatus.ARCHIVED == "Archived"


def test_vehicle_document_type_enum():
	assert VehicleDocumentType.REGISTRATION == "Registration"
	assert VehicleDocumentType.INSURANCE == "Insurance"
	assert VehicleDocumentType.FITNESS == "Fitness Certificate"




def test_vehicle_validator_valid():
	valid_payload = {
		"license_plate": "ABC-123",
		"vehicle_brand": "Toyota",
		"vehicle_model": "Toyota-Corolla",
		"vehicle_category": "Car",
		"company": "Fleet Corp",
		"vin": "1HGCR2F83HA000000",
		"initial_odometer": 5000,
		"current_status": "Draft",
		"target_status": "Available"
	}
	validator = VehicleValidator(valid_payload)
	assert validator.validate() is True
	assert len(validator.errors) == 0


def test_vehicle_validator_invalid_vin_and_transition():
	invalid_payload = {
		"license_plate": "ABC-123",
		"vehicle_brand": "Toyota",
		"vehicle_model": "Toyota-Corolla",
		"vehicle_category": "Car",
		"company": "Fleet Corp",
		"vin": "INVALID_VIN",
		"current_status": "Draft",
		"target_status": "Sold"
	}
	validator = VehicleValidator(invalid_payload)
	assert validator.validate() is False
	assert len(validator.errors) >= 2


def test_vehicle_availability_rule():
	active_rule = VehicleAvailabilityRule({"status": VehicleStatus.AVAILABLE})
	assert active_rule.evaluate() is True

	out_rule = VehicleAvailabilityRule({"status": VehicleStatus.OUT_OF_SERVICE})
	assert out_rule.evaluate() is False
	with pytest.raises(FleetBusinessLogicError):
		out_rule.raise_if_violated()


def test_vehicle_company_isolation_rule():
	same_company = VehicleCompanyIsolationRule({"vehicle_company": "Corp A", "user_company": "Corp A"})
	assert same_company.evaluate() is True

	diff_company = VehicleCompanyIsolationRule({"vehicle_company": "Corp A", "user_company": "Corp B"})
	assert diff_company.evaluate() is False


def test_vehicle_vin_rule():
	valid_vin = VehicleVINValidationRule({"vin": "1HGCR2F83HA000000"})
	assert valid_vin.evaluate() is True

	invalid_vin = VehicleVINValidationRule({"vin": "123"})
	assert invalid_vin.evaluate() is False
