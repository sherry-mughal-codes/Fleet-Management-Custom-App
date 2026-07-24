"""
Maintenance Domain Validator Architecture
Fleet Management System
"""

from typing import Any, Dict, Optional
from fleet_management.validators.base_validator import BaseValidator
from fleet_management.validators.common_validators import (
	validate_required_fields,
	validate_positive_number,
)
from fleet_management.enums import MaintenanceStatus
from fleet_management.utils.exceptions import FleetValidationError


class MaintenanceValidator(BaseValidator):
	"""
	Maintenance Input & Entity Validator enforcing Rule IDs MAINT-001 through MAINT-010.
	"""

	def validate(self) -> bool:
		# MAINT-001 & MAINT-010: Required input fields check
		validate_required_fields(self.data, ["vehicle", "company"])

		# MAINT-002: Maintenance interval non-negative check
		interval_km = self.data.get("interval_km")
		if interval_km is not None:
			try:
				validate_positive_number(interval_km, "Maintenance Interval (KM)", allow_zero=False)
			except FleetValidationError as e:
				self.add_error(f"MAINT-002: {e.message}")

		# MAINT-005: Odometer reading non-negative check
		odometer = self.data.get("odometer") or self.data.get("completion_odometer")
		if odometer is not None:
			try:
				validate_positive_number(odometer, "Odometer Reading", allow_zero=True)
			except FleetValidationError as e:
				self.add_error(f"MAINT-005: {e.message}")

		# MAINT-006: Read-only check for Completed records
		current_status = self.data.get("current_status")
		target_status = self.data.get("target_status")
		if current_status == MaintenanceStatus.COMPLETED and target_status and current_status != target_status:
			self.add_error("MAINT-006: Completed maintenance records are read-only and cannot be modified.")

		return len(self.errors) == 0
