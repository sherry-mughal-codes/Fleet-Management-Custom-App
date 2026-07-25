"""
API v1 - Fleet Automation & Notification Engine REST Endpoints
Fleet Management System
"""

from fleet_management.api.automation_api import (
	get_automation_status_api,
	get_notification_status_api,
	get_health_report_api,
	get_scheduler_history_api,
	run_automation_job_api,
)

__all__ = [
	"get_automation_status_api",
	"get_notification_status_api",
	"get_health_report_api",
	"get_scheduler_history_api",
	"run_automation_job_api",
]
