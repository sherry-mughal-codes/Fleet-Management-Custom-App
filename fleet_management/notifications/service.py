"""
Notification Service Architecture
Fleet Management System
"""

from typing import Any, Dict, List, Optional
import frappe
from fleet_management.enums import NotificationType
from fleet_management.services.base_service import BaseService
from fleet_management.services.settings_service import SettingsService
from fleet_management.utils.logger import get_logger

logger = get_logger("fleet_management.notifications.service")


class NotificationService(BaseService):
	"""
	Enterprise service managing async and sync notification routing across Desk, Email, and System events.
	"""

	@staticmethod
	def dispatch(
		notification_type: NotificationType,
		recipients: List[str],
		subject: str,
		message: str,
		context: Optional[Dict[str, Any]] = None,
		reference_doctype: Optional[str] = None,
		reference_name: Optional[str] = None,
		enqueue_background: bool = True
	) -> bool:
		"""
		Dispatch notification through enabled system and email channels.
		"""
		if not recipients:
			return False

		email_enabled = SettingsService.is_email_notification_enabled()
		system_enabled = SettingsService.is_system_notification_enabled()

		if not email_enabled and not system_enabled:
			logger.info(f"Notifications disabled in Fleet Settings. Suppressing {notification_type}.")
			return False

		if enqueue_background and hasattr(frappe, "enqueue"):
			frappe.enqueue(
				"fleet_management.notifications.service.execute_dispatch",
				queue="short",
				notification_type=notification_type,
				recipients=recipients,
				subject=subject,
				message=message,
				context=context,
				reference_doctype=reference_doctype,
				reference_name=reference_name,
				email_enabled=email_enabled,
				system_enabled=system_enabled
			)
			return True

		return execute_dispatch(
			notification_type=notification_type,
			recipients=recipients,
			subject=subject,
			message=message,
			context=context,
			reference_doctype=reference_doctype,
			reference_name=reference_name,
			email_enabled=email_enabled,
			system_enabled=system_enabled
		)


def execute_dispatch(
	notification_type: str,
	recipients: List[str],
	subject: str,
	message: str,
	context: Optional[Dict[str, Any]] = None,
	reference_doctype: Optional[str] = None,
	reference_name: Optional[str] = None,
	email_enabled: bool = True,
	system_enabled: bool = True
) -> bool:
	"""
	Internal dispatch executor sending email or desk notification entries.
	"""
	logger.info(f"Executing notification dispatch: {notification_type}", {"recipients": recipients, "subject": subject})
	try:
		if email_enabled and hasattr(frappe, "sendmail"):
			frappe.sendmail(
				recipients=recipients,
				subject=subject,
				message=message,
				reference_doctype=reference_doctype,
				reference_name=reference_name
			)
		return True
	except Exception as e:
		logger.error("Error executing notification dispatch", {"error": str(e)}, exc=e)
		return False
