"""
Fleet Statistics Manager Service Implementation
Fleet Management System (Frappe Framework v15)
"""

from typing import Any, Dict, List, Optional

import frappe
from fleet_management.utils.logger import get_logger

logger = get_logger("fleet_management.services.statistics")


class FleetStatisticsManager:
	"""
	Centralized single source of truth for recalculating operational statistics across Vehicles,
	Employees, Companies, Fuel, Maintenance, and Executive Dashboard KPIs.
	"""

	@classmethod
	def recalculate_vehicle_statistics(cls, vehicle_id: str) -> Dict[str, Any]:
		"""Recalculates lifetime fuel average, maintenance costs, and Cost Per KM for a vehicle."""
		if not hasattr(frappe, "db") or not frappe.db or not frappe.db.exists("Vehicle", vehicle_id):
			return {}

		# Fetch all assignments for this vehicle
		assignments = frappe.get_all(
			"Vehicle Assignment",
			filters={"vehicle": vehicle_id},
			fields=["name", "employee"]
		) if hasattr(frappe, "get_all") else []
		asn_names = [a["name"] for a in assignments]

		# 1. Fuel Entry Stats
		fuel_entries = []
		if asn_names and hasattr(frappe, "get_all"):
			fuel_entries = frappe.get_all(
				"Fuel Entry",
				filters={"assignment": ["in", asn_names], "docstatus": 1},
				fields=["name", "fuel_date", "odometer", "fuel_qty", "fuel_price", "total_cost"],
				order_by="odometer asc, fuel_date asc"
			)

		total_liters = sum(float(f.get("fuel_qty") or 0.0) for f in fuel_entries)
		total_fuel_cost = sum(float(f.get("total_cost") or 0.0) for f in fuel_entries)

		# Fuel Average Calculation
		fuel_average = 0.0
		if len(fuel_entries) >= 2:
			min_odo = float(fuel_entries[0].get("odometer") or 0.0)
			max_odo = float(fuel_entries[-1].get("odometer") or 0.0)
			total_distance = max_odo - min_odo
			# Exclude first fill-up volume
			eval_liters = sum(float(f.get("fuel_qty") or 0.0) for f in fuel_entries[1:])
			if total_distance > 0 and eval_liters > 0:
				fuel_average = round(total_distance / eval_liters, 2)
		elif fuel_entries and float(fuel_entries[0].get("fuel_qty") or 0) > 0:
			fuel_average = round(float(fuel_entries[0].get("odometer") or 0) / float(fuel_entries[0].get("fuel_qty")), 2)

		last_fuel_date = fuel_entries[-1].get("fuel_date") if fuel_entries else None
		last_fuel_odo = float(fuel_entries[-1].get("odometer") or 0.0) if fuel_entries else 0.0

		# 2. Maintenance Entry Stats
		maint_entries = []
		if asn_names and hasattr(frappe, "get_all"):
			maint_entries = frappe.get_all(
				"Maintenance Entry",
				filters={"assignment": ["in", asn_names], "docstatus": 1},
				fields=["name", "total_cost"]
			)
		total_maint_cost = sum(float(m.get("total_cost") or 0.0) for m in maint_entries)

		# 3. Overall Vehicle Odometer & Cost Per KM
		v_doc = frappe.get_doc("Vehicle", vehicle_id)
		init_odo = float(v_doc.initial_odometer or 0.0)
		curr_odo = max(float(v_doc.current_odometer or 0.0), last_fuel_odo)
		total_distance_driven = max(curr_odo - init_odo, 0.0)
		total_operational_cost = total_fuel_cost + total_maint_cost

		cost_per_km = 0.0
		if total_distance_driven > 0:
			cost_per_km = round(total_operational_cost / total_distance_driven, 2)

		# Update Vehicle Record
		update_fields = {
			"current_odometer": curr_odo,
			"average_fuel_economy": fuel_average,
			"last_fuel_date": last_fuel_date,
			"total_fuel_cost": total_fuel_cost,
			"total_maintenance_cost": total_maint_cost,
			"lifetime_distance": total_distance_driven
		}
		frappe.db.set_value("Vehicle", vehicle_id, update_fields)
		logger.info(f"Recalculated statistics for Vehicle {vehicle_id}: Avg={fuel_average} KM/L, Cost/KM={cost_per_km}")

		return {
			"vehicle": vehicle_id,
			"total_liters": total_liters,
			"total_fuel_cost": total_fuel_cost,
			"fuel_average": fuel_average,
			"total_maintenance_cost": total_maint_cost,
			"total_operational_cost": total_operational_cost,
			"cost_per_km": cost_per_km
		}

	@classmethod
	def recalculate_employee_statistics(cls, employee_id: str) -> Dict[str, Any]:
		"""Recalculates fuel spend and assignment count for an employee."""
		if not hasattr(frappe, "db") or not frappe.db:
			return {}

		assignments = frappe.get_all("Vehicle Assignment", filters={"employee": employee_id}, fields=["name"]) if hasattr(frappe, "get_all") else []
		asn_names = [a["name"] for a in assignments]

		fuel_entries = frappe.get_all("Fuel Entry", filters={"assignment": ["in", asn_names], "docstatus": 1}, fields=["total_cost", "fuel_qty"]) if (asn_names and hasattr(frappe, "get_all")) else []
		return {
			"employee": employee_id,
			"total_assignments": len(assignments),
			"total_fuel_entries": len(fuel_entries),
			"total_fuel_qty": sum(float(f.get("fuel_qty") or 0.0) for f in fuel_entries),
			"total_fuel_spend": sum(float(f.get("total_cost") or 0.0) for f in fuel_entries)
		}

	@classmethod
	def recalculate_fleet_statistics(cls, company: Optional[str] = None) -> Dict[str, Any]:
		"""Recalculates aggregated fleet statistics for all vehicles."""
		if not hasattr(frappe, "db") or not frappe.db:
			return {}

		vehicles = frappe.get_all("Vehicle", filters={"company": company} if company else {}, fields=["name"]) if hasattr(frappe, "get_all") else []
		for v in vehicles:
			cls.recalculate_vehicle_statistics(v["name"])

		return {"total_vehicles": len(vehicles), "company": company or "All Companies"}

	@classmethod
	def get_dashboard_kpis(cls, company: Optional[str] = None) -> Dict[str, Any]:
		"""Retrieves operational KPIs for the Fleet Command Center Dashboard."""
		if not hasattr(frappe, "db") or not frappe.db:
			return {}

		filters = {"company": company} if company else {}

		total_vehicles = frappe.db.count("Vehicle", filters=filters)
		available_vehicles = frappe.db.count("Vehicle", filters={**filters, "status": "Available"})
		assigned_vehicles = frappe.db.count("Vehicle Assignment", filters={**filters, "docstatus": 1, "status": "Assigned"})
		maintenance_due = frappe.db.count("Vehicle", filters={**filters, "status": "Maintenance Due"})
		under_maintenance = frappe.db.count("Vehicle", filters={**filters, "status": "Under Maintenance"})
		fuel_locked = frappe.db.count("Vehicle", filters={**filters, "status": "Fuel Locked"})

		# Fuel and Maintenance Spends
		fuel_entries = frappe.get_all("Fuel Entry", filters={"docstatus": 1}, fields=["total_cost"]) if hasattr(frappe, "get_all") else []
		maint_entries = frappe.get_all("Maintenance Entry", filters={"docstatus": 1}, fields=["total_cost"]) if hasattr(frappe, "get_all") else []

		total_fuel_spend = sum(float(f.get("total_cost") or 0.0) for f in fuel_entries)
		total_maint_spend = sum(float(m.get("total_cost") or 0.0) for m in maint_entries)

		return {
			"total_vehicles": total_vehicles,
			"available_vehicles": available_vehicles,
			"assigned_vehicles": assigned_vehicles,
			"maintenance_due": maintenance_due,
			"under_maintenance": under_maintenance,
			"fuel_locked": fuel_locked,
			"total_fuel_spend": round(total_fuel_spend, 2),
			"total_maintenance_spend": round(total_maint_spend, 2),
			"total_fleet_spend": round(total_fuel_spend + total_maint_spend, 2)
		}
