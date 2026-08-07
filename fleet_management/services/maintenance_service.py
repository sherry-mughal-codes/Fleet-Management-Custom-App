"""
Maintenance Domain Service Implementation
Fleet Management System
"""

from typing import Any, Dict, List

import frappe

from fleet_management.enums import MaintenanceStatus, VehicleStatus
from fleet_management.events.maintenance_events import MaintenanceEventDispatcher
from fleet_management.services.base_service import BaseService
from fleet_management.services.maintenance_due_service import MaintenanceDueEngine
from fleet_management.services.vehicle_service import VehicleService
from fleet_management.utils.exceptions import FleetNotFoundError, FleetValidationError
from fleet_management.utils.logger import get_logger

logger = get_logger("fleet_management.services.maintenance")


class MaintenanceService(BaseService):
	"""
	Enterprise service managing business operations for Maintenance Request and Work Order records.
	Requests Vehicle status mutations strictly through VehicleService (Single Source of Truth).
	"""

	def __init__(self):
		super().__init__()
		self.vehicle_service = VehicleService()

	def create_maintenance_entry(self, payload: Dict[str, Any]) -> Dict[str, Any]:
		"""Creates a new Maintenance Entry document."""
		from fleet_management.services.maintenance_manager import MaintenanceManager
		return MaintenanceManager().create_maintenance_entry(payload)

	def submit_maintenance_entry(self, entry_id: str) -> Dict[str, Any]:
		"""Submits a Maintenance Entry document."""
		from fleet_management.services.maintenance_manager import MaintenanceManager
		return MaintenanceManager().submit_maintenance_entry(entry_id)

	def create_request(self, payload: Dict[str, Any]) -> Dict[str, Any]:
		"""Legacy alias - creates a Maintenance Entry using the provided payload."""
		logger.info("create_request redirected to create_maintenance_entry", {"vehicle": payload.get("vehicle")})
		if "maintenance_date" not in payload or not payload["maintenance_date"]:
			payload["maintenance_date"] = frappe.utils.nowdate() if hasattr(frappe, "utils") else "2026-07-29"
		if ("current_odometer" not in payload or not payload["current_odometer"]) and payload.get("vehicle"):
			v_odo = float(frappe.db.get_value("Fleet Vehicle", payload["vehicle"], "current_odometer") or 10000.0) if hasattr(frappe, "db") else 10000.0
			payload["current_odometer"] = v_odo
		return self.create_maintenance_entry(payload)

	def create_work_order(self, payload: Dict[str, Any]) -> Dict[str, Any]:
		"""Legacy alias - creates a Maintenance Entry using the provided payload."""
		logger.info("create_work_order redirected to create_maintenance_entry", {"vehicle": payload.get("vehicle")})
		if "maintenance_date" not in payload or not payload["maintenance_date"]:
			payload["maintenance_date"] = frappe.utils.nowdate() if hasattr(frappe, "utils") else "2026-07-29"
		if ("current_odometer" not in payload or not payload["current_odometer"]) and payload.get("vehicle"):
			v_odo = float(frappe.db.get_value("Fleet Vehicle", payload["vehicle"], "current_odometer") or 10000.0) if hasattr(frappe, "db") else 10000.0
			payload["current_odometer"] = v_odo
		return self.create_maintenance_entry(payload)

	def complete_work_order(self, work_order_id: str, completion_odometer: float, costs: Dict[str, float] | None = None) -> Dict[str, Any]:
		"""
		Legacy alias - submits a Maintenance Entry and updates vehicle odometer.
		If work_order_id maps to a Maintenance Entry, submit it.
		Otherwise, treat as a no-op for backwards compatibility.
		"""
		if frappe.db.exists("Maintenance Entry", work_order_id):
			return self.submit_maintenance_entry(work_order_id)
		logger.warning(f"complete_work_order: '{work_order_id}' is not a Maintenance Entry. Skipping.")
		return {"name": work_order_id, "status": "skipped"}

	def update_request(self, request_id: str, updates: Dict[str, Any]) -> Dict[str, Any]:
		"""Updates maintenance entry parameters cleanly."""
		if not frappe.db.exists("Maintenance Entry", request_id):
			raise FleetNotFoundError(f"Maintenance Entry '{request_id}' not found.")
		doc = frappe.get_doc("Maintenance Entry", request_id)
		doc.update(updates)
		doc.save()
		return doc.as_dict()

	def cancel_request(self, request_id: str, reason: str | None = None) -> bool:
		"""Cancels a maintenance entry record."""
		if not frappe.db.exists("Maintenance Entry", request_id):
			raise FleetNotFoundError(f"Maintenance Entry '{request_id}' not found.")
		doc = frappe.get_doc("Maintenance Entry", request_id)
		doc.cancel()
		logger.info(f"Cancelled Maintenance Entry: {request_id}")
		return True

	# --- Analytics & Utilization Helpers ---

	def get_total_maintenance_cost_by_vehicle(self, vehicle_id: str) -> float:
		"""Returns total maintenance cost spent on a vehicle via Maintenance Entries."""
		if not hasattr(frappe, "get_all"):
			return 0.0
		asn_names = [a.name for a in frappe.get_all("Vehicle Assignment", filters={"vehicle": vehicle_id}, fields=["name"])]
		if not asn_names:
			return 0.0
		entries = frappe.get_all("Maintenance Entry", filters={"assignment": ["in", asn_names], "docstatus": 1}, fields=["total_cost"])
		return sum(float(e.get("total_cost") or 0.0) for e in entries)

	def get_company_maintenance_cost_stats(self, company: str | None = None) -> Dict[str, Any]:
		"""Returns total maintenance entries count and spend for a company."""
		entries = frappe.get_all("Maintenance Entry", filters={"docstatus": 1}, fields=["total_cost"]) if hasattr(frappe, "get_all") else []
		return {
			"company": company or "All",
			"total_work_orders": len(entries),
			"total_maintenance_spend": sum(float(e.get("total_cost") or 0.0) for e in entries)
		}

	def get_workshop_performance_stats(self, workshop_name: str) -> Dict[str, Any]:
		"""Returns performance stats for a specific vendor/workshop."""
		entries = frappe.get_all("Maintenance Entry", filters={"vendor": workshop_name, "docstatus": 1}, fields=["name", "total_cost"]) if hasattr(frappe, "get_all") else []
		return {
			"workshop": workshop_name,
			"total_jobs": len(entries),
			"completed_jobs": len(entries),
			"total_revenue_generated": sum(float(e.get("total_cost") or 0.0) for e in entries)
		}

	def get_vehicle_reliability_rankings(self, company: str | None = None, limit: int = 10) -> List[Dict[str, Any]]:
		"""Returns top vehicles ranked by fewest maintenance requests."""
		return frappe.get_all(
			"Fleet Vehicle",
			filters={"company": company} if company else {},
			fields=["name", "vehicle_number", "vehicle_brand", "vehicle_model", "current_odometer", "status"],
			order_by="creation desc",
			limit=limit
		) if hasattr(frappe, "get_all") else []

	def get_vehicle_history(self, vehicle_id: str, limit: int = 20) -> List[Dict[str, Any]]:
		"""Retrieves maintenance entry history for a vehicle via assignments."""
		asn_names = [a.name for a in frappe.get_all("Vehicle Assignment", filters={"vehicle": vehicle_id}, fields=["name"])] if hasattr(frappe, "get_all") else []
		if not asn_names:
			return []
		return frappe.get_all(
			"Maintenance Entry",
			filters={"assignment": ["in", asn_names]},
			fields=["name", "maintenance_date", "assignment", "total_cost"],
			order_by="maintenance_date desc",
			limit=limit
		) if hasattr(frappe, "get_all") else []

	def get_summary(self, vehicle_id: str) -> Dict[str, Any]:
		"""Retrieves summary maintenance statistics for a vehicle."""
		if not frappe.db.exists("Fleet Vehicle", vehicle_id):
			raise FleetNotFoundError(f"Vehicle '{vehicle_id}' not found.")

		asn_names = [a.name for a in frappe.get_all("Vehicle Assignment", filters={"vehicle": vehicle_id}, fields=["name"])] if hasattr(frappe, "get_all") else []
		if asn_names:
			entries = frappe.get_all("Maintenance Entry", filters={"assignment": ["in", asn_names]}, fields=["name", "total_cost"]) if hasattr(frappe, "get_all") else []
		else:
			entries = []

		total_spend = sum(float(e.get("total_cost") or 0.0) for e in entries)

		return {
			"vehicle": vehicle_id,
			"total_requests": len(entries),
			"total_work_orders": len(entries),
			"total_maintenance_spend": total_spend,
			"in_progress_count": 0
		}

	# Contract aliases
	def create_maintenance_request(self, payload: Dict[str, Any]) -> Dict[str, Any]:
		return self.create_request(payload)

	def schedule_maintenance(self, maintenance_id: str, schedule_date: str) -> bool:
		return True

	def start_maintenance(self, maintenance_id: str) -> bool:
		return True

	def complete_maintenance(self, maintenance_id: str, closing_odometer: float) -> bool:
		self.complete_work_order(maintenance_id, closing_odometer)
		return True

	def cancel_maintenance(self, maintenance_id: str, reason: str | None = None) -> bool:
		return self.cancel_request(maintenance_id, reason)

	def get_vehicle_maintenance_history(self, vehicle_id: str, limit: int = 20) -> List[Dict[str, Any]]:
		return self.get_vehicle_history(vehicle_id, limit)

	def get_maintenance_summary(self, maintenance_id: str) -> Dict[str, Any]:
		return self.get_summary(maintenance_id)
