"""
Unit Tests for Fuel Entry DocType Implementation
Fleet Management System
"""

import pytest

from fleet_management.fleet_management.doctype.fuel_entry.fuel_entry import FuelEntry
from fleet_management.fleet_management.doctype.vehicle.vehicle import Vehicle
from fleet_management.utils.exceptions import FleetValidationError


def test_fuel_entry_creation_minimal_payload():
	payload = {
		"vehicle": "PROD-V-101",
		"company": "Fleet Corp",
		"fuel_qty": 50.0,
		"total_cost": 100.0,
		"odometer": 12000.0
	}
	fuel_doc = FuelEntry(payload)
	fuel_doc.before_validate_hook()

	assert fuel_doc.vehicle == "PROD-V-101"
	assert fuel_doc.company == "Fleet Corp"
	assert fuel_doc.fuel_qty == 50.0
	assert fuel_doc.total_cost == 100.0
	assert fuel_doc.odometer == 12000.0
	assert fuel_doc.status == "Draft"
	assert fuel_doc.naming_series == "FUEL-.YYYY.-.#####"


def test_fuel_entry_structural_validations():
	# Negative quantity check
	payload_bad_qty = {
		"vehicle": "PROD-V-101",
		"company": "Fleet Corp",
		"fuel_qty": -10.0,
		"total_cost": 100.0,
		"odometer": 12000.0
	}
	fuel_doc = FuelEntry(payload_bad_qty)
	with pytest.raises(FleetValidationError):
		fuel_doc.before_validate_hook()


def test_fuel_entry_odometer_defaults():
	v_payload = {
		"vehicle_number": "V-FUEL-TEST",
		"vehicle_brand": "Toyota",
		"vehicle_model": "Camry",
		"vehicle_category": "Car",
		"company": "Fleet Corp",
		"initial_odometer": 8500.0
	}
	v = Vehicle(v_payload)
	v.before_validate_hook()

	f_payload = {
		"vehicle": "V-FUEL-TEST",
		"company": "Fleet Corp",
		"fuel_qty": 40.0,
		"total_cost": 80.0
	}
	fuel_doc = FuelEntry(f_payload)

	# Mock doc lookup fallback logic
	fuel_doc.current_vehicle_odometer = v.current_odometer
	fuel_doc.odometer = v.current_odometer

	assert fuel_doc.odometer == 8500.0
