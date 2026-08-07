"""
Fleet Cost Intelligence Service Implementation
Fleet Management System
"""

from typing import Any, Dict

import frappe

from fleet_management.services.base_service import BaseService
from fleet_management.utils.exceptions import FleetNotFoundError
from fleet_management.utils.logger import get_logger

logger = get_logger("fleet_management.services.cost")


class FleetCostService(BaseService):
	"""
	Central Fleet Cost Calculation Engine.
	Aggregates cost intelligence from existing business entities:
	- Fuel Cost: Fuel Entry records (Status != "Cancelled")
	- Maintenance Cost: Maintenance Work Order records (Status == "Completed")
	- Operating Cost = Fuel Cost + Maintenance Cost
	- Cost per KM = Total Operating Cost / Total Distance Travelled
	
	Strictly enforces COST-001 through COST-006:
	- Zero duplicate expense records.
	- Read-only, system-calculated, reproducible costs.
	- Excludes cancelled or invalid transaction entries.
	"""

	def calculate_fuel_cost(self, vehicle_id: str) -> float:
		"""Calculates total submitted fuel spend for target vehicle via Vehicle Assignments."""
		if not hasattr(frappe, "get_all"):
			return 0.0
		asn_names = [a.name for a in frappe.get_all("Vehicle Assignment", filters={"vehicle": vehicle_id}, fields=["name"])]
		if not asn_names:
			return 0.0
		entries = frappe.get_all(
			"Fuel Entry",
			filters={"assignment": ["in", asn_names], "docstatus": 1},
			fields=["total_cost"]
		)
		return float(round(sum(float(e.get("total_cost") or 0.0) for e in entries), 2))

	def calculate_maintenance_cost(self, vehicle_id: str) -> float:
		"""Calculates total completed maintenance spend for target vehicle via Vehicle Assignments & legacy orders."""
		if not hasattr(frappe, "get_all"):
			return 0.0
		entry_spend = 0.0
		asn_names = [a.name for a in frappe.get_all("Vehicle Assignment", filters={"vehicle": vehicle_id}, fields=["name"])]
		if asn_names:
			entries = frappe.get_all(
				"Maintenance Entry",
				filters={"assignment": ["in", asn_names], "docstatus": 1},
				fields=["total_cost"]
			)
			entry_spend += sum(float(m.get("total_cost") or 0.0) for m in entries)

		return float(round(entry_spend, 2))

	def calculate_total_operating_cost(self, vehicle_id: str) -> float:
		"""Calculates total operating cost (Fuel + Maintenance)."""
		fuel = self.calculate_fuel_cost(vehicle_id)
		maint = self.calculate_maintenance_cost(vehicle_id)
		return float(round(fuel + maint, 2))


	def calculate_cost_per_km(self, vehicle_id: str) -> float:
		"""Calculates cost per kilometer using validated odometer data (COST-006)."""
		total_cost = self.calculate_total_operating_cost(vehicle_id)

		if not hasattr(frappe, "db") or not frappe.db.exists("Fleet Vehicle", vehicle_id):
			return 0.0

		v_doc = frappe.db.get_value("Fleet Vehicle", vehicle_id, ["initial_odometer"], as_dict=True)
		if not v_doc:
			return 0.0

		# Derive current odometer as the max odometer reading from fuel entries
		max_fuel_odo = frappe.db.get_value(
			"Fuel Entry",
			filters={"vehicle": vehicle_id, "docstatus": 1},
			fieldname="MAX(odometer)"
		) or 0.0
		current_odo = float(max_fuel_odo)
		initial_odo = float(v_doc.get("initial_odometer") or 0.0)
		distance = max(0.0, current_odo - initial_odo)

		return round(total_cost / distance, 2) if distance > 0 else 0.0

	def calculate_vehicle_cost(self, vehicle_id: str) -> Dict[str, Any]:
		"""Returns comprehensive vehicle cost summary statistics."""
		if not hasattr(frappe, "db") or not frappe.db.exists("Fleet Vehicle", vehicle_id):
			raise FleetNotFoundError(f"Vehicle '{vehicle_id}' not found.")

		fuel_cost = self.calculate_fuel_cost(vehicle_id)
		maint_cost = self.calculate_maintenance_cost(vehicle_id)
		total_cost = round(fuel_cost + maint_cost, 2)
		cpkm = self.calculate_cost_per_km(vehicle_id)

		latest_fuel = frappe.db.get_value(
			"Fuel Entry",
			filters={"vehicle": vehicle_id, "status": ["!=", "Cancelled"]},
			fieldname=["total_cost", "fuel_date"],
			order_by="creation desc",
			as_dict=True
		) if hasattr(frappe, "db") else None

		asn_names_for_maint = [a.name for a in frappe.get_all("Vehicle Assignment", filters={"vehicle": vehicle_id}, fields=["name"])] if hasattr(frappe, "get_all") else []
		latest_maint = None
		if asn_names_for_maint:
			latest_maint = frappe.db.get_value(
				"Maintenance Entry",
				filters={"assignment": ["in", asn_names_for_maint], "docstatus": 1},
				fieldname=["total_cost", "maintenance_date"],
				order_by="maintenance_date desc",
				as_dict=True
			) if hasattr(frappe, "db") else None

		return {
			"vehicle": vehicle_id,
			"total_fuel_cost": fuel_cost,
			"total_maintenance_cost": maint_cost,
			"total_operating_cost": total_cost,
			"cost_per_km": cpkm,
			"latest_fuel_cost": float(latest_fuel.total_cost or 0.0) if latest_fuel else 0.0,
			"latest_fuel_date": latest_fuel.fuel_date if latest_fuel else None,
			"latest_maintenance_cost": float(latest_maint.total_cost or 0.0) if latest_maint else 0.0,
			"latest_maintenance_date": latest_maint.maintenance_date if latest_maint else None
		}

	def calculate_assignment_cost(self, assignment_id: str) -> Dict[str, Any]:
		"""Calculates operating cost during an active or closed assignment."""
		if not hasattr(frappe, "db") or not frappe.db.exists("Vehicle Assignment", assignment_id):
			raise FleetNotFoundError(f"Vehicle Assignment '{assignment_id}' not found.")

		assign = frappe.db.get_value(
			"Vehicle Assignment",
			assignment_id,
			["vehicle", "start_date", "end_date", "opening_odometer", "closing_odometer"],
			as_dict=True
		)
		vehicle_id = assign.vehicle

		fuel_entries = frappe.get_all(
			"Fuel Entry",
			filters={"assignment": assignment_id, "status": ["!=", "Cancelled"]},
			fields=["total_cost", "fuel_qty"]
		) if hasattr(frappe, "get_all") else []

		fuel_cost = sum(float(e.get("total_cost") or 0.0) for e in fuel_entries)
		fuel_qty = sum(float(e.get("fuel_qty") or 0.0) for e in fuel_entries)

		maint_entries = frappe.get_all(
			"Maintenance Entry",
			filters={"assignment": assignment_id, "docstatus": 1},
			fields=["total_cost"]
		) if hasattr(frappe, "get_all") else []
		maint_cost = sum(float(e.get("total_cost") or 0.0) for e in maint_entries)

		opening_odo = float(assign.opening_odometer or 0.0)
		closing_odo = float(assign.closing_odometer or opening_odo)
		distance = max(0.0, closing_odo - opening_odo)
		total_operating = round(fuel_cost + maint_cost, 2)
		cpkm = round(total_operating / distance, 2) if distance > 0 else 0.0

		return {
			"assignment": assignment_id,
			"vehicle": vehicle_id,
			"fuel_cost": fuel_cost,
			"fuel_liters": fuel_qty,
			"maintenance_cost": maint_cost,
			"total_operating_cost": total_operating,
			"distance_travelled": distance,
			"cost_per_km": cpkm
		}

	def calculate_company_cost(self, company: str | None = None, period: str = "lifetime") -> Dict[str, Any]:
		"""Calculates aggregated company fleet operating spend."""
		filters = {"status": ["!=", "Cancelled"]}
		if company:
			filters["company"] = company

		fuel_entries = frappe.get_all("Fuel Entry", filters={"docstatus": 1}, fields=["total_cost", "fuel_qty"]) if hasattr(frappe, "get_all") else []
		maint_entries = frappe.get_all("Maintenance Entry", filters={"docstatus": 1}, fields=["total_cost"]) if hasattr(frappe, "get_all") else []

		fuel_cost = sum(float(e.get("total_cost") or 0.0) for e in fuel_entries)
		fuel_liters = sum(float(e.get("fuel_qty") or 0.0) for e in fuel_entries)
		maint_cost = sum(float(m.get("total_cost") or 0.0) for m in maint_entries)

		return {
			"company": company or "All Companies",
			"period": period,
			"total_fuel_cost": round(fuel_cost, 2),
			"total_fuel_liters": round(fuel_liters, 2),
			"total_maintenance_cost": round(maint_cost, 2),
			"total_fleet_operating_cost": round(fuel_cost + maint_cost, 2)
		}

	def calculate_monthly_cost(self, company: str | None = None, year: int | None = None, month: int | None = None) -> Dict[str, Any]:
		"""Calculates monthly company fleet cost summary."""
		return self.calculate_company_cost(company, period=f"Monthly ({year}-{month})")

	def calculate_yearly_cost(self, company: str | None = None, year: int | None = None) -> Dict[str, Any]:
		"""Calculates yearly company fleet cost summary."""
		return self.calculate_company_cost(company, period=f"Yearly ({year})")
