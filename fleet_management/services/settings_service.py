"""
Reusable Settings Service
Fleet Management System
"""

from typing import Any, Dict

import frappe

from fleet_management import constants
from fleet_management.services.base_service import BaseService
from fleet_management.utils.exceptions import FleetConfigurationError
from fleet_management.utils.logger import get_logger

logger = get_logger("fleet_management.services.settings")


class SettingsService(BaseService):
	"""
	Enterprise service managing access to global Fleet Settings.
	Uses Redis caching to avoid repetitive database roundtrips.
	"""

	@staticmethod
	def get_all_settings() -> Dict[str, Any]:
		"""
		Retrieve complete settings dictionary from Redis or DB.
		"""
		cached = frappe.cache().get_value(constants.FLEET_SETTINGS_CACHE_KEY)
		if cached and isinstance(cached, dict):
			return cached

		try:
			doc = frappe.get_single("Fleet Settings")
			settings_dict = doc.as_dict()
			frappe.cache().set_value(constants.FLEET_SETTINGS_CACHE_KEY, settings_dict, expires_in_sec=3600)
			return settings_dict
		except Exception as e:
			logger.warning(f"Unable to read Fleet Settings from DB: {str(e)}. Using default fallbacks.")
			return SettingsService.get_default_fallbacks()

	@staticmethod
	def get_value(key: str, default: Any = None) -> Any:
		"""
		Get a specific configuration setting value.
		"""
		settings = SettingsService.get_all_settings()
		return settings.get(key, default)

	@staticmethod
	def resolve_default_company(user: str | None = None) -> str:
		"""
		Auto-resolve default company from the logged-in user profile / defaults.
		"""
		target_user = user or (frappe.session.user if hasattr(frappe, "session") else "Administrator")
		comp = None
		if hasattr(frappe, "defaults") and hasattr(frappe.defaults, "get_user_default"):
			try:
				comp = frappe.defaults.get_user_default("company", user=target_user)
			except Exception:
				pass
		if not comp and hasattr(frappe, "db") and frappe.db:
			comp = frappe.db.get_value("User", target_user, "company")
			if not comp:
				comp = frappe.db.get_value("Fleet Company", {"is_group": 0}, "name")
		return comp or "ABC Logistics (Private) Limited"

	@staticmethod
	def resolve_default_currency(company: str | None = None) -> str:
		"""
		Auto-resolve default currency from company or user default company (defaults to PKR).
		"""
		comp = company or SettingsService.resolve_default_company()
		if comp and hasattr(frappe, "db") and frappe.db:
			try:
				curr = frappe.db.get_value("Fleet Company", comp, "default_currency")
				if curr:
					return curr
			except Exception:
				pass
		return "PKR"

	@staticmethod
	def clear_cache():
		"""Clear Redis cached settings."""
		try:
			frappe.cache().delete_value(constants.FLEET_SETTINGS_CACHE_KEY)
		except Exception:
			pass

	@staticmethod
	def get_default_fallbacks() -> Dict[str, Any]:
		"""Fallback dictionary when settings DocType has not been saved yet."""
		return {
			"fuel_entry_lock_when_maintenance_due": 1,
			"max_fuel_capacity_validation": constants.DEFAULT_MAX_FUEL_CAPACITY,
			"default_currency": constants.DEFAULT_CURRENCY,
			"default_distance_unit": constants.DISTANCE_UNIT_KM,
			"default_fuel_unit": constants.FUEL_UNIT_LITERS,
			"enable_email_notifications": 1,
			"enable_system_notifications": 1,
			"enable_scheduler": 1,
			"enable_notifications": 1,
			"maintenance_reminder_days": 7,
			"fuel_anomaly_threshold": 20.0,
			"health_check_schedule": "Daily",
			"escalation_recipient": "",
		}

	@staticmethod
	def get_maintenance_interval() -> int:
		return int(SettingsService.get_value("default_maintenance_interval_km", constants.DEFAULT_MAINTENANCE_INTERVAL_KM))

	@staticmethod
	def get_reminder_distance() -> int:
		return int(SettingsService.get_value("default_reminder_distance_km", constants.DEFAULT_REMINDER_DISTANCE_KM))

	@staticmethod
	def is_fuel_lock_enabled() -> bool:
		return bool(SettingsService.get_value("fuel_entry_lock_when_maintenance_due", 1))

	@staticmethod
	def get_max_fuel_capacity() -> float:
		return float(SettingsService.get_value("max_fuel_capacity_validation", constants.DEFAULT_MAX_FUEL_CAPACITY))

	@staticmethod
	def is_email_notification_enabled() -> bool:
		return bool(SettingsService.get_value("enable_email_notifications", 1))

	@staticmethod
	def is_system_notification_enabled() -> bool:
		return bool(SettingsService.get_value("enable_system_notifications", 1))

	@staticmethod
	def is_scheduler_enabled() -> bool:
		return bool(SettingsService.get_value("enable_scheduler", 1))

	@staticmethod
	def is_notifications_enabled() -> bool:
		return bool(SettingsService.get_value("enable_notifications", 1))

	@staticmethod
	def get_maintenance_reminder_days() -> int:
		return int(SettingsService.get_value("maintenance_reminder_days", 7))

	@staticmethod
	def get_fuel_anomaly_threshold() -> float:
		return float(SettingsService.get_value("fuel_anomaly_threshold", 20.0))

	@staticmethod
	def get_health_check_schedule() -> str:
		return str(SettingsService.get_value("health_check_schedule", "Daily"))

	@staticmethod
	def get_escalation_recipient() -> str | None:
		recipient = SettingsService.get_value("escalation_recipient")
		return str(recipient) if recipient else None

	@staticmethod
	def validate_settings(settings: Dict[str, Any] | None = None):
		"""Validate configuration invariants."""
		data = settings or SettingsService.get_all_settings()
		interval = data.get("default_maintenance_interval_km", 0)
		reminder = data.get("default_reminder_distance_km", 0)

		if interval > 0 and (reminder < 0 or reminder >= interval):
			raise FleetConfigurationError("Reminder Distance must be non-negative and less than Maintenance Interval.")
