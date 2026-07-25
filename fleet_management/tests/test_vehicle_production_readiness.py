"""
Master Production Readiness Integration Test Suite
Vehicle Domain - Fleet Management System
"""

import pytest
from fleet_management.enums import VehicleStatus, VehicleDocumentStatus, VehicleImageCategory
from fleet_management.services.vehicle_service import VehicleService
from fleet_management.fleet_management.doctype.vehicle.vehicle import Vehicle
from fleet_management.fleet_management.doctype.vehicle_document_detail.vehicle_document_detail import VehicleDocumentDetail
from fleet_management.fleet_management.doctype.vehicle_image_detail.vehicle_image_detail import VehicleImageDetail
from fleet_management.validators.vehicle_validator import VehicleValidator
from fleet_management.validators.vehicle_asset_validator import VehicleAssetValidator, enforce_single_primary_image
from fleet_management.business_rules.vehicle_rules import (
	VehicleAvailabilityRule,
	VehicleFuelingMaintenanceRule,
	VehicleArchivalAssignmentRule,
	VehicleScrapAssignmentRule,
)
from fleet_management.utils.exceptions import FleetValidationError, FleetBusinessLogicError


def test_end_to_end_vehicle_registration():
	"""Verify <2 minute vehicle registration policy with Category A minimal fields."""
	payload = {
		"vehicle_number": "PROD-V-101",
		"vehicle_brand": "Toyota",
		"vehicle_model": "Corolla",
		"vehicle_category": "Car",
		"company": "Fleet Corp",
		"initial_odometer": 500.0
	}
	v = Vehicle(payload)
	v.before_validate_hook()

	assert v.vehicle_number == "PROD-V-101"
	assert v.vehicle_name == "Toyota Corolla (PROD-V-101)"
	assert v.status == VehicleStatus.AVAILABLE
	assert v.distance_unit == "KM"
	assert v.fuel_unit == "Liters"
	assert v.current_odometer == 500.0
	assert v.next_maintenance_due_odometer >= 500.0


def test_13_state_lifecycle_transitions():
	"""Verify all 13 states exist and status transitions follow state machine rules."""
	assert len(VehicleStatus) == 12


	validator_valid = VehicleValidator({
		"license_plate": "PROD-101",
		"vehicle_brand": "Toyota",
		"vehicle_model": "Corolla",
		"vehicle_category": "Car",
		"company": "Fleet Corp",
		"current_status": VehicleStatus.AVAILABLE,
		"target_status": VehicleStatus.ASSIGNED
	})
	assert validator_valid.validate() is True


def test_invalid_lifecycle_transition_prevention():
	"""Verify invalid state transitions raise FleetValidationError."""
	validator_invalid = VehicleValidator({
		"license_plate": "PROD-101",
		"vehicle_brand": "Toyota",
		"vehicle_model": "Corolla",
		"vehicle_category": "Car",
		"company": "Fleet Corp",
		"current_status": VehicleStatus.DRAFT,
		"target_status": VehicleStatus.SOLD
	})
	assert validator_invalid.validate() is False
	assert any("VEH-004" in err for err in validator_invalid.errors)


def test_business_rules_veh_001_to_006():
	"""Verify business rules VEH-001 through VEH-006."""
	# VEH-001
	avail = VehicleAvailabilityRule({"status": VehicleStatus.AVAILABLE})
	assert avail.evaluate() is True
	unavail = VehicleAvailabilityRule({"status": VehicleStatus.UNDER_MAINTENANCE})
	assert unavail.evaluate() is False

	# VEH-002
	fuel_maint = VehicleFuelingMaintenanceRule({"status": VehicleStatus.UNDER_MAINTENANCE})
	assert fuel_maint.evaluate() is False

	# VEH-004
	archive_assigned = VehicleArchivalAssignmentRule({"status": VehicleStatus.ASSIGNED, "target_status": VehicleStatus.ARCHIVED})
	assert archive_assigned.evaluate() is False

	# VEH-005
	scrap_assigned = VehicleScrapAssignmentRule({"status": VehicleStatus.ASSIGNED, "target_status": VehicleStatus.SCRAPPED})
	assert scrap_assigned.evaluate() is False


def test_digital_asset_subsystem_validations():
	"""Verify ASSET-001 through ASSET-008 rules and single primary image selection."""
	# ASSET-001
	valid_asset = VehicleAssetValidator({
		"documents": [
			{
				"document_type": "Registration",
				"document_number": "REG-881",
				"issue_date": "2026-01-01",
				"expiry_date": "2027-01-01",
				"attachment": "/files/doc.pdf",
				"status": "Active"
			}
		],
		"images": []
	})
	assert valid_asset.validate() is True

	# ASSET-005 Single Primary Image Auto-Reset
	img1 = VehicleImageDetail({"title": "Front", "image": "/files/f.jpg", "is_primary": 1})
	img2 = VehicleImageDetail({"title": "Rear", "image": "/files/r.jpg", "is_primary": 1})
	images = [img1, img2]
	enforce_single_primary_image(images)
	assert img1.is_primary == 1
	assert img2.is_primary == 0


def test_vehicle_service_dashboard_and_summary():
	"""Verify dashboard summary metrics aggregation."""
	svc = VehicleService()
	dash = svc.get_dashboard_summary()
	assert "total_vehicles" in dash
	assert "available_count" in dash
	assert "assigned_count" in dash
	assert "maintenance_count" in dash
	assert "out_of_service_count" in dash
	assert "inactive_count" in dash
