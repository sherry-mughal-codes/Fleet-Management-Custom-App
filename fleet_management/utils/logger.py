"""
Centralized Reusable Logging Architecture
Fleet Management System
"""

import json
import logging
import time
from contextlib import contextmanager
from typing import Any, Dict

import frappe

SENSITIVE_KEYS = {"password", "api_secret", "secret", "token", "auth_header", "jwt"}

class FleetLogger:
	"""
	Enterprise logger wrapping frappe.logger with structured metadata,
	component tagging, sensitive parameter sanitization, and execution timing.
	"""

	def __init__(self, module_name: str = "fleet_management"):
		self.module_name = module_name
		try:
			self._logger = frappe.logger(module_name)
		except Exception:
			self._logger = logging.getLogger(module_name)

	def _sanitize(self, data: Any) -> Any:
		if isinstance(data, dict):
			return {
				k: "***MASKED***" if str(k).lower() in SENSITIVE_KEYS else self._sanitize(v)
				for k, v in data.items()
			}
		elif isinstance(data, list):
			return [self._sanitize(item) for item in data]
		return data

	def _format_message(self, message: str, context: Dict[str, Any] | None = None, level: str = "INFO") -> str:
		user = "System"
		if hasattr(frappe, "session"):
			try:
				user = getattr(frappe.session, "user", "System") or "System"
			except Exception:
				user = "System"

		payload = {
			"module": self.module_name,
			"level": level,
			"message": message,
			"user": user,
		}

		if context:
			payload["context"] = self._sanitize(context)
		return json.dumps(payload)

	def debug(self, message: str, context: Dict[str, Any] | None = None):
		self._logger.debug(self._format_message(message, context, level="DEBUG"))

	def info(self, message: str, context: Dict[str, Any] | None = None):
		self._logger.info(self._format_message(message, context, level="INFO"))

	def warning(self, message: str, context: Dict[str, Any] | None = None):
		self._logger.warning(self._format_message(message, context, level="WARNING"))

	def error(self, message: str, context: Dict[str, Any] | None = None, exc: Exception | None = None):
		if exc and hasattr(frappe, "log_error"):
			try:
				frappe.log_error(title=f"{self.module_name}: {message}", message=str(exc))
			except Exception:
				pass
		self._logger.error(self._format_message(message, context, level="ERROR"))

	def critical(self, message: str, context: Dict[str, Any] | None = None, exc: Exception | None = None):
		if exc and hasattr(frappe, "log_error"):
			try:
				frappe.log_error(title=f"CRITICAL {self.module_name}: {message}", message=str(exc))
			except Exception:
				pass
		self._logger.critical(self._format_message(message, context, level="CRITICAL"))

	@contextmanager
	def log_execution_time(self, action_name: str, context: Dict[str, Any] | None = None):
		"""Context manager measuring and logging execution duration."""
		start = time.time()
		ctx = context.copy() if context else {}
		try:
			yield
		finally:
			duration_ms = round((time.time() - start) * 1000, 2)
			ctx["duration_ms"] = duration_ms
			self.info(f"Execution completed: {action_name}", ctx)


_loggers: Dict[str, FleetLogger] = {}

def get_logger(module_name: str = "fleet_management") -> FleetLogger:
	"""
	Factory function returning singleton FleetLogger instances per module name.
	"""
	if module_name not in _loggers:
		_loggers[module_name] = FleetLogger(module_name)
	return _loggers[module_name]
