"""
Unit Tests for Fuel Intelligence Engine
Fleet Management System (Frappe Framework v15)

Tests:
- FuelIntelligenceEngine.classify_efficiency (no DB needed)
- FuelIntelligenceEngine.calculate_intelligence (mock-free pure logic)
- FuelAverageService.calculate_entry_average (no DB path)
- Business rule evaluations
"""

import pytest

from fleet_management.business_rules.fuel_rules import (
	FuelOdometerAdvancementRule,
	FuelQuantityPositiveRule,
)
from fleet_management.services.fuel_average_service import FuelAverageService
from fleet_management.services.fuel_intelligence_service import FuelIntelligenceEngine
from fleet_management.services.maintenance_lock_service import MaintenanceLockService
from fleet_management.utils.exceptions import FleetValidationError


# ---------------------------------------------------------------------------
# Efficiency Classification
# ---------------------------------------------------------------------------

def test_classify_efficiency_excellent():
	"""Fuel economy >= 15 KM/L → Excellent."""
	assert FuelIntelligenceEngine.classify_efficiency(15.0) == "Excellent"
	assert FuelIntelligenceEngine.classify_efficiency(20.0) == "Excellent"


def test_classify_efficiency_good():
	"""10 <= KM/L < 15 → Good."""
	assert FuelIntelligenceEngine.classify_efficiency(10.0) == "Good"
	assert FuelIntelligenceEngine.classify_efficiency(14.9) == "Good"


def test_classify_efficiency_average():
	"""7 <= KM/L < 10 → Average."""
	assert FuelIntelligenceEngine.classify_efficiency(7.0) == "Average"
	assert FuelIntelligenceEngine.classify_efficiency(9.9) == "Average"


def test_classify_efficiency_poor():
	"""KM/L < 7 → Poor."""
	assert FuelIntelligenceEngine.classify_efficiency(5.0) == "Poor"
	assert FuelIntelligenceEngine.classify_efficiency(0.1) == "Poor"


def test_classify_efficiency_zero():
	"""0 KM/L returns —."""
	assert FuelIntelligenceEngine.classify_efficiency(0.0) == "—"
	assert FuelIntelligenceEngine.classify_efficiency(None) == "—"


# ---------------------------------------------------------------------------
# Intelligence Calculation (pure logic, no DB, no previous record)
# ---------------------------------------------------------------------------

def test_calculate_intelligence_first_entry():
	"""
	When there is no previous fuel record, is_first_entry=True and
	distance/average/cost_per_km should all be 0.
	"""
	# Monkeypatch get_previous_fuel_record to return None (first entry)
	original = FuelIntelligenceEngine.get_previous_fuel_record
	FuelIntelligenceEngine.get_previous_fuel_record = staticmethod(lambda *a, **kw: None)
	try:
		intel = FuelIntelligenceEngine.calculate_intelligence(
			vehicle_id="V-FIRST",
			current_odometer=10000.0,
			fuel_qty=50.0,
			fuel_price=2.0,
			fuel_date="2026-07-28",
		)
		assert intel["is_first_entry"] == 1
		assert intel["distance_travelled"] == 0.0
		assert intel["fuel_average"] == 0.0
		assert intel["cost_per_km"] == 0.0
		assert intel["total_cost"] == pytest.approx(100.0, 0.01)
		assert intel["fuel_efficiency_rating"] == "—"
	finally:
		FuelIntelligenceEngine.get_previous_fuel_record = original


