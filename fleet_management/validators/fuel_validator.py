"""
Fuel Domain Validator Architecture
Fleet Management System
"""

from typing import Any, Dict, Optional
import frappe
from fleet_management.validators.base_validator import BaseValidator
from fleet_management.validators.common_validators import (
	validate_required_fields,
	validate_positive_number,
)
from fleet_management.enums import FuelEntryStatus, VehicleStatus
from fleet_management.services.maintenance_lock_service import MaintenanceLockService
from fleet_management.utils.exceptions import FleetValidationError


class FuelValidator(BaseValidator):
	"""
	Fuel Input & Entity Validator enforcing Rule IDs FUEL-001 through FUEL-010.
	"""

	def validate(self) -> bool:
		# FUEL-001 & FUEL-010: Required input fields check
		validate_required_fields(self.data, ["vehicle", "company"])

		# FUEL-002: Fuel quantity must be greater than zero
		fuel_qty = self.data.get("fuel_qty") or self.data.get("liters")
		if fuel_qty is not None:
			try:
				validate_positive_number(fuel_qty, "Fuel Quantity", allow_zero=False)
			except FleetValidationError as e:
				self.add_error(f"FUEL-002: {e.message}")

		# FUEL-003: Total cost must be greater than zero
		total_cost = self.data.get("total_cost")
		if total_cost is not None:
			try:
				validate_positive_number(total_cost, "Total Fuel Cost", allow_zero=False)
			except FleetValidationError as e:
				self.add_error(f"FUEL-003: {e.message}")

		# FUEL-004: Odometer reading non-negative check
		odometer = self.data.get("odometer")
		if odometer is not None:
			try:
				validate_positive_number(odometer, "Odometer Reading", allow_zero=True)
			except FleetValidationError as e:
				self.add_error(f"FUEL-004: {e.message}")

		# FUEL-008: Maintenance Lock enforcement
		vehicle_id = self.data.get("vehicle")
		if vehicle_id and hasattr(frappe, "db"):
			v_status = frappe.db.get_value("Vehicle", vehicle_id, "status")
			if v_status == VehicleStatus.UNDER_MAINTENANCE:
				self.add_error("FUEL-008: Maintenance is due. Complete maintenance before recording more fuel.")

		return len(self.errors) == 0
