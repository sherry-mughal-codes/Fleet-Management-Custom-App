"""
Unit Tests for Constants and Enums
Fleet Management System
"""

from fleet_management import constants
from fleet_management.enums import (
	VehicleStatus,
	AssignmentStatus,
	MaintenanceStatus,
	FuelEntryStatus,
	ApprovalStatus,
	NotificationType,
	ExpenseType,
	DistanceUnit,
	FuelUnit,
	FleetRole,
)


def test_vehicle_status_enum():
	assert VehicleStatus.ACTIVE == "Active"
	assert VehicleStatus.IN_SERVICE == "In Service"
	assert VehicleStatus.OUT_OF_SERVICE == "Out of Service"
	assert VehicleStatus.DISPOSED == "Disposed"
	assert VehicleStatus.PENDING_INSPECTION == "Pending Inspection"
	assert len(VehicleStatus) == 5


def test_assignment_status_enum():
	assert AssignmentStatus.DRAFT == "Draft"
	assert AssignmentStatus.ACTIVE == "Active"
	assert AssignmentStatus.COMPLETED == "Completed"


def test_constants_tuples():
	assert len(constants.ALL_VEHICLE_STATUSES) == 5
	assert constants.ROLE_FLEET_MANAGER in constants.ALL_FLEET_ROLES
	assert constants.DISTANCE_UNIT_KM == "KM"
	assert constants.DEFAULT_MAINTENANCE_INTERVAL_KM == 5000
