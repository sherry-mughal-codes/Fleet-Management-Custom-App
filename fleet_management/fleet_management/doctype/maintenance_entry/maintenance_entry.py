"""
Maintenance Entry Controller Implementation
Fleet Management System (Frappe Framework v15)
"""

from typing import Any, Dict, List, Optional

import frappe
from frappe.model.document import Document

from fleet_management.services.maintenance_manager import MaintenanceManager
from fleet_management.services.vehicle_state_manager import VehicleStateManager
from fleet_management.utils.exceptions import FleetValidationError
from fleet_management.utils.logger import get_logger

logger = get_logger("fleet_management.doctype.maintenance_entry")


class MaintenanceEntry(Document):
	"""
	Submittable transactional document representing a completed vehicle maintenance servicing.
	Auto-loads template schedule lines from the linked Vehicle Assignment's vehicle category template.
	"""

	doctype = "Maintenance Entry"

	def __init__(self, *args, **kwargs):
		if args and isinstance(args[0], dict):
			if "doctype" not in args[0]:
				args[0]["doctype"] = "Maintenance Entry"
			if "vehicle" in args[0]:
				self._vehicle = args[0].get("vehicle")
			# Apply naming_series default when not provided
			if "naming_series" not in args[0]:
				args[0]["naming_series"] = "MAINT-.YYYY.-.#####"
		elif not args and "doctype" not in kwargs:
			kwargs["doctype"] = "Maintenance Entry"
			if "vehicle" in kwargs:
				self._vehicle = kwargs.get("vehicle")
			if "naming_series" not in kwargs:
				kwargs["naming_series"] = "MAINT-.YYYY.-.#####"
		super().__init__(*args, **kwargs)

	@property
	def vehicle(self) -> Optional[str]:
		"""Dynamic property resolving linked Vehicle from Vehicle Assignment."""
		if hasattr(self, "_vehicle") and self._vehicle:
			return self._vehicle
		if hasattr(self, "assignment") and self.assignment and hasattr(frappe, "db") and frappe.db:
			return frappe.db.get_value("Vehicle Assignment", self.assignment, "vehicle")
		return getattr(self, "vehicle_id", None)

	@vehicle.setter
	def vehicle(self, val: str):
		self._vehicle = val

	@property
	def employee(self) -> Optional[str]:
		"""Dynamic property resolving linked Employee/Driver from Vehicle Assignment."""
		if hasattr(self, "assignment") and self.assignment and hasattr(frappe, "db") and frappe.db:
			return frappe.db.get_value("Vehicle Assignment", self.assignment, "employee")
		return None

	@property
	def company(self) -> Optional[str]:
		"""Dynamic property resolving linked Company from Vehicle Assignment."""
		if hasattr(self, "assignment") and self.assignment and hasattr(frappe, "db") and frappe.db:
			return frappe.db.get_value("Vehicle Assignment", self.assignment, "company")
		return None

	@property
	def maintenance_type(self) -> str:
		"""Returns summary string of completed maintenance items."""
		completed = [i.item_name for i in getattr(self, "items", []) if getattr(i, "is_completed", 0)]
		return ", ".join(completed) if completed else "General Servicing"

	@property
	def rate(self) -> float:
		return float(getattr(self, "total_cost", 0.0) or 0.0)

	@property
	def qty(self) -> float:
		return 1.0

	def validate(self):
		"""Validates assignment link, auto-loads items if empty, and computes total cost."""
		if not self.assignment:
			v_id = getattr(self, "vehicle", None) or getattr(self, "_vehicle", None)
			if v_id and hasattr(frappe, "db") and frappe.db:
				active_assign = frappe.db.get_value("Vehicle Assignment", {"vehicle": v_id, "docstatus": 1}, "name")
				if not active_assign:
					active_assign = frappe.db.get_value("Vehicle Assignment", {"vehicle": v_id}, "name")
				if active_assign:
					self.assignment = active_assign

		if not self.assignment:
			raise FleetValidationError("Vehicle Assignment is mandatory for Maintenance Entry.")

		v_id = self.vehicle
		if not v_id:
			raise FleetValidationError(f"Could not resolve linked Vehicle for Assignment '{self.assignment}'.")

		# Validate odometer reading cannot be less than the vehicle's last recorded odometer
		if hasattr(frappe, "db") and frappe.db and v_id:
			last_odo = float(frappe.db.get_value("Vehicle", v_id, "current_odometer") or 0.0)
			if last_odo == 0.0:
				last_odo = float(frappe.db.get_value("Vehicle", v_id, "initial_odometer") or 0.0)
			curr_odo = float(self.current_odometer or 0.0)
			if last_odo > 0 and curr_odo > 0 and curr_odo < last_odo:
				raise FleetValidationError(f"Odometer reading ({curr_odo} KM) cannot be less than the previous recorded vehicle odometer ({last_odo} KM).")

		# Auto-load template schedule lines if items child table is empty
		if not getattr(self, "items", None):
			self.auto_load_template_items(v_id)

		# Calculate total cost from completed items (or default item costs)
		total = 0.0
		for item in getattr(self, "items", []):
			if item.is_completed:
				total += float(item.cost or 0.0)
		if total == 0.0:
			total = sum(float(item.cost or 0.0) for item in getattr(self, "items", []))
		self.total_cost = round(total, 2)

	def auto_load_template_items(self, vehicle_id: str):
		"""Auto-populates items child table with due maintenance items."""
		manager = MaintenanceManager()
		due_items = manager.get_due_maintenance(vehicle_id)
		for item in due_items:
			self.append("items", {
				"item_name": item["maintenance_type"],
				"interval_km": item["interval_km"],
				"is_mandatory": 1 if item["is_mandatory"] else 0,
				"priority": item.get("priority", "Medium"),
				"grace_distance": item.get("grace_distance", 0.0),
				"description": f"Servicing Due at {item['next_due_odometer']} KM",
				"is_completed": 1,
				"cost": 0.0
			})

	def on_submit(self):
		"""Executes transaction submission: updates vehicle odometer, resets completed items & vehicle state."""
		v_id = self.vehicle
		if not v_id:
			return

		odo = float(self.current_odometer or 0.0)

		# Update vehicle current odometer if higher
		curr_odo = float(frappe.db.get_value("Vehicle", v_id, "current_odometer") or 0.0)
		if odo > curr_odo:
			frappe.db.set_value("Vehicle", v_id, "current_odometer", round(odo, 1))

		# Update last maintenance odometer and date on vehicle
		m_date = self.maintenance_date or (frappe.utils.nowdate() if hasattr(frappe, "utils") else None)
		frappe.db.set_value("Vehicle", v_id, {
			"last_maintenance_odometer": round(odo, 1),
			"last_maintenance_date": m_date
		})

		# Recalculate operational statistics (updates last_maintenance_date & advances next_due_odo)
		from fleet_management.services.fleet_statistics_manager import FleetStatisticsManager
		FleetStatisticsManager.recalculate_vehicle_statistics(v_id)

		# Clear 'Under Maintenance' / 'Maintenance Due' / 'Fuel Locked' status upon servicing completion
		curr_status = frappe.db.get_value("Vehicle", v_id, "status")
		if curr_status in ("Under Maintenance", "Maintenance Due", "Fuel Locked"):
			active_asn = frappe.db.exists("Vehicle Assignment", {
				"vehicle": v_id,
				"docstatus": 1,
				"return_date": ["is", "not set"],
				"status": ["in", ["Assigned", "In Use", "Approved"]]
			})
			new_st = "Assigned" if active_asn else "Available"
			frappe.db.set_value("Vehicle", v_id, "status", new_st)

		VehicleStateManager.recalculate_vehicle_state(v_id)

		logger.info(f"Submitted Maintenance Entry {self.name} for Vehicle {v_id}")

	def on_cancel(self):
		"""Executes transaction reversal on document cancellation."""
		v_id = self.vehicle
		if not v_id:
			return

		from fleet_management.services.fleet_statistics_manager import FleetStatisticsManager
		FleetStatisticsManager.recalculate_vehicle_statistics(v_id)
		VehicleStateManager.recalculate_vehicle_state(v_id)

		logger.info(f"Cancelled Maintenance Entry {self.name} for Vehicle {v_id}")
