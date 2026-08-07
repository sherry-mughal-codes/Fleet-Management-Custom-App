"""
Unit Tests for Vehicle DocType Implementation
Fleet Management System
"""

import pytest

from fleet_management.fleet_management.doctype.fleet_vehicle.fleet_vehicle import FleetVehicle as Vehicle
from fleet_management.fleet_management.doctype.vehicle_document_detail.vehicle_document_detail import (
	VehicleDocumentDetail,
)
from fleet_management.fleet_management.doctype.vehicle_image_detail.vehicle_image_detail import (
	VehicleImageDetail,
)
from fleet_management.utils.exceptions import FleetValidationError


def test_vehicle_creation_minimal_payload():
	payload = {
		"vehicle_number": "V-1001",
		"vehicle_brand": "Toyota",
		"vehicle_model": "Corolla",
		"vehicle_category": "Car",
		"company": "Fleet Corp"
	}
	v = Vehicle(payload)
	v.before_validate_hook()

	assert v.vehicle_number == "V-1001"
	assert v.status == "Available"
	assert v.current_assignment_status == "Unassigned"
	assert v.current_odometer == 0.0


def test_vehicle_auto_name_generation():
	payload = {
		"vehicle_number": "V-1002",
		"vehicle_brand": "Toyota",
		"vehicle_model": "Corolla",
		"vehicle_category": "Car",
		"company": "Fleet Corp"
	}
	v = Vehicle(payload)
	v.before_validate_hook()

	assert v.vehicle_name == "Toyota Corolla (V-1002)"


def test_vehicle_auto_population_defaults():
	payload = {
		"vehicle_number": "V-1003",
		"vehicle_brand": "Toyota",
		"vehicle_model": "Corolla",
		"vehicle_category": "Car",
		"company": "Fleet Corp",
		"initial_odometer": 1000.0
	}
	v = Vehicle(payload)
	v.before_validate_hook()

	assert v.distance_unit == "KM"
	assert v.fuel_unit == "Liters"
	assert v.current_odometer == 1000.0
	assert v.next_maintenance_due_odometer >= 1000.0


def test_vehicle_warranty_dates_validation():
	payload = {
		"vehicle_number": "V-1004",
		"vehicle_brand": "Toyota",
		"vehicle_model": "Corolla",
		"vehicle_category": "Car",
		"company": "Fleet Corp",
		"warranty_start": "2026-06-01",
		"warranty_end": "2026-01-01"
	}
	v = Vehicle(payload)
	with pytest.raises(FleetValidationError):
		v.before_validate_hook()


def test_vehicle_child_table_details():
	doc_detail = VehicleDocumentDetail({
		"document_type": "Insurance",
		"document_number": "INS-99901",
		"issue_date": "2026-01-01",
		"expiry_date": "2027-01-01"
	})
	assert doc_detail.document_type == "Insurance"

	img_detail = VehicleImageDetail({
		"title": "Front View",
		"is_primary": 1
	})
	assert img_detail.is_primary == 1