def test_calculate_intelligence_with_previous_record():
	"""
	When a previous fuel entry exists, all metrics are calculated correctly.
	Example: prev odo = 10000, curr odo = 10500, qty = 50L, price = 2.0
	  distance = 500 KM
	  fuel_average = 500 / 50 = 10.0 KM/L → Good
	  total_cost = 50 × 2 = 100
	  cost_per_km = 100 / 500 = 0.2
	"""
	prev_record = {
		"name": "FUEL-PREV-001",
		"fuel_date": "2026-07-20",
		"odometer": 10000.0,
		"fuel_qty": 45.0,
		"total_cost": 90.0,
		"fuel_average": 9.5,
	}
	original = FuelIntelligenceEngine.get_previous_fuel_record
	FuelIntelligenceEngine.get_previous_fuel_record = staticmethod(lambda *a, **kw: prev_record)
	try:
		intel = FuelIntelligenceEngine.calculate_intelligence(
			vehicle_id="V-TEST",
			current_odometer=10500.0,
			fuel_qty=50.0,
			fuel_price=2.0,
			fuel_date="2026-07-28",
		)
		assert intel["is_first_entry"] == 0
		assert intel["previous_odometer"] == 10000.0
		assert intel["distance_travelled"] == pytest.approx(500.0, 0.01)
		assert intel["fuel_average"] == pytest.approx(10.0, 0.01)
		assert intel["cost_per_km"] == pytest.approx(0.2, 0.01)
		assert intel["total_cost"] == pytest.approx(100.0, 0.01)
		assert intel["fuel_efficiency_rating"] == "Good"
		assert intel["days_since_last_fuel"] == 8
	finally:
		FuelIntelligenceEngine.get_previous_fuel_record = original


def test_calculate_intelligence_zero_distance():
	"""When current odometer equals previous, distance = 0 and avg = 0."""
	prev_record = {"name": "PREV", "fuel_date": "2026-07-25", "odometer": 10500.0, "fuel_qty": 40.0, "total_cost": 80.0}
	original = FuelIntelligenceEngine.get_previous_fuel_record
	FuelIntelligenceEngine.get_previous_fuel_record = staticmethod(lambda *a, **kw: prev_record)
	try:
		intel = FuelIntelligenceEngine.calculate_intelligence(
			vehicle_id="V-TEST",
			current_odometer=10500.0,
			fuel_qty=40.0,
			fuel_price=2.0,
			fuel_date="2026-07-28",
		)
		assert intel["distance_travelled"] == 0.0
		assert intel["fuel_average"] == 0.0
	finally:
		FuelIntelligenceEngine.get_previous_fuel_record = original


# ---------------------------------------------------------------------------
# FuelAverageService (no-DB path)
# ---------------------------------------------------------------------------

def test_fuel_average_service_no_db():
	"""FuelAverageService returns zero dict when vehicle_id is empty."""
	result = FuelAverageService.calculate_entry_average("", 12000.0, 40.0)
	assert result["distance_travelled"] == 0.0
	assert result["fuel_average"] == 0.0


def test_fuel_average_service_zero_qty():
	"""FuelAverageService returns zero dict when fuel_qty = 0."""
	result = FuelAverageService.calculate_entry_average("V-TEST", 12000.0, 0.0)
	assert result["fuel_average"] == 0.0


# ---------------------------------------------------------------------------
# Business Rules
# ---------------------------------------------------------------------------

def test_maintenance_lock_service_enforcement():
	"""Maintenance Lock raises FleetValidationError for vehicles under maintenance."""
	with pytest.raises(FleetValidationError):
		MaintenanceLockService.enforce_maintenance_lock("V-MOCK-UNDER-MAINTENANCE")


def test_odometer_advancement_rule():
	"""FUEL-004: current odometer must be >= previous odometer."""
	valid_rule = FuelOdometerAdvancementRule({"odometer": 12500.0, "previous_odometer": 12000.0})
	assert valid_rule.evaluate() is True

	invalid_rule = FuelOdometerAdvancementRule({"odometer": 11500.0, "previous_odometer": 12000.0})
	assert invalid_rule.evaluate() is False


def test_fuel_quantity_positive_rule():
	"""FUEL-003: fuel_qty must be > 0."""
	assert FuelQuantityPositiveRule({"fuel_qty": 45.0}).evaluate() is True
	assert FuelQuantityPositiveRule({"fuel_qty": 0.0}).evaluate() is False
	assert FuelQuantityPositiveRule({"fuel_qty": -5.0}).evaluate() is False
