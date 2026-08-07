"""
Fuel Domain Validator Architecture
Fleet Management System
"""

import frappe

from fleet_management.enums import VehicleStatus
from fleet_management.utils.exceptions import FleetValidationError
from fleet_management.validators.base_validator import BaseValidator
from fleet_management.validators.common_validators import (
	validate_positive_number,
	validate_required_fields,
)


class FuelValidator(BaseValidator):
	"""
	Fuel Input & Entity Validator enforcing Rule IDs FUEL-001 through FUEL-010.
	"""

	def validate(self) -> bool:
		# FUEL-001: assignment is now the primary reference (not vehicle)
		assignment = self.data.get("assignment")
		if not assignment:
			self.add_error("FUEL-001: Vehicle Assignment is required for a Fuel Entry.")

		# FUEL-002: Fuel quantity must be greater than zero
		fuel_qty = self.data.get("fuel_qty") or self.data.get("liters")
		if fuel_qty is not None:
			try:
				validate_positive_number(fuel_qty, "Fuel Quantity", allow_zero=False)
			except FleetValidationError as e:
				self.add_error(f"FUEL-002: {e.message}")

			from fleet_management.services.settings_service import SettingsService
			max_cap = SettingsService.get_max_fuel_capacity()
			if max_cap > 0 and float(fuel_qty or 0.0) > max_cap:
				self.add_error(f"FUEL-009: Fuel quantity ({float(fuel_qty):,.1f} Litres) exceeds maximum allowed limit ({max_cap:,.1f} Litres) in Fleet Settings.")

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

		# FUEL-008: Maintenance Lock enforcement via vehicle resolved from assignment
		if assignment and hasattr(frappe, "db") and frappe.db:
			vehicle_id = frappe.db.get_value("Vehicle Assignment", assignment, "vehicle")
			if vehicle_id:
				v_status = frappe.db.get_value("Fleet Vehicle", vehicle_id, "status")
				if v_status == VehicleStatus.UNDER_MAINTENANCE:
					self.add_error("FUEL-008: Maintenance is due. Complete maintenance before recording more fuel.")

		return len(self.errors) == 0
