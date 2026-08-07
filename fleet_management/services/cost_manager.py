"""
Cost Manager Service
Fleet Management System (Frappe v15)

Centralized cost intelligence engine calculating fuel, maintenance,
and total operational expenditure for fleet vehicles.
"""

from typing import Any, Dict, Optional
import frappe

from fleet_management.services.base_service import BaseService
from fleet_management.utils.exceptions import FleetNotFoundError


class CostManager(BaseService):
	"""
	Enterprise service for Fleet Cost calculations.
	"""

	def calculate_vehicle_cost(self, vehicle_id: str) -> Dict[str, float]:
		"""Calculates total fuel, maintenance, and operating cost for a vehicle."""
		if not frappe.db.exists("Fleet Vehicle", vehicle_id):
			raise FleetNotFoundError(f"Vehicle '{vehicle_id}' not found.")

		# Fuel Cost Aggregation (via assignments)
		asn_names = [a.name for a in frappe.get_all("Vehicle Assignment", filters={"vehicle": vehicle_id}, fields=["name"])] if hasattr(frappe, "get_all") else []
		if asn_names:
			fuel_entries = frappe.get_all("Fuel Entry", filters={"assignment": ["in", asn_names], "docstatus": 1}, fields=["total_cost"]) if hasattr(frappe, "get_all") else []
		else:
			fuel_entries = []
		total_fuel_cost = sum(float(f.get("total_cost") or 0.0) for f in fuel_entries)

		# Maintenance Cost Aggregation (via Maintenance Entry)
		if asn_names:
			maint_entries = frappe.get_all("Maintenance Entry", filters={"assignment": ["in", asn_names], "docstatus": 1}, fields=["total_cost"]) if hasattr(frappe, "get_all") else []
		else:
			maint_entries = []
		total_maint_cost = sum(float(m.get("total_cost") or 0.0) for m in maint_entries)

		total_operating_cost = round(total_fuel_cost + total_maint_cost, 2)

		return {
			"vehicle": vehicle_id,
			"total_fuel_cost": round(total_fuel_cost, 2),
			"total_maintenance_cost": round(total_maint_cost, 2),
			"total_operating_cost": total_operating_cost
		}

	def get_company_cost_summary(self, company: Optional[str] = None) -> Dict[str, float]:
		"""Calculates company-wide cost summary."""
		fuel_filters: Dict[str, Any] = {"docstatus": 1}
		maint_filters: Dict[str, Any] = {"docstatus": 1}

		fuel_entries = frappe.get_all("Fuel Entry", filters=fuel_filters, fields=["total_cost"]) if hasattr(frappe, "get_all") else []
		maint_entries = frappe.get_all("Maintenance Entry", filters=maint_filters, fields=["total_cost"]) if hasattr(frappe, "get_all") else []

		total_fuel = sum(float(f.get("total_cost") or 0.0) for f in fuel_entries)
		total_maint = sum(float(m.get("total_cost") or 0.0) for m in maint_entries)

		return {
			"total_fuel_cost": round(total_fuel, 2),
			"total_maintenance_cost": round(total_maint, 2),
			"total_fleet_cost": round(total_fuel + total_maint, 2)
		}
