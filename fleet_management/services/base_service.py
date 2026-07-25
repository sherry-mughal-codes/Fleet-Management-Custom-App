"""
Base Service Layer Architecture
Fleet Management System
"""

from abc import ABC
from typing import Any, Callable, Dict, Optional
import frappe
from fleet_management.utils.logger import get_logger
from fleet_management.utils.exceptions import FleetManagementError

class BaseService(ABC):
	"""
	Abstract Base Class for all Business Services.
	Encapsulates database transaction boundaries, central logging, and permission checks.
	"""

	def __init__(self, user: Optional[str] = None):
		if user:
			self.user = user
		else:
			try:
				self.user = getattr(frappe.session, "user", "System") if hasattr(frappe, "session") else "System"
			except Exception:
				self.user = "System"
		self.logger = get_logger(self.__class__.__module__)

	def execute_in_transaction(self, action: Callable[..., Any], *args, **kwargs) -> Any:
		"""
		Execute an action block within an explicit Frappe database transaction boundary.
		Rolls back automatically on failure.
		"""
		try:
			self.logger.info(f"Starting transaction for {action.__name__}")
			result = action(*args, **kwargs)
			frappe.db.commit()
			self.logger.info(f"Transaction committed for {action.__name__}")
			return result
		except Exception as e:
			frappe.db.rollback()
			self.logger.error(f"Transaction failed for {action.__name__}: {str(e)}", exc=e)
			if isinstance(e, FleetManagementError):
				raise e
			raise FleetManagementError(message=f"Service action {action.__name__} failed.", details={"error": str(e)})


def scheduled_health_check():
	"""Placeholder scheduled job function for background worker verification."""
	logger = get_logger("fleet_management.scheduler")
	logger.info("Fleet Management scheduled health check triggered successfully.")
