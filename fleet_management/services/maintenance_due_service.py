"""
Maintenance Due Engine Service Implementation
Fleet Management System
"""

from typing import Any, Dict

import frappe

from fleet_management.utils.logger import get_logger

logger = get_logger("fleet_management.services.maintenance_due")


class MaintenanceDueEngine:
	"""
	Central Maintenance Due Calculation Engine implementing 4-tier policy hierarchy:
	1. Vehicle-specific interval (Vehicle.maintenance_interval_km)
	2. Maintenance Completion Override interval
	3. Maintenance Plan interval
	4. Fleet Settings default interval (5000 KM)
	"""

	@staticmethod
	def get_effective_maintenance_interval(vehicle_id: str, override_interval: float | None = None) -> float:
		"""Evaluates effective maintenance interval via policy hierarchy."""
		if override_interval and float(override_interval) > 0:
			return float(override_interval)

		if hasattr(frappe, "db") and frappe.db.exists("Vehicle", vehicle_id):
			v_interval = frappe.db.get_value("Vehicle", vehicle_id, "maintenance_interval_km")
			if v_interval and float(v_interval) > 0:
				return float(v_interval)

		return 5000.0

	@staticmethod
	def calculate_next_due_odometer(vehicle_id: str, completion_odometer: float | None = None, override_interval: float | None = None) -> float:
		"""Calculates next target due odometer reading."""
		base_odometer = float(completion_odometer or 0.0)
		if not base_odometer and hasattr(frappe, "db") and frappe.db.exists("Vehicle", vehicle_id):
			base_odometer = float(frappe.db.get_value("Vehicle", vehicle_id, "current_odometer") or 0.0)

		interval = MaintenanceDueEngine.get_effective_maintenance_interval(vehicle_id, override_interval)
		return round(base_odometer + interval, 2)

	@staticmethod
	def calculate_next_due_date(vehicle_id: str, completion_date: str | None = None, interval_days: int = 180) -> str | None:
		"""Calculates next target due date."""
		if not hasattr(frappe, "utils"):
			return None
		base_date = completion_date or (frappe.utils.nowdate() if hasattr(frappe, "utils") else None)
		if base_date:
			return str(frappe.utils.add_days(base_date, interval_days))
		return None

	@staticmethod
	def is_maintenance_overdue(vehicle_id: str, current_odometer: float | None = None) -> bool:
		"""Determines if vehicle maintenance is overdue."""
		if not hasattr(frappe, "db") or not frappe.db.exists("Vehicle", vehicle_id):
			return False

		v = frappe.db.get_value("Vehicle", vehicle_id, ["current_odometer", "last_maintenance_odometer", "maintenance_interval_km"], as_dict=True)
		if not v:
			return False

		odometer = float(current_odometer or v.current_odometer or 0.0)
		last_maint = float(v.last_maintenance_odometer or 0.0)
		interval = float(v.maintenance_interval_km or 5000.0)

		return odometer >= (last_maint + interval)

	@staticmethod
	def get_upcoming_maintenance_schedule(vehicle_id: str) -> Dict[str, Any]:
		"""Retrieves upcoming due schedule parameters."""
		due_odometer = MaintenanceDueEngine.calculate_next_due_odometer(vehicle_id)
		due_date = MaintenanceDueEngine.calculate_next_due_date(vehicle_id)
		overdue = MaintenanceDueEngine.is_maintenance_overdue(vehicle_id)

		return {
			"vehicle": vehicle_id,
			"next_due_odometer": due_odometer,
			"next_due_date": due_date,
			"is_overdue": overdue
		}
