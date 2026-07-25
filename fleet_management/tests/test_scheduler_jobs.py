"""
Unit Tests for Scheduled Tasks & Scheduler Handlers
Fleet Management System
"""

from fleet_management.services.scheduler import (
	scheduled_assignment_expiry_check,
	scheduled_cost_refresh,
	scheduled_fleet_automation_daily,
	scheduled_fuel_anomaly_check,
	scheduled_health_check,
	scheduled_maintenance_check,
)


def test_scheduled_maintenance_check():
	"""Test scheduled_maintenance_check handler."""
	res = scheduled_maintenance_check()
	assert isinstance(res, dict)
	assert "status" in res or "upcoming_count" in res


def test_scheduled_fuel_anomaly_check():
	"""Test scheduled_fuel_anomaly_check handler."""
	res = scheduled_fuel_anomaly_check()
	assert isinstance(res, dict)
	assert "status" in res or "anomalies_detected" in res


def test_scheduled_assignment_expiry_check():
	"""Test scheduled_assignment_expiry_check handler."""
	res = scheduled_assignment_expiry_check()
	assert isinstance(res, dict)
	assert "status" in res or "expiring_count" in res


def test_scheduled_cost_refresh():
	"""Test scheduled_cost_refresh handler."""
	res = scheduled_cost_refresh()
	assert isinstance(res, dict)
	assert "status" in res


def test_scheduled_health_check():
	"""Test scheduled_health_check handler."""
	res = scheduled_health_check()
	assert isinstance(res, dict)
	assert "status" in res or "health_score" in res


def test_scheduled_fleet_automation_daily():
	"""Test scheduled_fleet_automation_daily master job handler."""
	res = scheduled_fleet_automation_daily()
	assert isinstance(res, dict)
	assert "status" in res
