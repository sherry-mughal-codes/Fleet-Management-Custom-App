"""
Notification Manager Service
Fleet Management System (Frappe v15)

Centralized notification engine.
No document or controller directly dispatches emails or notifications;
all notifications pass through NotificationManager.
"""

from typing import Any, Dict, List, Optional
import frappe

from fleet_management.services.base_service import BaseService
from fleet_management.utils.logger import get_logger

logger = get_logger("fleet_management.services.notification_manager")


class NotificationManager(BaseService):
	"""
	Enterprise Notification Manager.
	Single point of contact for dispatches.
	"""

	def send_notification(
		self,
		recipients: List[str],
		subject: str,
		message: str,
		reference_doctype: Optional[str] = None,
		reference_name: Optional[str] = None
	) -> bool:
		"""Dispatches email notification to recipients via Frappe email engine."""
		if not recipients:
			return False

		try:
			if hasattr(frappe, "sendmail"):
				frappe.sendmail(
					recipients=recipients,
					subject=subject,
					message=message,
					reference_doctype=reference_doctype,
					reference_name=reference_name
				)
			logger.info(f"Notification sent to {recipients}: {subject}")
			return True
		except Exception as e:
			logger.error(f"Failed to dispatch notification: {e}")
			return False

	def notify_vehicle_event(self, event_name: str, vehicle_id: str, details: Dict[str, Any]) -> bool:
		"""Dispatches vehicle-related notification."""
		subject = f"Fleet Alert: Vehicle {vehicle_id} - {event_name}"
		message = f"Event '{event_name}' occurred on Vehicle {vehicle_id}. Details: {details}"
		return self.send_notification(
			recipients=["administrator@fleetmanagement.local"],
			subject=subject,
			message=message,
			reference_doctype="Fleet Vehicle",
			reference_name=vehicle_id
		)
