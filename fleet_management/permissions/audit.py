"""
Centralized Security & Operations Audit Logging Architecture
Fleet Management System
"""

import functools
from typing import Any, Callable, Dict, Optional
import frappe
from fleet_management.utils.logger import get_logger

logger = get_logger("fleet_management.audit")

def audit_log(action_name: str):
	"""
	Decorator to audit critical administrative or security actions.
	"""
	def decorator(func: Callable):
		@functools.wraps(func)
		def wrapper(*args, **kwargs):
			user = frappe.session.user if hasattr(frappe, "session") else "System"
			logger.info(f"AUDIT_START: {action_name}", {"user": user, "function": func.__name__})
			try:
				result = func(*args, **kwargs)
				logger.info(f"AUDIT_SUCCESS: {action_name}", {"user": user, "function": func.__name__})
				return result
			except Exception as e:
				logger.error(f"AUDIT_FAILURE: {action_name}", {"user": user, "error": str(e)})
				raise e
		return wrapper
	return decorator


def audit_document_change(doc, method: str):
	"""Frappe doc_events hook for auditing document modifications."""
	user = frappe.session.user if hasattr(frappe, "session") else "System"
	logger.info(
		f"DOC_AUDIT: {doc.doctype} {doc.name} [{method}]",
		{"user": user, "doctype": doc.doctype, "docname": doc.name, "event": method}
	)
