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
	assert VehicleStatus.AVAILABLE == "Available"
	assert VehicleStatus.ASSIGNED == "Assigned"
	assert VehicleStatus.UNDER_MAINTENANCE == "Under Maintenance"
	assert VehicleStatus.OUT_OF_SERVICE == "Out of Service"
	assert VehicleStatus.ARCHIVED == "Archived"
	assert len(VehicleStatus) == 12


def test_assignment_status_enum():
	assert AssignmentStatus.DRAFT == "Draft"
	assert AssignmentStatus.ASSIGNED == "Assigned"
	assert AssignmentStatus.CLOSED == "Closed"
	assert len(AssignmentStatus) == 8



def test_constants_tuples():
	assert len(constants.ALL_VEHICLE_STATUSES) == 12
	assert constants.ROLE_FLEET_MANAGER in constants.ALL_FLEET_ROLES
	assert constants.DISTANCE_UNIT_KM == "KM"
	assert constants.DEFAULT_MAINTENANCE_INTERVAL_KM == 5000

