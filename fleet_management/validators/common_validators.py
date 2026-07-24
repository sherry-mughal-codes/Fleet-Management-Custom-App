"""
Global Reusable Validation Framework
Fleet Management System
"""

from typing import Any, Dict, Iterable, Optional, Sequence
import frappe
from fleet_management.utils.exceptions import FleetValidationError, FleetDuplicateEntryError


def validate_positive_number(value: Any, field_name: str, allow_zero: bool = False):
	"""Ensure number is positive (or non-negative if allow_zero=True)."""
	if value is None:
		raise FleetValidationError(f"Field '{field_name}' cannot be null.")
	try:
		num = float(value)
	except (ValueError, TypeError):
		raise FleetValidationError(f"Field '{field_name}' must be a valid number.")

	if allow_zero and num < 0:
		raise FleetValidationError(f"Field '{field_name}' cannot be negative.")
	elif not allow_zero and num <= 0:
		raise FleetValidationError(f"Field '{field_name}' must be greater than zero.")


def validate_date_range(start_date: Any, end_date: Any, start_label: str = "Start Date", end_label: str = "End Date"):
	"""Validate that start_date is before or equal to end_date."""
	if not start_date or not end_date:
		return
	s = frappe.utils.getdate(start_date)
	e = frappe.utils.getdate(end_date)
	if s > e:
		raise FleetValidationError(f"'{start_label}' ({start_date}) cannot be after '{end_label}' ({end_date}).")


def validate_odometer_reading(current_reading: float, previous_reading: float, allow_rollback: bool = False):
	"""Validate odometer reading progression."""
	validate_positive_number(current_reading, "Current Odometer", allow_zero=True)
	if previous_reading is not None and previous_reading > 0:
		if current_reading < previous_reading and not allow_rollback:
			raise FleetValidationError(
				f"New odometer reading ({current_reading}) cannot be less than previous reading ({previous_reading})."
			)


def validate_required_fields(data: Dict[str, Any], required_fields: Iterable[str]):
	"""Validate presence of required fields in dictionary payload."""
	missing = [field for field in required_fields if data.get(field) is None or str(data.get(field)).strip() == ""]
	if missing:
		raise FleetValidationError(
			message=f"Missing required field(s): {', '.join(missing)}.",
			details={"missing_fields": missing}
		)


def validate_duplicate(doctype: str, field_name: str, value: Any, exclude_name: Optional[str] = None):
	"""Ensure value is unique for given Doctype field."""
	if not value:
		return
	filters = {field_name: value}
	if exclude_name:
		filters["name"] = ["!=", exclude_name]
	
	if frappe.db.exists(doctype, filters):
		raise FleetDuplicateEntryError(
			message=f"{doctype} with {field_name} '{value}' already exists.",
			details={"doctype": doctype, "field": field_name, "value": value}
		)


def validate_range(value: float, min_value: float, max_value: float, field_name: str):
	"""Ensure value is within inclusive [min_value, max_value] boundary."""
	if value < min_value or value > max_value:
		raise FleetValidationError(f"Field '{field_name}' ({value}) must be between {min_value} and {max_value}.")


def validate_status_transition(current_status: str, target_status: str, allowed_transitions: Dict[str, Sequence[str]]):
	"""Validate state machine status transition."""
	if current_status == target_status:
		return
	allowed = allowed_transitions.get(current_status, [])
	if target_status not in allowed:
		raise FleetValidationError(
			f"Invalid status transition from '{current_status}' to '{target_status}'. Allowed: {', '.join(allowed) if allowed else 'None'}."
		)
