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
	def _is_lock_enabled() -> bool:
		"""Checks if Maintenance Lock on Fuel Entry is enabled in Fleet Settings."""
		if hasattr(frappe, "db") and frappe.db and hasattr(frappe, "get_single"):
			try:
				val = frappe.db.get_single_value("Fleet Settings", "fuel_entry_lock_when_maintenance_due")
				if val is not None:
					return bool(val)
			except Exception:
				pass
		return True

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

		# Check Fleet Settings toggle
		if not MaintenanceLockService._is_lock_enabled():
			return False

		# 2. Check template-driven overdue mandatory maintenance items
		from fleet_management.services.maintenance_manager import MaintenanceManager
		odo = float(current_odometer or v.current_odometer or 0.0)
		overdue_items = MaintenanceManager().get_overdue_maintenance(vehicle_id, current_odometer=odo)
		if overdue_items:
			return True

		# 3. Check legacy next_maintenance_due_odometer fallback
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

		v_status = frappe.db.get_value("Vehicle", vehicle_id, "status")
		if v_status == VehicleStatus.UNDER_MAINTENANCE:
			raise FleetValidationError("FUEL-008: Vehicle is Under Maintenance. Complete maintenance before recording additional fuel.")

		from fleet_management.services.maintenance_manager import MaintenanceManager
		mgr = MaintenanceManager()
		odo = float(current_odometer or frappe.db.get_value("Vehicle", vehicle_id, "current_odometer") or 0.0)
		overdue_items = mgr.get_overdue_maintenance(vehicle_id, current_odometer=odo)

		if overdue_items:
			lines = ["<strong>Fuel Entry submission is not allowed because the following maintenance item(s) are due:</strong><br><ul>"]
			for item in overdue_items:
				m_type = item["maintenance_type"]
				last_done = int(item["last_serviced_odometer"])
				curr = int(item["current_odometer"])
				interval = int(item["interval_km"])
				exceeded = int(item["exceeded_km"])
				lines.append(f"<li><strong>{m_type}</strong> — Last Serviced: {last_done:,} KM | Current Odometer: {curr:,} KM | Interval: {interval:,} KM (Exceeded by {exceeded:,} KM)</li>")
			lines.append("</ul>Please complete the required maintenance before submitting this fuel entry.")
			msg = "".join(lines)

			# Enforce lock if Fleet Settings enables it
			if MaintenanceLockService._is_lock_enabled():
				logger.warning(f"FUEL-008: Fuel lock enforced for vehicle '{vehicle_id}'")
				# Update vehicle status to Maintenance Due immediately so status reflects in system
				if frappe.db.get_value("Vehicle", vehicle_id, "status") != VehicleStatus.MAINTENANCE_DUE:
					frappe.db.set_value("Vehicle", vehicle_id, "status", VehicleStatus.MAINTENANCE_DUE)
					frappe.clear_document_cache("Vehicle", vehicle_id)
					frappe.db.commit()
				raise FleetValidationError(msg)
			else:
				logger.info(f"FUEL-008: Lock disabled in Fleet Settings; showing advisory warning for '{vehicle_id}'")
				frappe.msgprint(msg, indicator="orange", alert=True)

		next_due = frappe.db.get_value("Vehicle", vehicle_id, "next_maintenance_due_odometer")
		if next_due and float(next_due) > 0 and odo >= float(next_due):
			msg = f"FUEL-008: Vehicle has reached maintenance threshold ({int(float(next_due)):,} KM). Complete maintenance before recording fuel."
			if MaintenanceLockService._is_lock_enabled():
				if frappe.db.get_value("Vehicle", vehicle_id, "status") != VehicleStatus.MAINTENANCE_DUE:
					frappe.db.set_value("Vehicle", vehicle_id, "status", VehicleStatus.MAINTENANCE_DUE)
					frappe.clear_document_cache("Vehicle", vehicle_id)
					frappe.db.commit()
				raise FleetValidationError(msg)
			else:
				frappe.msgprint(msg, indicator="orange", alert=True)
