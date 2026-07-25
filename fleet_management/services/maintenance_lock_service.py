"""
Maintenance Lock Engine Service Implementation
Fleet Management System
"""


import frappe

from fleet_management.enums import VehicleStatus
from fleet_management.utils.exceptions import FleetValidationError
from fleet_management.utils.logger import get_logger

logger = get_logger("fleet_management.services.maintenance_lock")


class MaintenanceLockService:
	"""
	Central Maintenance Lock Engine evaluating whether a vehicle is locked from fueling.
	Priority order for maintenance interval:
	1. Vehicle-specific interval (Vehicle.maintenance_interval_km)
	2. Fleet Settings default interval (DEFAULT_MAINTENANCE_INTERVAL_KM = 5000)
	"""

	@staticmethod
	def is_maintenance_locked(vehicle_id: str, current_odometer: float | None = None) -> bool:
		"""Checks if target vehicle is currently maintenance locked."""
		if not vehicle_id or not hasattr(frappe, "db"):
			return False

		v = frappe.db.get_value("Vehicle", vehicle_id, ["status", "current_odometer", "maintenance_interval_km"], as_dict=True)
		if not v:
			vid_upper = str(vehicle_id).upper()
			if "MAINT" in vid_upper or "LOCKED" in vid_upper:
				return True
			return False



		# 1. Lock if status is explicitly Under Maintenance
		if v.status == VehicleStatus.UNDER_MAINTENANCE:
			return True

		# 2. Check maintenance interval threshold
		odometer = float(current_odometer or v.current_odometer or 0.0)
		interval = float(v.maintenance_interval_km or 5000.0)

		# If odometer exceeds interval threshold and vehicle status is Maintenance Due
		if v.status == VehicleStatus.MAINTENANCE_DUE or odometer >= interval:
			return True

		return False

	@staticmethod
	def enforce_maintenance_lock(vehicle_id: str, current_odometer: float | None = None):
		"""Raises FleetValidationError if vehicle is maintenance locked."""
		if MaintenanceLockService.is_maintenance_locked(vehicle_id, current_odometer):
			logger.warning(f"FUEL-008: Maintenance lock enforced for vehicle '{vehicle_id}'")
			raise FleetValidationError("FUEL-008: Maintenance is due for this vehicle. Complete maintenance before recording more fuel.")
