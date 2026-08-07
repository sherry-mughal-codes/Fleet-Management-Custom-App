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
	Linked directly to Vehicle. Auto-loads template schedule lines from Vehicle.maintenance_template.
	"""

	doctype = "Maintenance Entry"

	def __init__(self, *args, **kwargs):
		if args and isinstance(args[0], dict):
			if "doctype" not in args[0]:
				args[0]["doctype"] = "Maintenance Entry"
			if "naming_series" not in args[0]:
				args[0]["naming_series"] = "MAINT-.YYYY.-.#####"
		elif not args and "doctype" not in kwargs:
			kwargs["doctype"] = "Maintenance Entry"
			if "naming_series" not in kwargs:
				kwargs["naming_series"] = "MAINT-.YYYY.-.#####"
		super().__init__(*args, **kwargs)

	@property
	def assignment(self) -> Optional[str]:
		"""Auto-resolves active assignment for this vehicle if one exists."""
		if getattr(self, "vehicle", None) and hasattr(frappe, "db") and frappe.db:
			return frappe.db.get_value("Vehicle Assignment", {"vehicle": self.vehicle, "docstatus": 1}, "name")
		return None

	@property
	def employee(self) -> Optional[str]:
		"""Resolves driver/user from vehicle active assignment."""
		asn = self.assignment
		if asn and hasattr(frappe, "db") and frappe.db:
			return frappe.db.get_value("Vehicle Assignment", asn, "employee")
		return None

	@property
	def company(self) -> Optional[str]:
		"""Resolves company from vehicle."""
		if getattr(self, "vehicle", None) and hasattr(frappe, "db") and frappe.db:
			return frappe.db.get_value("Fleet Vehicle", self.vehicle, "company")
		from fleet_management.services.settings_service import SettingsService
		return SettingsService.resolve_default_company()

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
		"""Validates vehicle link, auto-loads items if empty, computes total cost."""
		if not getattr(self, "vehicle", None):
			raise FleetValidationError("Vehicle is mandatory for Maintenance Entry.")

		if hasattr(frappe, "db") and frappe.db and not frappe.db.exists("Fleet Vehicle", self.vehicle):
			raise FleetValidationError(f"Vehicle '{self.vehicle}' does not exist.")

		v_id = self.vehicle

		# Validate odometer
		if hasattr(frappe, "db") and frappe.db and v_id:
			latest_fuel_odo = frappe.db.get_value("Fuel Entry", {"vehicle": v_id, "docstatus": 1}, "MAX(odometer)") or 0.0
			last_odo = float(latest_fuel_odo)
			if last_odo == 0.0:
				last_odo = float(frappe.db.get_value("Fleet Vehicle", v_id, "initial_odometer") or 0.0)
			curr_odo = float(self.current_odometer or 0.0)
			if last_odo > 0 and curr_odo > 0 and curr_odo < last_odo:
				raise FleetValidationError(f"Odometer reading ({curr_odo} KM) cannot be less than vehicle odometer ({last_odo} KM).")

		# Auto-load template schedule lines if items child table is empty
		if not getattr(self, "items", None):
			self.auto_load_template_items(v_id)

		# Calculate total cost from completed items
		total = 0.0
		for item in getattr(self, "items", []):
			if item.is_completed:
				total += float(item.cost or 0.0)
		if total == 0.0:
			total = sum(float(item.cost or 0.0) for item in getattr(self, "items", []))
		self.total_cost = round(total, 2)

	def auto_load_template_items(self, vehicle_id: str):
		"""Auto-populates items child table using Vehicle.maintenance_template (not category)."""
		manager = MaintenanceManager()
		due_items = manager.get_due_maintenance(vehicle_id)
		for item in due_items:
			self.append("items", {
				"item_name": item["maintenance_type"],
				"interval_km": item["interval_km"],
				"is_mandatory": 1 if item["is_mandatory"] else 0,
				"priority": item.get("priority", "Medium"),
				"description": f"Servicing Due at {item['next_due_odometer']} KM",
				"is_completed": 1,
				"cost": 0.0
			})

	def on_submit(self):
		"""Executes submission: recalculates vehicle statistics & updates vehicle state."""
		v_id = self.vehicle
		if not v_id:
			return

		# Recalculate operational statistics
		from fleet_management.services.fleet_statistics_manager import FleetStatisticsManager
		FleetStatisticsManager.recalculate_vehicle_statistics(v_id)

		# Clear Maintenance status after servicing
		curr_status = frappe.db.get_value("Fleet Vehicle", v_id, "status")
		if curr_status in ("Under Maintenance", "Maintenance Due", "Fuel Locked"):
			active_asn = frappe.db.exists("Vehicle Assignment", {
				"vehicle": v_id,
				"docstatus": 1,
				"return_date": ["is", "not set"],
				"status": ["in", ["Assigned", "In Use", "Approved", "Return Overdue"]]
			})
			new_st = "Assigned" if active_asn else "Available"
			frappe.db.set_value("Fleet Vehicle", v_id, "status", new_st)

		VehicleStateManager.recalculate_vehicle_state(v_id)
		logger.info(f"Submitted Maintenance Entry {self.name} for Vehicle {v_id}")

	def on_cancel(self):
		"""Executes reversal on document cancellation."""
		v_id = self.vehicle
		if not v_id:
			return
		from fleet_management.services.fleet_statistics_manager import FleetStatisticsManager
		FleetStatisticsManager.recalculate_vehicle_statistics(v_id)
		VehicleStateManager.recalculate_vehicle_state(v_id)
		logger.info(f"Cancelled Maintenance Entry {self.name} for Vehicle {v_id}")
