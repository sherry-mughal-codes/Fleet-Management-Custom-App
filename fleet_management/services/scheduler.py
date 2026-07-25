"""
Scheduler Event Handlers & Entry Points
Fleet Management System
"""

from typing import Any, Dict

from fleet_management.services.automation_service import FleetAutomationService
from fleet_management.services.settings_service import SettingsService
from fleet_management.utils.logger import get_logger

logger = get_logger("fleet_management.scheduler")


def scheduled_maintenance_check() -> Dict[str, Any]:
	"""Scheduled job: Maintenance detection, status refresh, and reminder generation."""
	if not SettingsService.is_scheduler_enabled():
		logger.info("Scheduler disabled in Fleet Settings. Skipping scheduled_maintenance_check.")
		return {"status": "skipped"}
	logger.info("Triggered scheduled_maintenance_check")
	try:
		service = FleetAutomationService()
		return service.run_maintenance_automation()
	except Exception as e:
		logger.error(f"Error executing scheduled_maintenance_check: {str(e)}", exc=e)
		return {"status": "error", "error": str(e)}


def scheduled_fuel_anomaly_check() -> Dict[str, Any]:
	"""Scheduled job: Fuel anomaly detection, declining economy, and inactive fuel entries."""
	if not SettingsService.is_scheduler_enabled():
		logger.info("Scheduler disabled in Fleet Settings. Skipping scheduled_fuel_anomaly_check.")
		return {"status": "skipped"}
	logger.info("Triggered scheduled_fuel_anomaly_check")
	try:
		service = FleetAutomationService()
		return service.run_fuel_automation()
	except Exception as e:
		logger.error(f"Error executing scheduled_fuel_anomaly_check: {str(e)}", exc=e)
		return {"status": "error", "error": str(e)}


def scheduled_assignment_expiry_check() -> Dict[str, Any]:
	"""Scheduled job: Inactive assignments and expiring assignment return date detection."""
	if not SettingsService.is_scheduler_enabled():
		logger.info("Scheduler disabled in Fleet Settings. Skipping scheduled_assignment_expiry_check.")
		return {"status": "skipped"}
	logger.info("Triggered scheduled_assignment_expiry_check")
	try:
		service = FleetAutomationService()
		return service.run_assignment_automation()
	except Exception as e:
		logger.error(f"Error executing scheduled_assignment_expiry_check: {str(e)}", exc=e)
		return {"status": "error", "error": str(e)}


def scheduled_cost_refresh() -> Dict[str, Any]:
	"""Scheduled job: Aggregated cost summary refresh."""
	if not SettingsService.is_scheduler_enabled():
		logger.info("Scheduler disabled in Fleet Settings. Skipping scheduled_cost_refresh.")
		return {"status": "skipped"}
	logger.info("Triggered scheduled_cost_refresh")
	try:
		service = FleetAutomationService()
		return service.run_cost_automation()
	except Exception as e:
		logger.error(f"Error executing scheduled_cost_refresh: {str(e)}", exc=e)
		return {"status": "error", "error": str(e)}


def scheduled_health_check() -> Dict[str, Any]:
	"""Scheduled job: System health checks and data integrity logging."""
	if not SettingsService.is_scheduler_enabled():
		logger.info("Scheduler disabled in Fleet Settings. Skipping scheduled_health_check.")
		return {"status": "skipped"}
	logger.info("Triggered scheduled_health_check")
	try:
		service = FleetAutomationService()
		return service.run_health_monitoring_automation()
	except Exception as e:
		logger.error(f"Error executing scheduled_health_check: {str(e)}", exc=e)
		return {"status": "error", "error": str(e)}


def scheduled_fleet_automation_daily() -> Dict[str, Any]:
	"""Scheduled job: Comprehensive daily automation execution."""
	if not SettingsService.is_scheduler_enabled():
		logger.info("Scheduler disabled in Fleet Settings. Skipping scheduled_fleet_automation_daily.")
		return {"status": "skipped"}
	logger.info("Triggered scheduled_fleet_automation_daily")
	try:
		service = FleetAutomationService()
		return service.run_all_automations()
	except Exception as e:
		logger.error(f"Error executing scheduled_fleet_automation_daily: {str(e)}", exc=e)
		return {"status": "error", "error": str(e)}
