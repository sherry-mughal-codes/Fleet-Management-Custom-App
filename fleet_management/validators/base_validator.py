"""
Base Validation Layer Architecture
Fleet Management System
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, List

from fleet_management.utils.exceptions import FleetValidationError


class BaseValidator(ABC):
	"""
	Abstract Base Class for all Validation rules across Fleet Management modules.
	Enforces single-responsibility principle for input and entity validation.
	"""

	def __init__(self, data: Dict[str, Any]):
		self.data = data
		self.errors: List[str] = []

	@abstractmethod
	def validate(self) -> bool:
		"""
		Execute validation rules. Returns True if valid, raises FleetValidationError or populates self.errors.
		"""
		pass

	def add_error(self, message: str):
		"""Record a validation error message."""
		self.errors.append(message)

	def raise_if_invalid(self, custom_message: str | None = None):
		"""Raise FleetValidationError if any validation errors exist."""
		if not self.validate() or self.errors:
			msg = custom_message or "Validation check failed."
			raise FleetValidationError(message=msg, details={"errors": self.errors})
