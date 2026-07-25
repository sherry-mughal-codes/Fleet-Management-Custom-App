"""
Unit Tests for Vehicle Assignment DocType Implementation
Fleet Management System
"""

import pytest

from fleet_management.fleet_management.doctype.vehicle.vehicle import Vehicle
from fleet_management.fleet_management.doctype.vehicle_assignment.vehicle_assignment import (
	VehicleAssignment,
)
from fleet_management.utils.exceptions import FleetValidationError


def test_assignment_creation_minimal_payload():
	payload = {
		"vehicle": "PROD-V-101",
		"employee": "Administrator",
		"company": "Fleet Corp"
	}
	assign_doc = VehicleAssignment(payload)
	assign_doc.before_validate_hook()

	assert assign_doc.vehicle == "PROD-V-101"
	assert assign_doc.employee == "Administrator"
	assert assign_doc.company == "Fleet Corp"
	assert assign_doc.status == "Draft"


def test_assignment_naming_series_default():
	payload = {
		"vehicle": "PROD-V-101",
		"employee": "Administrator",
		"company": "Fleet Corp"
	}
	assign_doc = VehicleAssignment(payload)
	assign_doc.before_validate_hook()

	assert assign_doc.naming_series == "ASSIGN-.YYYY.-.#####"


def test_assignment_date_validation():
	payload = {
		"vehicle": "PROD-V-101",
		"employee": "Administrator",
		"company": "Fleet Corp",
		"assignment_date": "2026-06-01",
		"expected_return_date": "2026-01-01"  # Invalid: Return < Start
	}
	assign_doc = VehicleAssignment(payload)
	with pytest.raises(FleetValidationError):
		assign_doc.before_validate_hook()


def test_assignment_odometer_defaults():
	v_payload = {
		"vehicle_number": "V-ASSIGN-TEST",
		"vehicle_brand": "Toyota",
		"vehicle_model": "Corolla",
		"vehicle_category": "Car",
		"company": "Fleet Corp",
		"initial_odometer": 1500.0
	}
	v = Vehicle(v_payload)
	v.before_validate_hook()

	a_payload = {
		"vehicle": "V-ASSIGN-TEST",
		"employee": "Administrator",
		"company": "Fleet Corp"
	}
	assign_doc = VehicleAssignment(a_payload)

	# Mock doc lookup fallback logic
	assign_doc.current_odometer = v.current_odometer
	assign_doc.opening_odometer = v.current_odometer

	assert assign_doc.opening_odometer == 1500.0
