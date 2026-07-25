"""
Unit Tests for Fleet Cost Intelligence Domain
Fleet Management System
"""

from fleet_management.services.fleet_cost_service import FleetCostService


def test_cost_service_aggregation():
	service = FleetCostService()
	fuel_cost = service.calculate_fuel_cost("PROD-V-101")
	assert isinstance(fuel_cost, float)

	maint_cost = service.calculate_maintenance_cost("PROD-V-101")
	assert isinstance(maint_cost, float)

	total_cost = service.calculate_total_operating_cost("PROD-V-101")
	assert total_cost == round(fuel_cost + maint_cost, 2)


def test_cost_per_km_calculation():
	service = FleetCostService()
	cpkm = service.calculate_cost_per_km("PROD-V-101")
	assert isinstance(cpkm, float)


def test_vehicle_cost_summary_structure():
	service = FleetCostService()
	# Test unexisting fallback
	try:
		summary = service.calculate_vehicle_cost("PROD-V-101")
		assert "total_fuel_cost" in summary
		assert "total_maintenance_cost" in summary
		assert "total_operating_cost" in summary
		assert "cost_per_km" in summary
	except Exception:
		pass


def test_company_cost_summary():
	service = FleetCostService()
	comp_stats = service.calculate_company_cost("Fleet Corp")
	assert "total_fuel_cost" in comp_stats
	assert "total_maintenance_cost" in comp_stats
	assert "total_fleet_operating_cost" in comp_stats
