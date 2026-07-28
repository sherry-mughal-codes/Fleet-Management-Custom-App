"""
Fuel Average Engine Service Implementation
Fleet Management System

Queries Fuel Entry records exclusively via Vehicle Assignment joins.
No direct 'vehicle' column is stored on Fuel Entry.
"""

from typing import Dict

import frappe

from fleet_management.utils.logger import get_logger

logger = get_logger("fleet_management.services.fuel_average")


class FuelAverageService:
	"""
	Central Calculation Engine for Fuel Economy & Distance Traveled.
	Calculates KM/L automatically using previous valid odometer readings.
	Queries Fuel Entry via Vehicle Assignment join — never via a direct vehicle column.
	"""

	@staticmethod
	def calculate_entry_average(vehicle_id: str, current_odometer: float, fuel_qty: float) -> Dict[str, float]:
		"""
		Calculates distance since last fuel and fuel average (KM/L) for the current entry.
		Returns dict containing 'distance_travelled' and 'fuel_average'.
		"""
		if not vehicle_id or not fuel_qty or float(fuel_qty) <= 0:
			return {"distance_travelled": 0.0, "fuel_average": 0.0}

		previous_odometer = 0.0
		if hasattr(frappe, "db") and frappe.db:
			try:
				result = frappe.db.sql("""
					SELECT fe.odometer
					FROM `tabFuel Entry` fe
					INNER JOIN `tabVehicle Assignment` va ON va.name = fe.assignment
					WHERE va.vehicle = %s
					  AND fe.docstatus = 1
					ORDER BY fe.fuel_date DESC, fe.creation DESC
					LIMIT 1
				""", (vehicle_id,), as_dict=True)
				if result and result[0].get("odometer"):
					previous_odometer = float(result[0]["odometer"])
			except Exception as e:
				logger.warning(f"FuelAverageService step 1 failed for {vehicle_id}: {e}")

		# Fallback: vehicle initial_odometer
		if not previous_odometer and hasattr(frappe, "db") and frappe.db:
			v_doc = frappe.db.get_value(
				"Vehicle", vehicle_id, ["current_odometer", "initial_odometer"], as_dict=True
			)
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
		"""Calculates total lifetime fuel average for the target vehicle."""
		if not hasattr(frappe, "db") or not frappe.db:
			return 0.0
		try:
			result = frappe.db.sql("""
				SELECT fe.distance_travelled, fe.fuel_qty
				FROM `tabFuel Entry` fe
				INNER JOIN `tabVehicle Assignment` va ON va.name = fe.assignment
				WHERE va.vehicle = %s
				  AND fe.docstatus = 1
			""", (vehicle_id,), as_dict=True)
		except Exception as e:
			logger.warning(f"Lifetime average query failed for {vehicle_id}: {e}")
			return 0.0

		total_dist = sum(float(e.get("distance_travelled") or 0.0) for e in result)
		total_qty = sum(float(e.get("fuel_qty") or 0.0) for e in result)
		return round(total_dist / total_qty, 2) if total_qty > 0 else 0.0
