"""
Unit Tests for Automation Whitelisted REST API Endpoints
Fleet Management System
"""

import pytest
from fleet_management.api.automation_api import (
	get_automation_status_api,
	get_notification_status_api,
	get_health_report_api,
	get_scheduler_history_api,
	run_automation_job_api,
)


def test_get_automation_status_api():
	"""Test get_automation_status_api response envelope."""
	res = get_automation_status_api()
	assert res["success"] is True
	assert "scheduler_enabled" in res["data"]
	assert "fuel_anomaly_threshold" in res["data"]


def test_get_notification_status_api():
	"""Test get_notification_status_api response envelope."""
	res = get_notification_status_api()
	assert res["success"] is True
	assert "channels" in res["data"]
	assert "authorized_managers" in res["data"]


def test_get_health_report_api():
	"""Test get_health_report_api response envelope."""
	res = get_health_report_api()
	assert res["success"] is True
	assert "status" in res["data"]
	assert "health_score" in res["data"]


def test_get_scheduler_history_api():
	"""Test get_scheduler_history_api response envelope."""
	res = get_scheduler_history_api(limit=5)
	assert res["success"] is True
	assert isinstance(res["data"], list)


def test_run_automation_job_api():
	"""Test run_automation_job_api execution."""
	res = run_automation_job_api(job_name="maintenance")
	assert res["success"] is True
	assert "data" in res
