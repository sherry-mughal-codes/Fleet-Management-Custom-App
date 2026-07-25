"""
Notification Service Architecture
Fleet Management System
"""

from typing import Any, Dict, List

import frappe

from fleet_management.services.base_service import BaseService
from fleet_management.services.settings_service import SettingsService
from fleet_management.utils.logger import get_logger

logger = get_logger("fleet_management.notifications.service")


class FleetNotificationService(BaseService):
	"""
	Enterprise Notification Engine managing notification routing across Desk, Email,
	System Logs, and escalation channels. Features extension hooks for SMS, WhatsApp, and Push.
	"""

	@staticmethod
	def get_authorized_recipients(role: str = "Fleet Manager") -> List[str]:
		"""
		Retrieves email addresses for users possessing the target authorization role.
		Respects Frappe user permissions and active user status.
		"""
		if not hasattr(frappe, "db") or not hasattr(frappe.db, "get_all"):
			return ["administrator@example.com"]

		try:
			user_roles = frappe.db.get_all(
				"Has Role",
				filters={"role": role, "parenttype": "User"},
				fields=["parent"]
			)
			user_ids = [r.get("parent") for r in user_roles if r.get("parent")]
			if not user_ids:
				user_ids = ["Administrator"]

			active_users = frappe.db.get_all(
				"User",
				filters={"name": ["in", user_ids], "enabled": 1},
				fields=["email"]
			)
			emails = [u.get("email") for u in active_users if u.get("email")]
			return emails or ["administrator@example.com"]
		except Exception as e:
			logger.warning(f"Error querying authorized recipients for role '{role}': {str(e)}")
			return ["administrator@example.com"]

	@staticmethod
	def dispatch(
		notification_type: Any,
		recipients: List[str],
		subject: str,
		message: str,
		context: Dict[str, Any] | None = None,
		reference_doctype: str | None = None,
		reference_name: str | None = None,
		enqueue_background: bool = True
	) -> bool:
		"""
		Dispatch notification through enabled system, email, and desk channels.
		"""
		if not SettingsService.is_notifications_enabled():
			logger.info(f"Global notifications disabled in Fleet Settings. Suppressing notification: {subject}")
			return False

		if not recipients:
			escalation = SettingsService.get_escalation_recipient()
			if escalation:
				recipients = [escalation]
			else:
				recipients = FleetNotificationService.get_authorized_recipients("Fleet Manager")

		email_enabled = SettingsService.is_email_notification_enabled()
		system_enabled = SettingsService.is_system_notification_enabled()

		if not email_enabled and not system_enabled:
			logger.info(f"Email & System notifications disabled in Fleet Settings. Suppressing {notification_type}.")
			return False

		if enqueue_background and hasattr(frappe, "enqueue"):
			frappe.enqueue(
				"fleet_management.notifications.service.execute_dispatch",
				queue="short",
				notification_type=str(notification_type),
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
			notification_type=str(notification_type),
			recipients=recipients,
			subject=subject,
			message=message,
			context=context,
			reference_doctype=reference_doctype,
			reference_name=reference_name,
			email_enabled=email_enabled,
			system_enabled=system_enabled
		)

	# --- Channel Extension Points (Out of Scope for active dispatch, defined for clean future integration) ---

	@staticmethod
	def send_sms(recipients: List[str], message: str) -> Dict[str, Any]:
		"""Extension point for SMS notification gateway."""
		logger.info(f"SMS Channel Hook invoked for {len(recipients)} recipients. Channel non-active.")
		return {"status": "skipped", "channel": "sms", "reason": "SMS gateway integration not enabled in scope."}

	@staticmethod
	def send_whatsapp(recipients: List[str], message: str) -> Dict[str, Any]:
		"""Extension point for WhatsApp notification gateway."""
		logger.info(f"WhatsApp Channel Hook invoked for {len(recipients)} recipients. Channel non-active.")
		return {"status": "skipped", "channel": "whatsapp", "reason": "WhatsApp integration not enabled in scope."}

	@staticmethod
	def send_push(recipients: List[str], message: str) -> Dict[str, Any]:
		"""Extension point for Push notification gateway."""
		logger.info(f"Push Channel Hook invoked for {len(recipients)} recipients. Channel non-active.")
		return {"status": "skipped", "channel": "push", "reason": "Push notification service not enabled in scope."}


class NotificationService(FleetNotificationService):
	"""Alias for backward compatibility with existing notification callers."""
	pass


def execute_dispatch(
	notification_type: str,
	recipients: List[str],
	subject: str,
	message: str,
	context: Dict[str, Any] | None = None,
	reference_doctype: str | None = None,
	reference_name: str | None = None,
	email_enabled: bool = True,
	system_enabled: bool = True
) -> bool:
	"""
	Internal dispatch executor sending email or desk notification entries.
	"""
	logger.info(f"Executing notification dispatch: {notification_type}", {"recipients": recipients, "subject": subject})
	success = True

	try:
		if email_enabled and hasattr(frappe, "sendmail"):
			try:
				frappe.sendmail(
					recipients=recipients,
					subject=subject,
					message=message,
					reference_doctype=reference_doctype,
					reference_name=reference_name
				)
			except Exception as email_err:
				logger.warning(f"Email dispatch warning: {str(email_err)}")

		if system_enabled and hasattr(frappe, "get_doc") and hasattr(frappe, "db") and frappe.db.exists("DocType", "Notification Log"):
			for recipient in recipients:
				try:
					n_log = frappe.get_doc({
						"doctype": "Notification Log",
						"for_user": recipient,
						"subject": subject,
						"email_content": message,
						"document_type": reference_doctype,
						"document_name": reference_name,
						"type": "Alert"
					})
					n_log.insert(ignore_permissions=True)
				except Exception as log_err:
					logger.warning(f"Could not create Notification Log for {recipient}: {str(log_err)}")

		return success
	except Exception as e:
		logger.error("Error executing notification dispatch", {"error": str(e)}, exc=e)
		return False
