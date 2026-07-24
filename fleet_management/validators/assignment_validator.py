"""
Assignment Domain Validator Architecture
Fleet Management System
"""

from typing import Any, Dict, Optional
import frappe
from fleet_management.validators.base_validator import BaseValidator
from fleet_management.validators.common_validators import (
	validate_required_fields,
	validate_positive_number,
	validate_date_range,
	validate_status_transition,
)
from fleet_management.enums import AssignmentStatus, VehicleStatus
from fleet_management.utils.exceptions import FleetValidationError


class AssignmentValidator(BaseValidator):
	"""
	Assignment Input & Entity Validator enforcing Rule IDs ASSIGN-001 through ASSIGN-010.
	"""

	ALLOWED_STATUS_TRANSITIONS = {
		AssignmentStatus.DRAFT: [AssignmentStatus.PENDING_APPROVAL, AssignmentStatus.APPROVED, AssignmentStatus.ASSIGNED, AssignmentStatus.CANCELLED],
		AssignmentStatus.PENDING_APPROVAL: [AssignmentStatus.APPROVED, AssignmentStatus.CANCELLED],
		AssignmentStatus.APPROVED: [AssignmentStatus.ASSIGNED, AssignmentStatus.CANCELLED],
		AssignmentStatus.ASSIGNED: [AssignmentStatus.IN_USE, AssignmentStatus.RETURNED, AssignmentStatus.CANCELLED],
		AssignmentStatus.IN_USE: [AssignmentStatus.RETURNED, AssignmentStatus.CANCELLED],
		AssignmentStatus.RETURNED: [AssignmentStatus.CLOSED],
		AssignmentStatus.CLOSED: [],
		AssignmentStatus.CANCELLED: [],
	}

	def validate(self) -> bool:
		# ASSIGN-002 & ASSIGN-003 & ASSIGN-010: Required input fields check
		validate_required_fields(self.data, ["vehicle", "employee", "company"])

		# ASSIGN-004: Opening Odometer non-negative check
		opening_odometer = self.data.get("opening_odometer")
		if opening_odometer is not None:
			try:
				validate_positive_number(opening_odometer, "Opening Odometer", allow_zero=True)
			except FleetValidationError as e:
				self.add_error(f"ASSIGN-004: {e.message}")

		# ASSIGN-005: Closing Odometer >= Opening Odometer
		closing_odometer = self.data.get("closing_odometer")
		if opening_odometer is not None and closing_odometer is not None:
			if float(closing_odometer) < float(opening_odometer):
				self.add_error("ASSIGN-005: Closing Odometer cannot be less than Opening Odometer.")

		# ASSIGN-006: Status transition validity check
		current_status = self.data.get("current_status")
		target_status = self.data.get("target_status")
		if current_status and target_status and current_status != target_status:
			try:
				validate_status_transition(current_status, target_status, self.ALLOWED_STATUS_TRANSITIONS)
			except FleetValidationError as e:
				self.add_error(f"ASSIGN-006: {e.message}")

		# ASSIGN-007: Expected return date >= Assignment start date
		start_date = self.data.get("assignment_date") or self.data.get("start_date")
		end_date = self.data.get("expected_return_date") or self.data.get("end_date")
		if start_date and end_date:
			try:
				validate_date_range(start_date, end_date, "Assignment Start Date", "Expected Return Date")
			except FleetValidationError as e:
				self.add_error(f"ASSIGN-007: {e.message}")

		# ASSIGN-008: Read-only check for Closed / Cancelled assignments
		if current_status in (AssignmentStatus.CLOSED, AssignmentStatus.CANCELLED) and target_status and current_status != target_status:
			self.add_error(f"ASSIGN-008: Assignment is '{current_status}' and cannot be modified or re-activated.")

		return len(self.errors) == 0
