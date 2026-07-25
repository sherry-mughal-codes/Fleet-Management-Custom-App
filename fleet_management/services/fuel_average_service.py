"""
Fuel Average Engine Service Implementation
Fleet Management System
"""

from typing import Dict

import frappe

from fleet_management.utils.logger import get_logger

logger = get_logger("fleet_management.services.fuel_average")


class FuelAverageService:
	"""
	Central Calculation Engine for Fuel Economy & Distance Traveled.
	Calculates KM/L or MPG automatically using previous valid odometer readings.
	"""

	@staticmethod
	def calculate_entry_average(vehicle_id: str, current_odometer: float, fuel_qty: float) -> Dict[str, float]:
		"""
		Calculates distance since last fuel and fuel average (KM/L) for current entry.
		Returns dictionary containing 'distance_travelled' and 'fuel_average'.
		"""
		if not vehicle_id or not fuel_qty or float(fuel_qty) <= 0:
			return {"distance_travelled": 0.0, "fuel_average": 0.0}

		previous_odometer = 0.0
		if hasattr(frappe, "db"):
			last_entry = frappe.db.get_value(
				"Fuel Entry",
				filters={"vehicle": vehicle_id, "status": ["!=", "Cancelled"]},
				fieldname=["odometer"],
				order_by="creation desc"
			)
			if last_entry:
				previous_odometer = float(last_entry)

		if not previous_odometer:
			v_doc = frappe.db.get_value("Vehicle", vehicle_id, ["current_odometer", "initial_odometer"], as_dict=True) if hasattr(frappe, "db") else None
			if v_doc:
				previous_odometer = float(v_doc.get("initial_odometer") or 0.0)

		current = float(current_odometer)
		qty = float(fuel_qty)
		distance = max(0.0, current - previous_odometer)
		avg = distance / qty if (distance > 0 and qty > 0) else 0.0

		return {
			"distance_travelled": round(distance, 2),
			"fuel_average": round(avg, 2)
		}

	@staticmethod
	def get_lifetime_vehicle_average(vehicle_id: str) -> float:
		"""Calculates total lifetime fuel average for target vehicle."""
		if not hasattr(frappe, "get_all"):
			return 0.0
		entries = frappe.get_all(
			"Fuel Entry",
			filters={"vehicle": vehicle_id, "status": ["!=", "Cancelled"]},
			fields=["distance_since_last_fuel", "fuel_qty"]
		)
		total_dist = sum(float(e.get("distance_since_last_fuel") or 0.0) for e in entries)
		total_qty = sum(float(e.get("fuel_qty") or 0.0) for e in entries)
		return round(total_dist / total_qty, 2) if total_qty > 0 else 0.0
