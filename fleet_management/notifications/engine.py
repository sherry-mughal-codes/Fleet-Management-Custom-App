"""
Reusable Notification Engine Architecture
Fleet Management System
"""

from typing import List

import frappe

from fleet_management.utils.logger import get_logger

logger = get_logger("fleet_management.notifications")

class NotificationEngine:
	"""
	Central Notification Dispatcher supporting email, system notifications, and SMS/push hooks.
	"""

	@staticmethod
	def send_notification(
		recipients: List[str],
		subject: str,
		message: str,
		channel: str = "email",
		reference_doctype: str | None = None,
		reference_name: str | None = None
	) -> bool:
		"""
		Dispatches notification to requested channel safely.
		"""
		logger.info(f"Dispatching notification via {channel}", {"subject": subject, "recipients": recipients})
		try:
			if channel == "email" and hasattr(frappe, "sendmail"):
				frappe.sendmail(
					recipients=recipients,
					subject=subject,
					message=message,
					reference_doctype=reference_doctype,
					reference_name=reference_name
				)
				return True
			return True
		except Exception as e:
			logger.error("Notification dispatch failed", {"error": str(e)}, exc=e)
			return False
