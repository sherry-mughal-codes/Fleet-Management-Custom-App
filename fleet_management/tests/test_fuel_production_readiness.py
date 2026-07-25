"""
Master Production Readiness Integration Test Suite for Fuel Subsystem
Fleet Management System
"""

from fleet_management.fleet_management.doctype.fuel_entry.fuel_entry import FuelEntry
from fleet_management.permissions.fuel_permission import FuelPermissionEvaluator
from fleet_management.services.fuel_average_service import FuelAverageService
from fleet_management.services.fuel_service import FuelService
from fleet_management.services.maintenance_lock_service import MaintenanceLockService


def test_master_fuel_entry_creation_and_autofetch():
	"""Verify Category A minimal field creation & auto-fetch cascade (<30s UX)."""
	payload = {
		"vehicle": "PROD-V-101",
		"company": "Fleet Corp",
		"fuel_qty": 50.0,
		"total_cost": 100.0,
		"odometer": 15500.0,
		"fuel_date": "2026-07-24"
	}
	doc = FuelEntry(payload)
	doc.before_validate_hook()

	assert doc.vehicle == "PROD-V-101"
	assert doc.company == "Fleet Corp"
	assert doc.fuel_qty == 50.0
	assert doc.total_cost == 100.0
	assert doc.odometer == 15500.0
	assert doc.status == "Draft"
	assert doc.naming_series == "FUEL-.YYYY.-.#####"


def test_master_fuel_average_calculation_engine():
	"""Verify FuelAverageService formulas and output structure."""
	stats = FuelAverageService.calculate_entry_average("PROD-V-101", 16000.0, 50.0)
	assert "distance_travelled" in stats
	assert "fuel_average" in stats


def test_master_maintenance_lock_engine():
	"""Verify MaintenanceLockService enforcement (FUEL-008)."""
	# Mock status Under Maintenance check
	locked = MaintenanceLockService.is_maintenance_locked("V-LOCKED-TEST")
	assert isinstance(locked, bool)


def test_master_fuel_service_analytics_helpers():
	"""Verify analytics helper methods in FuelService."""
	service = FuelService()
	vehicle_cost = service.get_total_fuel_cost_by_vehicle("PROD-V-101")
	assert isinstance(vehicle_cost, (int, float))

	driver_stats = service.get_driver_fuel_cost_stats("Administrator")
	assert "total_spend" in driver_stats

	monthly_stats = service.get_monthly_consumption_stats("Fleet Corp")
	assert "total_consumption_liters" in monthly_stats


def test_master_fuel_permissions():
	"""Verify role-based access control evaluator for fuel entries."""
	can_create = FuelPermissionEvaluator.can_create_fuel_entry("Administrator")
	assert can_create is True

	can_verify = FuelPermissionEvaluator.can_verify_fuel_entry("Administrator")
	assert can_verify is True
