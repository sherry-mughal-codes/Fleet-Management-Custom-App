"""
Fuel Intelligence Engine Service
Fleet Management System (Frappe Framework v15)

Provides smart odometer resolution, previous-entry lookup,
and automatic calculation of all Fuel Intelligence metrics.
"""

from typing import Any, Dict, Optional
from datetime import date

import frappe

from fleet_management.utils.logger import get_logger

logger = get_logger("fleet_management.services.fuel_intelligence")

# Fallback thresholds when Fleet Settings are unavailable
_DEFAULT_EXCELLENT = 15.0
_DEFAULT_GOOD = 10.0
_DEFAULT_AVERAGE = 7.0


class FuelIntelligenceEngine:
	"""
	Central Fuel Intelligence calculation engine.
	All methods are @staticmethod — no instance state required.
	"""

	# ------------------------------------------------------------------
	# 1. Smart Odometer Resolution
	# ------------------------------------------------------------------

	@staticmethod
	def get_smart_odometer(assignment_id: str, vehicle_id: Optional[str] = None) -> float:
		"""
		Resolves the best starting odometer for a new Fuel Entry.

		Priority order (as approved):
		  1. Latest submitted Fuel Entry odometer for the vehicle (via assignment join)
		  2. Vehicle current_odometer
		  3. Assignment opening_odometer (fallback)

		Returns 0.0 if nothing is found.
		"""
		if not hasattr(frappe, "db") or not frappe.db:
			return 0.0

		# Resolve vehicle_id if not passed
		if not vehicle_id and assignment_id:
			vehicle_id = frappe.db.get_value("Vehicle Assignment", assignment_id, "vehicle")

		if vehicle_id:
			# Step 1 — Latest submitted Fuel Entry for vehicle (join via assignments)
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
					return float(result[0]["odometer"])
			except Exception as e:
				logger.warning(f"Smart odometer step 1 failed: {e}")

			# Step 2 — Vehicle current_odometer
			curr = frappe.db.get_value("Vehicle", vehicle_id, "current_odometer")
			if curr and float(curr) > 0:
				return float(curr)

		# Step 3 — Assignment opening_odometer fallback
		if assignment_id:
			opening = frappe.db.get_value("Vehicle Assignment", assignment_id, "opening_odometer")
			if opening and float(opening) > 0:
				return float(opening)

		return 0.0

	# ------------------------------------------------------------------
	# 2. Previous Fuel Record Lookup
	# ------------------------------------------------------------------

	@staticmethod
	def get_previous_fuel_record(vehicle_id: str, exclude_entry: Optional[str] = None) -> Optional[Dict[str, Any]]:
		"""
		Finds the most recent submitted Fuel Entry for the vehicle.
		Joins through Vehicle Assignment — no direct 'vehicle' column on Fuel Entry.

		Returns dict with keys:
		  name, fuel_date, odometer, fuel_qty, total_cost, fuel_average
		or None if this is the first entry.
		"""
		if not vehicle_id or not hasattr(frappe, "db") or not frappe.db:
			return None

		try:
			where_exclude = "AND fe.name != %s" if exclude_entry else ""
			params = [vehicle_id, exclude_entry] if exclude_entry else [vehicle_id]

			results = frappe.db.sql(f"""
				SELECT
					fe.name,
					fe.fuel_date,
					fe.odometer,
					fe.fuel_qty,
					fe.total_cost,
					fe.fuel_average
				FROM `tabFuel Entry` fe
				INNER JOIN `tabVehicle Assignment` va ON va.name = fe.assignment
				WHERE va.vehicle = %s
				  AND fe.docstatus = 1
				  {where_exclude}
				ORDER BY fe.fuel_date DESC, fe.creation DESC
				LIMIT 1
			""", params, as_dict=True)

			return results[0] if results else None
		except Exception as e:
			logger.warning(f"Previous fuel record lookup failed for {vehicle_id}: {e}")
			return None

	# ------------------------------------------------------------------
	# 3. Full Intelligence Calculation
	# ------------------------------------------------------------------

	@staticmethod
	def calculate_intelligence(
		vehicle_id: str,
		current_odometer: float,
		fuel_qty: float,
		fuel_price: float,
		fuel_date: Any,
		exclude_entry: Optional[str] = None
	) -> Dict[str, Any]:
		"""
		Calculates all Fuel Intelligence metrics for a given Fuel Entry.

		Returns:
		  previous_odometer, previous_fuel_date, days_since_last_fuel,
		  distance_travelled, fuel_average, cost_per_km,
		  fuel_efficiency_rating, is_first_entry, total_cost
		"""
		current_odometer = float(current_odometer or 0.0)
		fuel_qty = float(fuel_qty or 0.0)
		fuel_price = float(fuel_price or 0.0)
		total_cost = round(fuel_qty * fuel_price, 2)

		prev = FuelIntelligenceEngine.get_previous_fuel_record(vehicle_id, exclude_entry=exclude_entry)

		is_first_entry = prev is None
		previous_odometer = 0.0
		previous_fuel_date = None
		days_since_last_fuel = 0
		distance_travelled = 0.0
		fuel_average = 0.0
		cost_per_km = 0.0

		if prev:
			previous_odometer = float(prev.get("odometer") or 0.0)
			previous_fuel_date = prev.get("fuel_date")

			# Distance
			distance_travelled = max(0.0, current_odometer - previous_odometer)

			# Days since last fuel
			if previous_fuel_date and fuel_date:
				try:
					if isinstance(fuel_date, str):
						from datetime import datetime
						fuel_date_obj = datetime.strptime(fuel_date, "%Y-%m-%d").date()
					else:
						fuel_date_obj = fuel_date
					if isinstance(previous_fuel_date, str):
						from datetime import datetime
						prev_date_obj = datetime.strptime(str(previous_fuel_date), "%Y-%m-%d").date()
					else:
						prev_date_obj = previous_fuel_date
					days_since_last_fuel = max(0, (fuel_date_obj - prev_date_obj).days)
				except Exception:
					days_since_last_fuel = 0

			# Fuel Economy (KM/L)
			if distance_travelled > 0 and fuel_qty > 0:
				fuel_average = round(distance_travelled / fuel_qty, 2)

			# Cost Per KM
			if distance_travelled > 0 and total_cost > 0:
				cost_per_km = round(total_cost / distance_travelled, 4)

		fuel_efficiency_rating = FuelIntelligenceEngine.classify_efficiency(fuel_average)

		return {
			"is_first_entry": 1 if is_first_entry else 0,
			"previous_odometer": round(previous_odometer, 2),
			"previous_fuel_date": str(previous_fuel_date) if previous_fuel_date else None,
			"days_since_last_fuel": days_since_last_fuel,
			"distance_travelled": round(distance_travelled, 2),
			"fuel_average": fuel_average,
			"cost_per_km": cost_per_km,
			"fuel_efficiency_rating": fuel_efficiency_rating,
			"total_cost": total_cost,
		}

	# ------------------------------------------------------------------
	# 4. Efficiency Classification
	# ------------------------------------------------------------------

	@staticmethod
	def classify_efficiency(fuel_average: float) -> str:
		"""
		Classifies fuel average (KM/L) into a rating band.
		Thresholds are read from Fleet Settings (with hardcoded fallbacks).
		"""
		if not fuel_average or float(fuel_average) <= 0:
			return "—"

		try:
			settings = frappe.get_single("Fleet Settings") if hasattr(frappe, "get_single") else None
			excellent = float(getattr(settings, "excellent_fuel_economy_kmpl", None) or _DEFAULT_EXCELLENT)
			good = float(getattr(settings, "good_fuel_economy_kmpl", None) or _DEFAULT_GOOD)
			average = float(getattr(settings, "average_fuel_economy_kmpl", None) or _DEFAULT_AVERAGE)
		except Exception:
			excellent, good, average = _DEFAULT_EXCELLENT, _DEFAULT_GOOD, _DEFAULT_AVERAGE

		avg = float(fuel_average)
		if avg >= excellent:
			return "Excellent"
		elif avg >= good:
			return "Good"
		elif avg >= average:
			return "Average"
		else:
			return "Poor"
