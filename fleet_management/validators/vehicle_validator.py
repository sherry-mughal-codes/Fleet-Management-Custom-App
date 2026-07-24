"""
Vehicle Domain Validator Architecture
Fleet Management System
"""

import re
from typing import Any, Dict, Optional
from fleet_management.validators.base_validator import BaseValidator
from fleet_management.validators.common_validators import (
	validate_required_fields,
	validate_positive_number,
	validate_status_transition,
)
from fleet_management.enums import VehicleStatus
from fleet_management.utils.exceptions import FleetValidationError


class VehicleValidator(BaseValidator):
	"""
	Vehicle Input & Entity Validator enforcing Rule IDs VEH-001 through VEH-010.
	"""

	ALLOWED_STATUS_TRANSITIONS = {
		VehicleStatus.DRAFT: [VehicleStatus.AVAILABLE, VehicleStatus.INACTIVE],
		VehicleStatus.AVAILABLE: [
			VehicleStatus.RESERVED,
			VehicleStatus.ASSIGNED,
			VehicleStatus.MAINTENANCE_DUE,
			VehicleStatus.UNDER_MAINTENANCE,
			VehicleStatus.INSPECTION,
			VehicleStatus.OUT_OF_SERVICE,
			VehicleStatus.INACTIVE,
			VehicleStatus.SOLD,
			VehicleStatus.SCRAPPED
		],
		VehicleStatus.RESERVED: [VehicleStatus.AVAILABLE, VehicleStatus.ASSIGNED, VehicleStatus.OUT_OF_SERVICE],
		VehicleStatus.ASSIGNED: [VehicleStatus.AVAILABLE, VehicleStatus.MAINTENANCE_DUE, VehicleStatus.UNDER_MAINTENANCE, VehicleStatus.OUT_OF_SERVICE],
		VehicleStatus.MAINTENANCE_DUE: [VehicleStatus.UNDER_MAINTENANCE, VehicleStatus.AVAILABLE, VehicleStatus.OUT_OF_SERVICE],
		VehicleStatus.UNDER_MAINTENANCE: [VehicleStatus.INSPECTION, VehicleStatus.AVAILABLE, VehicleStatus.OUT_OF_SERVICE],
		VehicleStatus.INSPECTION: [VehicleStatus.AVAILABLE, VehicleStatus.UNDER_MAINTENANCE, VehicleStatus.OUT_OF_SERVICE],
		VehicleStatus.OUT_OF_SERVICE: [VehicleStatus.AVAILABLE, VehicleStatus.UNDER_MAINTENANCE, VehicleStatus.INACTIVE, VehicleStatus.SCRAPPED, VehicleStatus.SOLD],
		VehicleStatus.INACTIVE: [VehicleStatus.AVAILABLE, VehicleStatus.ARCHIVED],
		VehicleStatus.SOLD: [VehicleStatus.ARCHIVED],
		VehicleStatus.SCRAPPED: [VehicleStatus.ARCHIVED],
		VehicleStatus.ARCHIVED: [VehicleStatus.INACTIVE],
	}

	def validate(self) -> bool:
		# VEH-001: Required Category A registration fields check
		validate_required_fields(self.data, ["license_plate", "vehicle_brand", "vehicle_model", "vehicle_category", "company"])

		# VEH-002: VIN format validation (if provided)
		vin = self.data.get("vin")
		if vin:
			cleaned_vin = str(vin).upper().strip()
			if not re.match(r"^[A-HJ-NPR-Z0-9]{17}$", cleaned_vin):
				self.add_error("VEH-002: VIN must contain exactly 17 uppercase alphanumeric characters (excluding I, O, Q).")

		# VEH-003: Initial odometer non-negative check
		initial_odometer = self.data.get("initial_odometer")
		if initial_odometer is not None:
			try:
				validate_positive_number(initial_odometer, "Initial Odometer", allow_zero=True)
			except FleetValidationError as e:
				self.add_error(f"VEH-003: {e.message}")

		# VEH-004: Status transition validity check
		current_status = self.data.get("current_status")
		target_status = self.data.get("target_status")
		if current_status and target_status and current_status != target_status:
			try:
				validate_status_transition(current_status, target_status, self.ALLOWED_STATUS_TRANSITIONS)
			except FleetValidationError as e:
				self.add_error(f"VEH-004: {e.message}")

		return len(self.errors) == 0
