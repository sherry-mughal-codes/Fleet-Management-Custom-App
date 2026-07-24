"""
Unit Tests for Settings Service
Fleet Management System
"""

from fleet_management.services.settings_service import SettingsService
from fleet_management.utils.exceptions import FleetConfigurationError
import pytest


def test_settings_service_default_fallbacks():
	fallbacks = SettingsService.get_default_fallbacks()
	assert fallbacks["default_maintenance_interval_km"] == 5000
	assert fallbacks["default_currency"] == "USD"
	assert fallbacks["default_distance_unit"] == "KM"


def test_settings_service_getters():
	interval = SettingsService.get_maintenance_interval()
	assert interval > 0

	reminder = SettingsService.get_reminder_distance()
	assert reminder >= 0

	assert SettingsService.is_audit_logging_enabled() in (True, False)


def test_settings_validation_valid():
	valid_settings = {
		"default_maintenance_interval_km": 5000,
		"default_reminder_distance_km": 500
	}
	SettingsService.validate_settings(valid_settings)


def test_settings_validation_invalid():
	invalid_settings = {
		"default_maintenance_interval_km": 1000,
		"default_reminder_distance_km": 1500
	}
	with pytest.raises(FleetConfigurationError):
		SettingsService.validate_settings(invalid_settings)
