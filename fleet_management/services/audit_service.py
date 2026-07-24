"""
Audit Service Architecture
Fleet Management System
"""

from typing import Any, Dict, Optional
import frappe
from fleet_management.services.base_service import BaseService
from fleet_management.services.settings_service import SettingsService
from fleet_management.utils.logger import get_logger

logger = get_logger("fleet_management.services.audit")


class AuditService(BaseService):
	"""
	Enterprise service managing security, data mutation, and administrative audit records.
	"""

	@staticmethod
	def record_audit_entry(
		doctype: str,
		docname: str,
		action: str,
		user: Optional[str] = None,
		old_values: Optional[Dict[str, Any]] = None,
		new_values: Optional[Dict[str, Any]] = None,
		reference: Optional[str] = None,
		ip_address: Optional[str] = None
	) -> bool:
		"""
		Logs structured audit payload if audit logging is enabled in Fleet Settings.
		"""
		if not SettingsService.is_audit_logging_enabled():
			return False

		user_id = user or (frappe.session.user if hasattr(frappe, "session") else "System")
		ip = ip_address or (frappe.local.request_ip if hasattr(frappe, "local") and hasattr(frappe.local, "request_ip") else "127.0.0.1")

		payload = {
			"doctype": doctype,
			"docname": docname,
			"action": action,
			"user": user_id,
			"ip_address": ip,
			"reference": reference,
			"timestamp": frappe.utils.now(),
			"old_values": old_values or {},
			"new_values": new_values or {}
		}

		logger.info(f"AUDIT_RECORD: {doctype}/{docname} [{action}] by {user_id}", payload)
		return True
