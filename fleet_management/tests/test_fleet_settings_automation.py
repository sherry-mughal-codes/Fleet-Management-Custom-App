"""
Unit Tests for Fleet Settings Automation Configurations
Fleet Management System
"""

import pytest
from fleet_management.services.settings_service import SettingsService


def test_automation_settings_default_fallbacks():
	"""Verify automation settings default fallbacks."""
	assert SettingsService.is_scheduler_enabled() is True
	assert SettingsService.is_notifications_enabled() is True
	assert SettingsService.get_maintenance_reminder_days() == 7
	assert SettingsService.get_fuel_anomaly_threshold() == 20.0
	assert SettingsService.get_health_check_schedule() == "Daily"
	assert SettingsService.get_escalation_recipient() is None or isinstance(SettingsService.get_escalation_recipient(), str)


def test_settings_validation_rules():
	"""Verify validation invariants on Fleet Settings."""
	valid_settings = {
		"default_maintenance_interval_km": 5000,
		"default_reminder_distance_km": 500,
		"maintenance_reminder_days": 7,
		"fuel_anomaly_threshold": 20.0
	}
	# Should not raise exception
	SettingsService.validate_settings(valid_settings)
