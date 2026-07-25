"""
Unit Tests for API v1 Versioned REST Endpoints
Fleet Management System v1.0.0
"""

import pytest
from fleet_management.api.v1.vehicle_api import search_vehicles
from fleet_management.api.v1.assignment_api import get_assignment_summary
from fleet_management.api.v1.fuel_api import get_fuel_summary
from fleet_management.api.v1.cost_api import get_company_cost_summary_api
from fleet_management.api.v1.analytics_api import get_kpis_api
from fleet_management.api.v1.automation_api import get_automation_status_api, get_health_report_api


def test_v1_vehicle_api_routing():
	"""Verify API v1 vehicle list endpoint routing."""
	res = search_vehicles()
	assert res["success"] is True
	assert "data" in res


def test_v1_cost_api_routing():
	"""Verify API v1 cost calculation endpoint routing."""
	res = get_company_cost_summary_api()
	assert res["success"] is True
	assert "data" in res


def test_v1_analytics_api_routing():
	"""Verify API v1 executive KPIs endpoint routing."""
	res = get_kpis_api()
	assert res["success"] is True
	assert "data" in res


def test_v1_automation_api_routing():
	"""Verify API v1 automation status endpoint routing."""
	res = get_automation_status_api()
	assert res["success"] is True
	assert "data" in res
	assert res["data"]["scheduler_enabled"] is True


def test_v1_health_report_api_routing():
	"""Verify API v1 health report endpoint routing."""
	res = get_health_report_api()
	assert res["success"] is True
	assert "data" in res
	assert "health_score" in res["data"]
