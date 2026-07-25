"""
Fleet Automation & Notification Engine Whitelisted API Endpoints
Fleet Management System
"""

from typing import Any, Dict, Optional
import frappe
from fleet_management.api.base import api_endpoint
from fleet_management.api.responses import success_response
from fleet_management.services.settings_service import SettingsService
from fleet_management.services.automation_service import FleetAutomationService
from fleet_management.services.health_service import FleetHealthService
from fleet_management.notifications.service import FleetNotificationService
from fleet_management.permissions.evaluator import PermissionEvaluator

automation_service = FleetAutomationService()
health_service = FleetHealthService()


@api_endpoint(allow_guest=False)
def get_automation_status_api() -> Dict[str, Any]:
	"""Whitelisted API endpoint retrieving status of automation engine and scheduler policies."""
	status_data = {
		"scheduler_enabled": SettingsService.is_scheduler_enabled(),
		"notifications_enabled": SettingsService.is_notifications_enabled(),
		"maintenance_reminder_days": SettingsService.get_maintenance_reminder_days(),
		"fuel_anomaly_threshold": SettingsService.get_fuel_anomaly_threshold(),
		"health_check_schedule": SettingsService.get_health_check_schedule(),
		"escalation_recipient": SettingsService.get_escalation_recipient(),
	}
	return success_response(data=status_data, message="Fleet automation status retrieved successfully.")


@api_endpoint(allow_guest=False)
def get_notification_status_api() -> Dict[str, Any]:
	"""Whitelisted API endpoint retrieving notification channel configurations."""
	status_data = {
		"email_notifications": SettingsService.is_email_notification_enabled(),
		"system_notifications": SettingsService.is_system_notification_enabled(),
		"global_notifications": SettingsService.is_notifications_enabled(),
		"channels": {
			"email": "Active" if SettingsService.is_email_notification_enabled() else "Disabled",
			"in_app": "Active" if SettingsService.is_system_notification_enabled() else "Disabled",
			"sms": "Extensible Stub",
			"whatsapp": "Extensible Stub",
			"push": "Extensible Stub"
		},
		"authorized_managers": FleetNotificationService.get_authorized_recipients("Fleet Manager")
	}
	return success_response(data=status_data, message="Notification status retrieved successfully.")


@api_endpoint(allow_guest=False)
def get_health_report_api() -> Dict[str, Any]:
	"""Whitelisted API endpoint retrieving system data integrity and health report."""
	report = health_service.run_health_check()
	return success_response(data=report, message="Fleet health report generated successfully.")


@api_endpoint(allow_guest=False)
def get_scheduler_history_api(limit: int = 20) -> Dict[str, Any]:
	"""Whitelisted API endpoint retrieving recent scheduler execution logs."""
	if hasattr(frappe, "db") and hasattr(frappe.db, "get_all"):
		logs = frappe.db.get_all(
			"Scheduled Job Log",
			filters={"scheduled_job_type": ["like", "%fleet_management%"]},
			fields=["name", "scheduled_job_type", "status", "creation"],
			order_by="creation desc",
			limit=limit
		)
	else:
		logs = []
	return success_response(data=logs, message="Scheduler execution history retrieved successfully.")


@api_endpoint(allow_guest=False)
def run_automation_job_api(job_name: Optional[str] = None) -> Dict[str, Any]:
	"""
	Whitelisted API endpoint allowing Fleet Managers to manually trigger an automation job.
	Requires 'Fleet Manager' or 'System Manager' role.
	"""
	PermissionEvaluator.require_any_role(["Fleet Manager", "System Manager"])

	if not job_name or job_name == "all":
		result = automation_service.run_all_automations()
	elif job_name == "maintenance":
		result = automation_service.run_maintenance_automation()
	elif job_name == "fuel":
		result = automation_service.run_fuel_automation()
	elif job_name == "assignment":
		result = automation_service.run_assignment_automation()
	elif job_name == "cost":
		result = automation_service.run_cost_automation()
	elif job_name == "health":
		result = automation_service.run_health_monitoring_automation()
	else:
		frappe.throw(f"Unknown automation job name '{job_name}'. Valid options: all, maintenance, fuel, assignment, cost, health.")

	return success_response(data=result, message=f"Automation job '{job_name or 'all'}' executed successfully.")
