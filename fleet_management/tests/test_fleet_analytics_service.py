"""
Unit Tests for Fleet Analytics & Command Center Subsystem
Fleet Management System
"""

import pytest
from fleet_management.services.fleet_analytics_service import FleetAnalyticsService


def test_executive_kpis_calculation():
	service = FleetAnalyticsService()
	kpis = service.get_executive_kpis("Fleet Corp")

	assert "total_vehicles" in kpis
	assert "active_vehicles" in kpis
	assert "assigned_vehicles" in kpis
	assert "available_vehicles" in kpis
	assert "under_maintenance" in kpis
	assert "overdue_maintenance" in kpis
	assert "monthly_fuel_cost" in kpis
	assert "monthly_maintenance_cost" in kpis
	assert "monthly_operating_cost" in kpis


def test_smart_alerts_severities():
	service = FleetAnalyticsService()
	alerts = service.get_smart_alerts("Fleet Corp")
	assert isinstance(alerts, list)


def test_analytics_charts_structure():
	service = FleetAnalyticsService()
	charts = service.get_analytics_charts("Fleet Corp")

	assert "fuel_vs_maintenance" in charts
	assert "vehicle_status_distribution" in charts
	assert "labels" in charts["fuel_vs_maintenance"]
	assert "datasets" in charts["fuel_vs_maintenance"]


def test_vehicle_health_summary():
	service = FleetAnalyticsService()
	health = service.get_vehicle_health_summary("Fleet Corp", limit=5)
	assert isinstance(health, list)


def test_recent_activity_timeline():
	service = FleetAnalyticsService()
	activity = service.get_recent_activity_timeline("Fleet Corp", limit=5)
	assert isinstance(activity, list)
