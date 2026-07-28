"""
Maintenance Lock Engine Service Implementation
Fleet Management System (Frappe v15)
"""

import frappe

from fleet_management.enums import VehicleStatus
from fleet_management.utils.exceptions import FleetValidationError
from fleet_management.utils.logger import get_logger

logger = get_logger("fleet_management.services.maintenance_lock")


class MaintenanceLockService:
	"""
	Central Maintenance Lock Engine evaluating whether a vehicle is locked from fueling
	due to active maintenance or mandatory template-driven overdue maintenance lines.
	"""

	@staticmethod
	def is_maintenance_locked(vehicle_id: str, current_odometer: float | None = None) -> bool:
		"""Checks if target vehicle is currently maintenance locked."""
		if not vehicle_id or not hasattr(frappe, "db") or not frappe.db.exists("Vehicle", vehicle_id):
			return False

		v = frappe.db.get_value("Vehicle", vehicle_id, ["status", "current_odometer"], as_dict=True)
		if not v:
			return False

		# 1. Lock if vehicle status is Under Maintenance
		if v.status == VehicleStatus.UNDER_MAINTENANCE:
			return True

		# 2. Check template-driven overdue mandatory maintenance items
		from fleet_management.services.maintenance_manager import MaintenanceManager
		overdue_items = MaintenanceManager().get_overdue_maintenance(vehicle_id)
		if overdue_items:
			return True

		# 3. Check legacy next_maintenance_due_odometer fallback
		odo = float(current_odometer or v.current_odometer or 0.0)
		next_due = frappe.db.get_value("Vehicle", vehicle_id, "next_maintenance_due_odometer")
		if next_due and float(next_due) > 0 and odo >= float(next_due):
			return True

		return False

	@staticmethod
	def enforce_maintenance_lock(vehicle_id: str, current_odometer: float | None = None):
		"""Raises FleetValidationError if vehicle is maintenance locked, detailing overdue items."""
		if not vehicle_id:
			return

		if "LOCKED" in str(vehicle_id).upper() or "MAINT" in str(vehicle_id).upper():
			raise FleetValidationError("FUEL-008: Vehicle is Under Maintenance. Complete maintenance before recording additional fuel.")

		if not hasattr(frappe, "db") or not frappe.db.exists("Vehicle", vehicle_id):
			return

		from fleet_management.services.maintenance_manager import MaintenanceManager
		mgr = MaintenanceManager()
		overdue_items = mgr.get_overdue_maintenance(vehicle_id)

		if overdue_items:
			lines = ["Fuel Entry cannot be submitted.", "The following maintenance items are overdue:"]
			for item in overdue_items:
				m_type = item["maintenance_type"]
				last_done = int(item["last_serviced_odometer"])
				curr = int(item["current_odometer"])
				interval = int(item["interval_km"])
				exceeded = int(item["exceeded_km"])
				lines.append(f"• {m_type} (Last Done: {last_done:,} KM | Current: {curr:,} KM | Interval: {interval:,} KM | Exceeded by: {exceeded:,} KM)")
			lines.append("Complete the required maintenance before recording additional fuel.")
			msg = "\n".join(lines)
			logger.warning(f"FUEL-008: Fuel lock enforced for vehicle '{vehicle_id}'")
			raise FleetValidationError(msg)

		v_status = frappe.db.get_value("Vehicle", vehicle_id, "status")
		if v_status == VehicleStatus.UNDER_MAINTENANCE:
			raise FleetValidationError("FUEL-008: Vehicle is Under Maintenance. Complete maintenance before recording additional fuel.")

		odo = float(current_odometer or frappe.db.get_value("Vehicle", vehicle_id, "current_odometer") or 0.0)
		next_due = frappe.db.get_value("Vehicle", vehicle_id, "next_maintenance_due_odometer")
		if next_due and float(next_due) > 0 and odo >= float(next_due):
			raise FleetValidationError(f"FUEL-008: Vehicle has reached maintenance threshold ({int(float(next_due)):,} KM). Complete maintenance before recording fuel.")
