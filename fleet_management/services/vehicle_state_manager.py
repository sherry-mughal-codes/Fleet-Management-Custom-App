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
			["status", "current_odometer", "next_maintenance_due_odometer", "current_employee"],
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

		# 3. Check Maintenance Due State
		curr_odo = float(v_data.get("current_odometer") or 0.0)
		due_odo = float(v_data.get("next_maintenance_due_odometer") or 0.0)
		if due_odo > 0 and curr_odo >= due_odo:
			return VehicleStatus.MAINTENANCE_DUE

		# 4. Check Assigned State (Active submitted assignment)
		active_assignment = frappe.db.exists(
			"Vehicle Assignment",
			{
				"vehicle": vehicle_id,
				"docstatus": 1,
				"return_date": ["is", "not set"],
				"status": ["in", ["Assigned", "In Use", "Approved"]]
			}
		)
		if active_assignment or v_data.get("current_employee"):
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
			frappe.db.set_value(
				"Vehicle",
				vehicle_id,
				"current_assignment_status",
				"Assigned" if new_status == VehicleStatus.ASSIGNED else "Unassigned"
			)
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
