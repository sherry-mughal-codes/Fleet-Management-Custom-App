"""
Unit Tests for Business Rules Architecture
Fleet Management System
"""

import pytest
from fleet_management.business_rules.vehicle_rules import VehicleAvailabilityRule
from fleet_management.business_rules.fuel_rules import FuelCapacityThresholdRule
from fleet_management.utils.exceptions import FleetBusinessLogicError


def test_vehicle_availability_rule_pass():
	rule = VehicleAvailabilityRule({"status": "Available"})
	assert rule.evaluate() is True



def test_vehicle_availability_rule_fail():
	rule = VehicleAvailabilityRule({"status": "Out of Service"})
	assert rule.evaluate() is False
	with pytest.raises(FleetBusinessLogicError):
		rule.raise_if_violated()


def test_fuel_capacity_rule_pass():
	rule = FuelCapacityThresholdRule({"fuel_amount": 50, "max_capacity": 100})
	assert rule.evaluate() is True


def test_fuel_capacity_rule_fail():
	rule = FuelCapacityThresholdRule({"fuel_amount": 150, "max_capacity": 100})
	assert rule.evaluate() is False
	with pytest.raises(FleetBusinessLogicError):
		rule.raise_if_violated()
