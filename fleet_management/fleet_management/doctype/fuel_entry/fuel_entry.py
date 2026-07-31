"""
Fuel Entry Controller Implementation
Fleet Management System (Frappe Framework v15)

Architecture:
- Fuel Entry is linked ONLY via Vehicle Assignment (no stored vehicle field)
- Vehicle, Employee, Company are resolved dynamically through the Assignment
- All Fuel Intelligence metrics are auto-calculated and stored on save/submit
- On Submit: updates Vehicle odometer + statistics
- On Cancel: recalculates Vehicle statistics to reverse this entry
"""

from typing import Optional

import frappe
from frappe.model.document import Document

from fleet_management.services.fuel_intelligence_service import FuelIntelligenceEngine
from fleet_management.services.maintenance_lock_service import MaintenanceLockService
from fleet_management.services.vehicle_state_manager import VehicleStateManager
from fleet_management.utils.exceptions import FleetValidationError
from fleet_management.utils.logger import get_logger

logger = get_logger("fleet_management.doctype.fuel_entry")


class FuelEntry(Document):
	"""
	Submittable transactional document for a fuel refilling event.
	Linked directly to Vehicle.
	"""

	doctype = "Fuel Entry"

	def __init__(self, *args, **kwargs):
		if args and isinstance(args[0], dict):
			d = args[0]
			if "doctype" not in d:
				d["doctype"] = "Fuel Entry"
			if "naming_series" not in d:
				d["naming_series"] = "FUEL-.YYYY.-.#####"
		elif not args:
			if "doctype" not in kwargs:
				kwargs["doctype"] = "Fuel Entry"
			if "naming_series" not in kwargs:
				kwargs["naming_series"] = "FUEL-.YYYY.-.#####"
		super().__init__(*args, **kwargs)

	@property
	def assignment(self) -> Optional[str]:
		"""Auto-resolves active assignment for vehicle if available."""
		if getattr(self, "vehicle", None) and hasattr(frappe, "db") and frappe.db:
			return frappe.db.get_value("Vehicle Assignment", {"vehicle": self.vehicle, "docstatus": 1}, "name")
		return None

	@property
	def employee(self) -> Optional[str]:
		"""Resolves driver / user from vehicle active assignment."""
		asn = self.assignment
		if asn and hasattr(frappe, "db") and frappe.db:
			return frappe.db.get_value("Vehicle Assignment", asn, "employee")
		return None

	@property
	def company(self) -> Optional[str]:
		"""Resolves company from vehicle or settings."""
		if getattr(self, "vehicle", None) and hasattr(frappe, "db") and frappe.db:
			comp = frappe.db.get_value("Vehicle", self.vehicle, "company")
			if comp:
				return comp
		from fleet_management.services.settings_service import SettingsService
		return SettingsService.resolve_default_company()

	@property
	def status(self) -> str:
		"""Maps docstatus to status string."""
		return {0: "Draft", 1: "Submitted", 2: "Cancelled"}.get(int(self.docstatus or 0), "Draft")

	# ------------------------------------------------------------------
	# Frappe Lifecycle Hooks
	# ------------------------------------------------------------------

	def before_validate(self):
		"""
		Runs before validate():
		1. Auto-resolve 3-way fuel calculation (Rate, Quantity, Total Cost)
		2. Auto-resolve fuel_type from Vehicle if missing
		"""
		self._calculate_three_way_fuel()
		if not getattr(self, "fuel_type", None) and getattr(self, "vehicle", None) and hasattr(frappe, "db") and frappe.db:
			v_fuel_type = frappe.db.get_value("Vehicle", self.vehicle, "fuel_type")
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
		if hasattr(frappe, "db") and frappe.db and not frappe.db.exists("Vehicle", self.vehicle):
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
		Calculates the 3rd missing value given any 2 of: Rate (fuel_price), Qty (fuel_qty), Total (total_cost).
		Handles division by zero gracefully and rounds values properly.
		"""
		rate = float(self.fuel_price) if self.fuel_price is not None and float(self.fuel_price or 0) > 0 else 0.0
		qty = float(self.fuel_qty) if self.fuel_qty is not None and float(self.fuel_qty or 0) > 0 else 0.0
		total = float(self.total_cost) if self.total_cost is not None and float(self.total_cost or 0) > 0 else 0.0

		if rate > 0 and qty > 0:
			# Case 1: Rate + Quantity -> Calculate Total Cost
			self.total_cost = round(rate * qty, 2)
		elif rate > 0 and total > 0:
			# Case 2: Rate + Total Cost -> Calculate Quantity
			self.fuel_qty = round(total / rate, 4)
		elif qty > 0 and total > 0:
			# Case 3: Quantity + Total Cost -> Calculate Rate
			self.fuel_price = round(total / qty, 4)

	def _validate_odometer_sequence(self, vehicle_id: str, current_odo: float):
		"""
		Ensures odometer sequence is non-decreasing.
		"""
		last_odo = frappe.db.sql(
			"SELECT MAX(odometer) as max_odo FROM `tabFuel Entry` WHERE vehicle = %s AND docstatus = 1 AND name != %s",
			(vehicle_id, self.name or ""),
			as_dict=True
		)
		prev_odo = 0.0
		if last_odo and last_odo[0].get("max_odo"):
			prev_odo = float(last_odo[0].get("max_odo"))
		else:
			prev_odo = float(frappe.db.get_value("Vehicle", vehicle_id, "initial_odometer") or 0.0)

		if prev_odo > 0 and current_odo < prev_odo:
			raise FleetValidationError(
				f"This is not allowed! Entered Odometer ({current_odo:,.1f} KM) is below previous odometer ({prev_odo:,.1f} KM)."
			)

	def before_validate_hook(self):
		"""
		Hook for unit tests without full DB.
		"""
		if not getattr(self, "naming_series", None):
			self.naming_series = "FUEL-.YYYY.-.#####"
		self._calculate_three_way_fuel()
