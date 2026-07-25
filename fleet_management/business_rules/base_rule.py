"""
Base Business Rule Architecture
Fleet Management System
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, List

from fleet_management.utils.exceptions import FleetBusinessLogicError


class BaseBusinessRule(ABC):
	"""
	Abstract Base Class for modular Business Invariant Rules.
	Decouples business invariant checking from Frappe DocType triggers and controllers.
	"""

	def __init__(self, context: Dict[str, Any]):
		self.context = context
		self.violations: List[str] = []

	@abstractmethod
	def evaluate(self) -> bool:
		"""
		Evaluate the business rule against self.context.
		Returns True if all business invariants hold, False otherwise.
		"""
		pass

	def add_violation(self, message: str):
		"""Record a business rule violation."""
		self.violations.append(message)

	def raise_if_violated(self, custom_message: str | None = None):
		"""Raise FleetBusinessLogicError if rule evaluation fails."""
		if not self.evaluate() or self.violations:
			msg = custom_message or "Business rule evaluation failed."
			raise FleetBusinessLogicError(message=msg, details={"violations": self.violations})
