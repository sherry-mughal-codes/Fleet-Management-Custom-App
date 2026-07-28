"""
Fleet Analytics & Command Center Service Implementation
Fleet Management System
"""

from typing import Any, Dict, List

import frappe

from fleet_management.enums import VehicleStatus
from fleet_management.services.assignment_service import AssignmentService
from fleet_management.services.base_service import BaseService
from fleet_management.services.fleet_cost_service import FleetCostService
from fleet_management.services.fuel_service import FuelService
from fleet_management.services.maintenance_service import MaintenanceService
from fleet_management.services.vehicle_service import VehicleService
from fleet_management.utils.logger import get_logger

logger = get_logger("fleet_management.services.analytics")


class FleetAnalyticsService(BaseService):
	"""
	Central Fleet Analytics & Command Center Service.
	Aggregates executive KPIs, smart severity alerts, chart metric data feeds,
	vehicle health summaries, and recent activity logs by reusing existing domain services.
	Zero calculation duplication.
	"""

	def __init__(self):
		super().__init__()
		self.vehicle_service = VehicleService()
		self.assignment_service = AssignmentService()
		self.fuel_service = FuelService()
		self.maintenance_service = MaintenanceService()
		self.cost_service = FleetCostService()

	def get_executive_kpis(self, company: str | None = None) -> Dict[str, Any]:
		"""Calculates executive KPI cards for Desk Workspace (<30-second fleet understanding)."""
		filters = {"company": company} if company else {}

		total_vehicles = frappe.db.count("Vehicle", filters=filters) if hasattr(frappe, "db") else 0
		active_vehicles = frappe.db.count("Vehicle", filters={**filters, "status": ["in", [VehicleStatus.AVAILABLE, VehicleStatus.ASSIGNED]]}) if hasattr(frappe, "db") else 0
		assigned_vehicles = frappe.db.count("Vehicle", filters={**filters, "status": VehicleStatus.ASSIGNED}) if hasattr(frappe, "db") else 0
		available_vehicles = frappe.db.count("Vehicle", filters={**filters, "status": VehicleStatus.AVAILABLE}) if hasattr(frappe, "db") else 0
		maintenance_vehicles = frappe.db.count("Vehicle", filters={**filters, "status": VehicleStatus.UNDER_MAINTENANCE}) if hasattr(frappe, "db") else 0
		overdue_maintenance = frappe.db.count("Vehicle", filters={**filters, "status": VehicleStatus.MAINTENANCE_DUE}) if hasattr(frappe, "db") else 0

		today = frappe.utils.nowdate() if hasattr(frappe, "utils") else "2026-07-24"
		today_fuel_entries = frappe.db.count("Fuel Entry", filters={**filters, "fuel_date": today, "status": ["!=", "Cancelled"]}) if hasattr(frappe, "db") else 0
		today_maint_jobs = frappe.db.count("Maintenance Entry", filters={"maintenance_date": today, "docstatus": 1}) if hasattr(frappe, "db") else 0

		cost_stats = self.cost_service.calculate_company_cost(company)

		return {
			"total_vehicles": total_vehicles,
			"active_vehicles": active_vehicles,
			"assigned_vehicles": assigned_vehicles,
			"available_vehicles": available_vehicles,
			"under_maintenance": maintenance_vehicles,
			"overdue_maintenance": overdue_maintenance,
			"today_fuel_entries": today_fuel_entries,
			"today_maintenance_jobs": today_maint_jobs,
			"monthly_fuel_cost": cost_stats["total_fuel_cost"],
			"monthly_maintenance_cost": cost_stats["total_maintenance_cost"],
			"monthly_operating_cost": cost_stats["total_fleet_operating_cost"],
			"total_fuel_spend": cost_stats["total_fuel_cost"],
			"total_maintenance_spend": cost_stats["total_maintenance_cost"]
		}

	def get_smart_alerts(self, company: str | None = None) -> List[Dict[str, Any]]:
		"""Generates severity-based actionable smart alerts (Information, Warning, Critical)."""
		alerts = []
		filters = {"company": company} if company else {}

		if not hasattr(frappe, "get_all"):
			return alerts

		# 1. Critical Alert: Vehicles Under Maintenance or Overdue
		overdue_vehicles = frappe.get_all("Vehicle", filters={**filters, "status": VehicleStatus.MAINTENANCE_DUE}, fields=["name", "vehicle_number"])
		for v in overdue_vehicles:
			alerts.append({
				"severity": "Critical",
				"category": "Maintenance Overdue",
				"title": f"Maintenance Overdue: {v.vehicle_number}",
				"message": f"Vehicle '{v.vehicle_number}' is overdue for scheduled maintenance. Fuel entry is locked.",
				"reference_doctype": "Vehicle",
				"reference_name": v.name
			})

		# 2. Warning Alert: Fuel Locked Vehicles
		maint_locked = frappe.get_all("Vehicle", filters={**filters, "status": VehicleStatus.UNDER_MAINTENANCE}, fields=["name", "vehicle_number"])
		for v in maint_locked:
			alerts.append({
				"severity": "Warning",
				"category": "Fuel Locked",
				"title": f"Vehicle Fuel Locked: {v.vehicle_number}",
				"message": f"Vehicle '{v.vehicle_number}' is under maintenance. Complete work order to unlock fueling.",
				"reference_doctype": "Vehicle",
				"reference_name": v.name
			})

		# 3. Information Alert: Available Vehicles Ready for Assignment
		available_count = frappe.db.count("Vehicle", filters={**filters, "status": VehicleStatus.AVAILABLE}) if hasattr(frappe, "db") else 0
		if available_count > 0:
			alerts.append({
				"severity": "Information",
				"category": "Fleet Capacity",
				"title": "Available Fleet Capacity",
				"message": f"{available_count} vehicles are ready for driver assignment.",
				"reference_doctype": "Vehicle",
				"reference_name": ""
			})

		return alerts

	def get_analytics_charts(self, company: str | None = None) -> Dict[str, Any]:
		"""Returns chart data feeds for Fuel spend, Maintenance distribution, and Operating Costs."""
		cost_stats = self.cost_service.calculate_company_cost(company)

		return {
			"fuel_vs_maintenance": {
				"labels": ["Fuel Spend", "Maintenance Spend"],
				"datasets": [
					{"values": [cost_stats["total_fuel_cost"], cost_stats["total_maintenance_cost"]]}
				]
			},
			"vehicle_status_distribution": {
				"labels": ["Available", "Assigned", "Under Maintenance", "Maintenance Due"],
				"datasets": [
					{"values": [
						frappe.db.count("Vehicle", filters={"status": VehicleStatus.AVAILABLE}) if hasattr(frappe, "db") else 0,
						frappe.db.count("Vehicle", filters={"status": VehicleStatus.ASSIGNED}) if hasattr(frappe, "db") else 0,
						frappe.db.count("Vehicle", filters={"status": VehicleStatus.UNDER_MAINTENANCE}) if hasattr(frappe, "db") else 0,
						frappe.db.count("Vehicle", filters={"status": VehicleStatus.MAINTENANCE_DUE}) if hasattr(frappe, "db") else 0
					]}
				]
			}
		}

	def get_vehicle_health_summary(self, company: str | None = None, limit: int = 20) -> List[Dict[str, Any]]:
		"""Returns comprehensive vehicle health table with fuel economy, status, and operating spend."""
		if not hasattr(frappe, "get_all"):
			return []

		vehicles = frappe.get_all(
			"Vehicle",
			filters={"company": company} if company else {},
			fields=["name", "vehicle_number", "vehicle_name", "vehicle_brand", "vehicle_model", "current_odometer", "status", "expected_fuel_average"],

			order_by="modified desc",
			limit=limit
		)

		summary = []
		for v in vehicles:
			cost_data = self.cost_service.calculate_vehicle_cost(v.name)
			summary.append({
				"vehicle": v.name,
				"vehicle_number": v.vehicle_number,
				"vehicle_name": v.vehicle_name,
				"brand": v.vehicle_brand,
				"model": v.vehicle_model,
				"current_odometer": v.current_odometer,
				"status": v.status,
				"fuel_average": v.last_fuel_average or 0.0,
				"total_fuel_cost": cost_data["total_fuel_cost"],
				"total_maintenance_cost": cost_data["total_maintenance_cost"],
				"total_operating_cost": cost_data["total_operating_cost"],
				"cost_per_km": cost_data["cost_per_km"]
			})
		return summary

	def get_recent_activity_timeline(self, company: str | None = None, limit: int = 10) -> List[Dict[str, Any]]:
		"""Aggregates recent timeline activity events across Vehicle, Assignment, Fuel, and Maintenance."""
		activity = []

		if not hasattr(frappe, "get_all"):
			return activity

		# Fuel entries
		fuels = frappe.get_all("Fuel Entry", fields=["name", "vehicle", "fuel_date", "total_cost", "status"], order_by="creation desc", limit=5)
		for f in fuels:
			activity.append({
				"doctype": "Fuel Entry",
				"name": f.name,
				"vehicle": f.vehicle,
				"date": str(f.fuel_date),
				"title": f"Fuel Entry: {f.name}",
				"description": f"Logged fuel spend of ${f.total_cost} for vehicle {f.vehicle}."
			})

		# Maintenance Entries
		maints = frappe.get_all("Maintenance Entry", fields=["name", "assignment", "maintenance_date", "total_cost"], order_by="maintenance_date desc", limit=5) if hasattr(frappe, "get_all") else []
		for m in maints:
			activity.append({
				"doctype": "Maintenance Entry",
				"name": m.name,
				"vehicle": m.assignment,
				"date": str(m.maintenance_date),
				"title": f"Maintenance Entry: {m.name}",
				"description": f"Maintenance servicing completed. Total cost: {m.total_cost}."
			})

		activity.sort(key=lambda x: x.get("date", ""), reverse=True)
		return activity[:limit]

	def get_dashboard_data(self, user: str, company: str | None = None) -> Dict[str, Any]:
		"""Aggregates full command center payload for Desk Workspace."""
		return {
			"kpis": self.get_executive_kpis(company),
			"alerts": self.get_smart_alerts(company),
			"charts": self.get_analytics_charts(company),
			"vehicle_health": self.get_vehicle_health_summary(company, limit=10),
			"recent_activity": self.get_recent_activity_timeline(company, limit=10)
		}
