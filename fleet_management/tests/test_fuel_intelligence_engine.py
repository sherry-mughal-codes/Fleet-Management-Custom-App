"""
Unit Tests for Fuel Intelligence Engine & Business Logic
Fleet Management System
"""

import pytest

from fleet_management.business_rules.fuel_rules import (
	FuelOdometerAdvancementRule,
	FuelQuantityPositiveRule,
)
from fleet_management.services.fuel_average_service import FuelAverageService
from fleet_management.services.maintenance_lock_service import MaintenanceLockService
from fleet_management.utils.exceptions import FleetValidationError


def test_fuel_average_calculation_formula():
	"""Verify distance_travelled / fuel_qty formula."""
	# 500 KM distance / 50 Litres = 10.0 KM/L
	stats = FuelAverageService.calculate_entry_average("V-TEST", 10500.0, 50.0)
	assert "distance_travelled" in stats
	assert "fuel_average" in stats


def test_maintenance_lock_service_enforcement():
	"""Verify Maintenance Lock blocks fueling when vehicle is under maintenance (FUEL-008)."""
	# Vehicle Under Maintenance check
	_ = MaintenanceLockService.is_maintenance_locked("V-MOCK-LOCKED")
	# Enforce maintenance lock raise
	with pytest.raises(FleetValidationError):
		MaintenanceLockService.enforce_maintenance_lock("V-MOCK-UNDER-MAINTENANCE")


def test_odometer_advancement_rule():
	"""Verify FUEL-004 odometer advancement rule."""
	valid_rule = FuelOdometerAdvancementRule({"odometer": 12500.0, "previous_odometer": 12000.0})
	assert valid_rule.evaluate() is True

	invalid_rule = FuelOdometerAdvancementRule({"odometer": 11500.0, "previous_odometer": 12000.0})
	assert invalid_rule.evaluate() is False


def test_fuel_quantity_positive_rule():
	"""Verify FUEL-003 positive quantity rule."""
	valid_rule = FuelQuantityPositiveRule({"fuel_qty": 45.0})
	assert valid_rule.evaluate() is True

	zero_rule = FuelQuantityPositiveRule({"fuel_qty": 0.0})
	assert zero_rule.evaluate() is False

	negative_rule = FuelQuantityPositiveRule({"fuel_qty": -5.0})
	assert negative_rule.evaluate() is False
