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
	The only stored reference is the Vehicle Assignment (field: assignment).
	Vehicle, employee, and company are resolved at runtime via the assignment.
	"""

	doctype = "Fuel Entry"

	def __init__(self, *args, **kwargs):
		if args and isinstance(args[0], dict):
			d = args[0]
			if "doctype" not in d:
				d["doctype"] = "Fuel Entry"
			if "naming_series" not in d:
				d["naming_series"] = "FUEL-.YYYY.-.#####"
			# Accept a vehicle kwarg for backwards-compat with service layer tests
			# but do NOT store it as a DB field — store temporarily for resolution
			if "vehicle" in d:
				self._vehicle_hint = d.pop("vehicle", None)
		elif not args:
			if "doctype" not in kwargs:
				kwargs["doctype"] = "Fuel Entry"
			if "naming_series" not in kwargs:
				kwargs["naming_series"] = "FUEL-.YYYY.-.#####"
		super().__init__(*args, **kwargs)

	# ------------------------------------------------------------------
	# Dynamic Properties — resolved from Vehicle Assignment
	# ------------------------------------------------------------------

	@property
	def vehicle(self) -> Optional[str]:
		"""Resolves linked Vehicle via Vehicle Assignment — never stored directly."""
		if hasattr(self, "_vehicle_hint") and self._vehicle_hint:
			return self._vehicle_hint
		if getattr(self, "assignment", None) and hasattr(frappe, "db") and frappe.db:
			v = frappe.db.get_value("Vehicle Assignment", self.assignment, "vehicle")
			if v:
				self._vehicle_hint = v
				return v
		return None

	@vehicle.setter
	def vehicle(self, val: str):
		"""Accept vehicle assignment in service layer but store only as a hint."""
		self._vehicle_hint = val

	@property
	def employee(self) -> Optional[str]:
		"""Resolves linked Employee via Vehicle Assignment."""
		if getattr(self, "assignment", None) and hasattr(frappe, "db") and frappe.db:
			return frappe.db.get_value("Vehicle Assignment", self.assignment, "employee")
		return None

	@property
	def company(self) -> Optional[str]:
		"""Resolves company via Vehicle Assignment."""
		if getattr(self, "assignment", None) and hasattr(frappe, "db") and frappe.db:
			return frappe.db.get_value("Vehicle Assignment", self.assignment, "company")
		return None

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
		1. Resolve assignment if only vehicle_hint provided (legacy service calls)
		2. Calculate total_cost from qty × rate
		3. Auto-populate all Fuel Intelligence fields
		"""
		self._auto_resolve_assignment()
		self._calculate_total_cost()
		self._populate_intelligence()

	def validate(self):
		"""
		Full server-side validation. Never rely on client scripts alone.
		"""
		# 1. Assignment is mandatory
		if not self.assignment:
			raise FleetValidationError("FUEL-001: Vehicle Assignment is mandatory for Fuel Entry.")

		# 2. Assignment must exist
		if hasattr(frappe, "db") and frappe.db and not frappe.db.exists("Vehicle Assignment", self.assignment):
			raise FleetValidationError(f"FUEL-001: Vehicle Assignment '{self.assignment}' does not exist.")

		# 3. Vehicle must resolve
		v_id = self.vehicle
		if not v_id:
			raise FleetValidationError(f"FUEL-001: Could not resolve Vehicle from Assignment '{self.assignment}'.")

		# 4. Fuel Quantity
		qty = float(self.fuel_qty or 0.0)
		if qty <= 0:
			raise FleetValidationError("FUEL-002: Fuel quantity (litres) must be greater than zero.")

		# 5. Rate Per Litre
		price = float(self.fuel_price or 0.0)
		if price <= 0:
			raise FleetValidationError("FUEL-003: Rate per litre must be greater than zero.")

		# 6. Odometer
		odo = float(self.odometer or 0.0)
		if odo <= 0:
			raise FleetValidationError("FUEL-004: Odometer reading must be greater than zero.")

		# 7. Odometer must not go backwards (non-decreasing sequence)
		if hasattr(frappe, "db") and frappe.db:
			self._validate_odometer_sequence(v_id, odo)

		# 8. Re-verify total cost on server
		expected_total = round(qty * price, 2)
		self.total_cost = expected_total

	def before_save(self):
		"""
		Non-blocking advisory check: warn if the odometer entered is
		suspiciously close (within 1 KM) to the previous submitted entry.
		This guards against accidental near-duplicate readings.
		"""
		v_id = self.vehicle
		odo = float(self.odometer or 0.0)
		if not v_id or odo <= 0 or not hasattr(frappe, "db") or not frappe.db:
			return

		prev = FuelIntelligenceEngine.get_previous_fuel_record(
			v_id,
			exclude_entry=self.name if getattr(self, "name", None) else None,
		)
		if prev:
			prev_odo = float(prev.get("odometer") or 0.0)
			gap = odo - prev_odo
			if 0 < gap < 1:
				frappe.msgprint(
					f"⚠️ Odometer reading ({odo:,.1f} KM) is only {gap:.2f} KM above "
					f"the previous entry ({prev_odo:,.1f} KM). Please verify the reading is correct.",
					indicator="orange",
					alert=True,
				)

	def on_submit(self):
		"""
		Post-submission business logic:
		1. Enforce Maintenance Lock (FUEL-008)
		2. Update Vehicle current_odometer if this entry has a higher reading
		3. Sync Vehicle operational summary
		4. Recalculate vehicle state
		"""
		v_id = self.vehicle
		odo = float(self.odometer or 0.0)

		if not v_id:
			logger.warning(f"Fuel Entry {self.name}: could not resolve vehicle on submit.")
			return

		# FUEL-008: Reject submission if vehicle is under maintenance
		MaintenanceLockService.enforce_maintenance_lock(v_id, odo)

		# Update vehicle current_odometer
		if hasattr(frappe, "db") and frappe.db:
			curr = float(frappe.db.get_value("Vehicle", v_id, "current_odometer") or 0.0)
			if odo > curr:
				frappe.db.set_value("Vehicle", v_id, "current_odometer", round(odo, 1))

		# Sync operational summary & recalculate state
		try:
			from fleet_management.services.fleet_statistics_manager import FleetStatisticsManager
			FleetStatisticsManager.recalculate_vehicle_statistics(v_id)
		except Exception as e:
			logger.warning(f"FleetStatisticsManager failed for {v_id}: {e}")

		try:
			VehicleStateManager.recalculate_vehicle_state(v_id)
		except Exception as e:
			logger.warning(f"VehicleStateManager failed for {v_id}: {e}")

		logger.info(f"Submitted Fuel Entry {self.name} for Assignment {self.assignment} | Vehicle {v_id}")

	def on_cancel(self):
		"""
		Post-cancellation business logic:
		Recalculate vehicle statistics to reverse this entry's contribution.
		"""
		v_id = self.vehicle
		if not v_id:
			return

		try:
			from fleet_management.services.fleet_statistics_manager import FleetStatisticsManager
			FleetStatisticsManager.recalculate_vehicle_statistics(v_id)
		except Exception as e:
			logger.warning(f"FleetStatisticsManager cancel reversal failed for {v_id}: {e}")

		try:
			VehicleStateManager.recalculate_vehicle_state(v_id)
		except Exception as e:
			logger.warning(f"VehicleStateManager cancel recalc failed for {v_id}: {e}")

		logger.info(f"Cancelled Fuel Entry {self.name}")

	# ------------------------------------------------------------------
	# Private Helpers
	# ------------------------------------------------------------------

	def _auto_resolve_assignment(self):
		"""
		Backwards-compat: if assignment is missing but we have a vehicle hint,
		try to find the active assignment for that vehicle.
		"""
		if self.assignment:
			return
		vehicle_hint = getattr(self, "_vehicle_hint", None)
		if vehicle_hint and hasattr(frappe, "db") and frappe.db:
			asn = frappe.db.get_value(
				"Vehicle Assignment",
				{"vehicle": vehicle_hint, "docstatus": 1},
				"name"
			) or frappe.db.get_value(
				"Vehicle Assignment",
				{"vehicle": vehicle_hint},
				"name"
			)
			if asn:
				self.assignment = asn

	def _calculate_total_cost(self):
		"""Calculates total_cost = fuel_qty × fuel_price. Defaults to 0.0 when inputs are zero."""
		qty = float(self.fuel_qty or 0.0)
		price = float(self.fuel_price or 0.0)
		if qty > 0 and price > 0:
			self.total_cost = round(qty * price, 2)
		elif qty > 0 and float(self.total_cost or 0.0) > 0:
			# Derive price from total if price missing
			self.fuel_price = round(float(self.total_cost) / qty, 4)
		else:
			# Ensure total_cost is never None
			if self.total_cost is None:
				self.total_cost = 0.0

	def _populate_intelligence(self):
		"""
		Calculates and populates all Fuel Intelligence fields:
		previous_odometer, previous_fuel_date, days_since_last_fuel,
		distance_travelled, fuel_average, cost_per_km, fuel_efficiency_rating,
		is_first_entry.
		"""
		v_id = self.vehicle
		if not v_id or not hasattr(frappe, "db") or not frappe.db:
			return

		odo = float(self.odometer or 0.0)
		qty = float(self.fuel_qty or 0.0)
		price = float(self.fuel_price or 0.0)

		if odo <= 0 or qty <= 0:
			return

		intel = FuelIntelligenceEngine.calculate_intelligence(
			vehicle_id=v_id,
			current_odometer=odo,
			fuel_qty=qty,
			fuel_price=price,
			fuel_date=self.fuel_date,
			exclude_entry=self.name if getattr(self, "name", None) else None,
		)

		self.is_first_entry = intel.get("is_first_entry", 0)
		self.previous_odometer = intel.get("previous_odometer", 0.0)
		self.previous_fuel_date = intel.get("previous_fuel_date")
		self.days_since_last_fuel = intel.get("days_since_last_fuel", 0)
		self.distance_travelled = intel.get("distance_travelled", 0.0)
		self.fuel_average = intel.get("fuel_average", 0.0)
		self.cost_per_km = intel.get("cost_per_km", 0.0)
		self.fuel_efficiency_rating = intel.get("fuel_efficiency_rating", "—")
		self.total_cost = intel.get("total_cost", self.total_cost)

	def _validate_odometer_sequence(self, vehicle_id: str, current_odo: float):
		"""
		Ensures the odometer never decreases (FUEL-004 advancement rule).
		Checks the previous submitted Fuel Entry.
		"""
		prev = FuelIntelligenceEngine.get_previous_fuel_record(
			vehicle_id,
			exclude_entry=self.name if getattr(self, "name", None) else None,
		)
		if prev:
			prev_odo = float(prev.get("odometer") or 0.0)
			if current_odo < prev_odo:
				raise FleetValidationError(
					f"FUEL-004: Odometer reading ({current_odo} KM) cannot be less than the "
					f"previous recorded odometer ({prev_odo} KM)."
				)

	# ------------------------------------------------------------------
	# Test-compatibility hook (used in unit tests without DB)
	# ------------------------------------------------------------------

	def before_validate_hook(self):
		"""
		Thin hook for unit tests that cannot invoke the full Frappe lifecycle.
		Runs pure calculation logic and raises FleetValidationError on invalid inputs.
		"""
		if not getattr(self, "naming_series", None):
			self.naming_series = "FUEL-.YYYY.-.#####"

		# Validate inputs (negative values are always rejected)
		qty = float(self.fuel_qty or 0.0)
		price = float(self.fuel_price or 0.0)

		if qty < 0:
			raise FleetValidationError("Fuel quantity (litres) cannot be negative.")
		if price < 0:
			raise FleetValidationError("Rate per litre cannot be negative.")

		self._calculate_total_cost()
