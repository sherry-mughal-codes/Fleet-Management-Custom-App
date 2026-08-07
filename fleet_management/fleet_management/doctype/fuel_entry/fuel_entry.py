"""
Fuel Entry DocType Controller
Fleet Management System (Frappe v15)
"""

import frappe
from fleet_management.services.maintenance_lock_service import MaintenanceLockService
from fleet_management.utils.base_document import BaseFleetDocument
from fleet_management.utils.exceptions import FleetValidationError
from fleet_management.utils.logger import get_logger

logger = get_logger("fleet_management.doctype.fuel_entry")


class FuelEntry(BaseFleetDocument):
	"""
	Fuel Entry Document Controller.
	"""

	doctype = "Fuel Entry"

	def before_validate(self):
		"""
		Runs before validate():
		1. Auto-resolve 3-way fuel calculation (Rate, Quantity, Total Cost)
		2. Auto-resolve fuel_type from Vehicle if missing
		"""
		self._calculate_three_way_fuel()
		if not getattr(self, "fuel_type", None) and getattr(self, "vehicle", None) and hasattr(frappe, "db") and frappe.db:
			v_fuel_type = frappe.db.get_value("Fleet Vehicle", self.vehicle, "fuel_type")
			if v_fuel_type:
				self.fuel_type = v_fuel_type

	def validate(self):
		"""
		Full server-side validation.
		"""
		# 1. Vehicle is mandatory
		if not self.vehicle:
			raise FleetValidationError("FUEL-001: Vehicle is mandatory for Fuel Entry.")

		# 2. Vehicle must exist
		if hasattr(frappe, "db") and frappe.db and not frappe.db.exists("Fleet Vehicle", self.vehicle):
			raise FleetValidationError(f"FUEL-001: Vehicle '{self.vehicle}' does not exist.")

		# 3. Perform 3-way fuel calculation validation (Rate, Quantity, Total Cost)
		self._calculate_three_way_fuel()

		qty = float(self.fuel_qty or 0.0)
		rate = float(self.fuel_price or 0.0)
		total = float(self.total_cost or 0.0)

		if qty <= 0 and rate <= 0 and total <= 0:
			raise FleetValidationError("FUEL-002: Please provide at least two values among Rate Per Litre, Fuel Quantity, and Total Cost.")

		if qty <= 0:
			raise FleetValidationError("FUEL-002: Fuel quantity must be greater than zero.")
		if rate <= 0:
			raise FleetValidationError("FUEL-003: Rate per litre must be greater than zero.")
		if total <= 0:
			raise FleetValidationError("FUEL-004: Total cost must be greater than zero.")

		# Validate Maximum Allowed Fuel Capacity from Fleet Settings
		from fleet_management.services.settings_service import SettingsService
		max_capacity = SettingsService.get_max_fuel_capacity()
		if max_capacity > 0 and qty > max_capacity:
			raise FleetValidationError(
				f"FUEL-009: Fuel quantity ({qty:,.1f} Litres) exceeds maximum allowed capacity limit ({max_capacity:,.1f} Litres) configured in Fleet Settings."
			)

		# 4. Odometer validation
		odo = float(self.odometer or 0.0)
		if odo <= 0:
			raise FleetValidationError("FUEL-005: Odometer reading must be greater than zero.")

		# 5. Odometer sequence validation
		if hasattr(frappe, "db") and frappe.db:
			self._validate_odometer_sequence(self.vehicle, odo)

		# 6. Maintenance Lock enforcement (FUEL-008)
		if hasattr(frappe, "db") and frappe.db and self.vehicle:
			MaintenanceLockService.enforce_maintenance_lock(self.vehicle, odo)

	def on_submit(self):
		"""
		Post-submission business logic:
		1. Enforce Maintenance Lock (FUEL-008)
		"""
		v_id = self.vehicle
		odo = float(self.odometer or 0.0)

		if not v_id:
			return

		# Enforce Maintenance Lock
		MaintenanceLockService.enforce_maintenance_lock(v_id, odo)

		logger.info(f"Submitted Fuel Entry {self.name} for Vehicle {v_id}")

	def on_cancel(self):
		logger.info(f"Cancelled Fuel Entry {self.name}")

	# ------------------------------------------------------------------
	# Calculation Helpers
	# ------------------------------------------------------------------

	def _calculate_three_way_fuel(self):
		"""
		3-Way Auto-Calculation logic for Rate, Quantity, and Total Cost.
		"""
		qty = float(self.fuel_qty or 0.0)
		rate = float(self.fuel_price or 0.0)
		total = float(self.total_cost or 0.0)

		# Case 1: Qty and Rate provided -> calculate Total Cost
		if qty > 0 and rate > 0 and total == 0:
			self.total_cost = round(qty * rate, 2)
		# Case 2: Total Cost and Qty provided -> calculate Rate
		elif total > 0 and qty > 0 and rate == 0:
			self.fuel_price = round(total / qty, 2)
		# Case 3: Total Cost and Rate provided -> calculate Qty
		elif total > 0 and rate > 0 and qty == 0:
			self.fuel_qty = round(total / rate, 2)

	def _validate_odometer_sequence(self, vehicle_id: str, new_odometer: float):
		"""
		Validates that new odometer is greater than or equal to previous odometer.
		"""
		prev_odo = frappe.db.get_value("Fuel Entry", {"vehicle": vehicle_id, "docstatus": 1}, "MAX(odometer)")
		if not prev_odo:
			prev_odo = frappe.db.get_value("Fleet Vehicle", vehicle_id, "initial_odometer")

		if prev_odo and float(new_odometer) < float(prev_odo):
			raise FleetValidationError(
				f"FUEL-006: New odometer reading ({int(new_odometer):,} KM) cannot be less than previous odometer ({int(float(prev_odo)):,} KM)."
			)
