"""
Vehicle State Manager
Fleet Management System (Frappe v15)

Centralized engine for calculating and updating Vehicle operational status.
This is the ONLY component allowed to alter Vehicle state.
"""

from typing import Optional
import frappe

from fleet_management.enums import VehicleStatus
from fleet_management.services.base_service import BaseService
from fleet_management.utils.exceptions import FleetNotFoundError
from fleet_management.utils.logger import get_logger

logger = get_logger("fleet_management.services.vehicle_state_manager")


class VehicleStateManager(BaseService):
	"""
	Enterprise service for computing and updating Vehicle operational state.
	Enforces deterministic, rule-based status calculation.
	"""

	@staticmethod
	def calculate_vehicle_state(vehicle_id: str) -> str:
		"""
		Calculates the deterministic operational state of a vehicle based on DB records:
		1. Retired: if status is Retired or Out of Service/Scrapped.
		2. Under Maintenance: if there is an active/submitted Maintenance Work Order.
		3. Maintenance Due: if current_odometer >= next_maintenance_due_odometer.
		4. Assigned: if there is an active/submitted Vehicle Assignment without return_date.
		5. Available: default state.
		"""
		if not frappe.db.exists("Vehicle", vehicle_id):
			raise FleetNotFoundError(f"Vehicle '{vehicle_id}' not found.")

		v_data = frappe.db.get_value(
			"Vehicle",
			vehicle_id,
			["status"],
			as_dict=True
		)

		if not v_data:
			return VehicleStatus.AVAILABLE

		current_status = v_data.get("status")

		# 1. Check Retired / Inactive / Scrapped / Sold / Out of Service States (preserves terminal states)
		if current_status in ("Retired", "Scrapped", "Sold", "Out of Service", "Archived"):
			return current_status

		# 2. Check Explicit Under Maintenance State
		if current_status == "Under Maintenance":
			return VehicleStatus.UNDER_MAINTENANCE

		# 3. Check Maintenance Due State (via MaintenanceManager due items)
		try:
			from fleet_management.services.maintenance_manager import MaintenanceManager
			due_items = MaintenanceManager().get_due_maintenance(vehicle_id)
			if due_items and any(d.get("is_mandatory") for d in due_items):
				return VehicleStatus.MAINTENANCE_DUE
		except Exception:
			pass

		# 4. Check Assigned State (Active submitted assignment)
		active_assignment = frappe.db.exists(
			"Vehicle Assignment",
			{
				"vehicle": vehicle_id,
				"docstatus": 1,
				"return_date": ["is", "not set"],
				"status": ["in", ["Assigned", "In Use", "Approved", "Return Overdue"]]
			}
		)
		if active_assignment:
			return VehicleStatus.ASSIGNED

		# 5. Default State
		return VehicleStatus.AVAILABLE

	def update_vehicle_state(self, vehicle_id: str, reason: Optional[str] = None) -> str:
		"""
		Calculates and persists the updated operational status for a vehicle.
		Single point of status persistence for Vehicle records.
		"""
		if not vehicle_id or not frappe.db.exists("Vehicle", vehicle_id):
			return VehicleStatus.AVAILABLE

		new_status = self.calculate_vehicle_state(vehicle_id)
		old_status = frappe.db.get_value("Vehicle", vehicle_id, "status")

		if old_status != new_status:
			frappe.db.set_value("Vehicle", vehicle_id, "status", new_status)
			logger.info(
				f"Vehicle State Recalculated: {vehicle_id} [{old_status} -> {new_status}]",
				{"reason": reason or "State Manager Recalculation"}
			)

		return new_status

	@classmethod
	def recalculate_vehicle_state(cls, vehicle_id: str, reason: Optional[str] = None) -> str:
		"""Classmethod helper for quick vehicle state recalculation."""
		manager = cls()
		return manager.update_vehicle_state(vehicle_id, reason=reason)


def recalculate_vehicle_state(vehicle_id: str, reason: Optional[str] = None) -> str:
	"""Module-level function helper."""
	return VehicleStateManager.recalculate_vehicle_state(vehicle_id, reason=reason)


def sync_all_vehicles():
	"""Recalculates state for all vehicles in database."""
	if not hasattr(frappe, "db") or not hasattr(frappe, "get_all"):
		return
	vehicles = frappe.get_all("Vehicle", fields=["name"])
	for v in vehicles:
		VehicleStateManager.recalculate_vehicle_state(v.get("name"), reason="Batch sync")
