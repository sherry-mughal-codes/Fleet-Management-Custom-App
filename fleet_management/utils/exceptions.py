"""
Enterprise Exception Architecture
Fleet Management System
"""

from typing import Any, Dict, Optional
import frappe

class FleetManagementError(frappe.ValidationError):
	"""Base domain exception for Fleet Management System."""

	status_code: int = 400
	default_message: str = "A fleet management exception occurred."

	def __init__(
		self,
		message: Optional[str] = None,
		details: Optional[Dict[str, Any]] = None,
		status_code: Optional[int] = None
	):
		self.message = message or self.default_message
		self.details = details or {}
		if status_code:
			self.status_code = status_code
		super().__init__(self.message)

	def to_dict(self) -> Dict[str, Any]:
		return {
			"error": self.__class__.__name__,
			"message": self.message,
			"details": self.details,
			"status_code": self.status_code
		}


class FleetValidationError(FleetManagementError):
	"""Raised when validation of input parameters or business rules fails."""
	status_code = 422
	default_message = "Validation failed for request parameter or entity."


class FleetPermissionError(FleetManagementError):
	"""Raised when user lacks required role, permission, or scope."""
	status_code = 403
	default_message = "Permission denied for requested action."


class FleetNotFoundError(FleetManagementError):
	"""Raised when requested fleet entity or resource is not found."""
	status_code = 404
	default_message = "Requested entity or resource was not found."


class FleetBusinessLogicError(FleetManagementError):
	"""Raised when standard business invariant violation occurs."""
	status_code = 409
	default_message = "Business logic error encountered."


class FleetExternalServiceError(FleetManagementError):
	"""Raised when external integrations or services fail."""
	status_code = 502
	default_message = "External service call failed."


class FleetRateLimitError(FleetManagementError):
	"""Raised when rate limits are exceeded."""
	status_code = 429
	default_message = "Rate limit exceeded. Please try again later."
