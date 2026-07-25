"""
Unit Tests for Maintenance Domain Architecture
Fleet Management System
"""

import pytest
from fleet_management.enums import (
	MaintenanceStatus,
	MaintenanceType,
	MaintenancePriority,
	MaintenanceEventType,
)
from fleet_management.services.maintenance_due_service import MaintenanceDueEngine
from fleet_management.validators.maintenance_validator import MaintenanceValidator
from fleet_management.permissions.maintenance_permission import MaintenancePermissionEvaluator
from fleet_management.business_rules.maintenance_rules import (
	MaintenanceVehicleRequiredRule,
	MaintenanceIntervalRequiredRule,
	MaintenanceOdometerAdvancementRule,
	MaintenanceReadOnlyCompletedRule,
	MaintenanceCompanyIsolationRule,
)
from fleet_management.utils.exceptions import FleetValidationError, FleetBusinessLogicError


def test_maintenance_enums_and_constants():
	assert MaintenanceStatus.SCHEDULED == "Scheduled"
	assert MaintenanceStatus.IN_PROGRESS == "In Progress"
	assert MaintenanceStatus.COMPLETED == "Completed"
	assert MaintenanceStatus.OVERDUE == "Overdue"

	assert MaintenanceType.PREVENTIVE == "Preventive"
	assert MaintenancePriority.HIGH == "High"
	assert MaintenanceEventType.CREATED == "Maintenance Created"


def test_maintenance_due_engine_calculations():
	due_odometer = MaintenanceDueEngine.calculate_next_due_odometer("V-MOCK", 5000.0)
	assert due_odometer == 10000.0


	schedule = MaintenanceDueEngine.get_upcoming_maintenance_schedule("V-MOCK")
	assert "next_due_odometer" in schedule
	assert "is_overdue" in schedule


def test_maintenance_validator_contracts():
	valid_payload = {
		"vehicle": "V-MAINT-101",
		"company": "Fleet Corp",
		"interval_km": 5000.0,
		"odometer": 10000.0
	}
	val = MaintenanceValidator(valid_payload)
	assert val.validate() is True

	invalid_payload = {"company": "Fleet Corp"}
	with pytest.raises(FleetValidationError):
		MaintenanceValidator(invalid_payload).validate()




def test_maintenance_business_rules():
	# MAINT-001 Vehicle Required
	r1 = MaintenanceVehicleRequiredRule({"vehicle": "V-101"})
	assert r1.evaluate() is True

	# MAINT-002 Interval Required
	r2 = MaintenanceIntervalRequiredRule({"interval_km": 5000.0})
	assert r2.evaluate() is True

	# MAINT-005 Odometer Advancement
	r5 = MaintenanceOdometerAdvancementRule({"odometer": 15000.0, "previous_odometer": 10000.0})
	assert r5.evaluate() is True

	# MAINT-006 Read-only Completed
	r6 = MaintenanceReadOnlyCompletedRule({"current_status": "Completed", "target_status": "In Progress"})
	assert r6.evaluate() is False

	# MAINT-010 Multi-company isolation
	r10 = MaintenanceCompanyIsolationRule({"company": "Fleet Corp", "vehicle_company": "Other Corp"})
	assert r10.evaluate() is False


def test_maintenance_permissions():
	can_create = MaintenancePermissionEvaluator.can_create_maintenance("Administrator")
	assert can_create is True
