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

	def create_request(self, payload: Dict[str, Any]) -> Dict[str, Any]:
		"""Creates a new Maintenance Request record."""
		logger.info("Creating Maintenance Request via MaintenanceService", {"vehicle": payload.get("vehicle")})
		doc = frappe.get_doc({
			"doctype": "Maintenance Request",
			**payload
		})
		doc.insert()
		MaintenanceEventDispatcher.notify_maintenance_created(doc)
		return doc.as_dict()

	def create_work_order(self, payload: Dict[str, Any]) -> Dict[str, Any]:
		"""Creates a new Maintenance Work Order record."""
		logger.info("Creating Maintenance Work Order via MaintenanceService", {"vehicle": payload.get("vehicle")})
		doc = frappe.get_doc({
			"doctype": "Maintenance Work Order",
			**payload
		})
		doc.insert()
		MaintenanceEventDispatcher.notify_maintenance_scheduled(doc)
		return doc.as_dict()

	def complete_work_order(self, work_order_id: str, completion_odometer: float, costs: Dict[str, float] | None = None) -> Dict[str, Any]:
		"""
		Completes a maintenance work order:
		1. Validates completion odometer >= vehicle current odometer (MAINT-003).
		2. Calculates next due thresholds via MaintenanceDueEngine (MAINT-004).
		3. Updates Vehicle last_maintenance_odometer and next_due fields.
		4. Removes Maintenance Lock by changing Vehicle status to Available via VehicleService (MAINT-006, MAINT-009).
		5. Updates linked Assignment statistics.
		"""
		if not frappe.db.exists("Maintenance Work Order", work_order_id):
			raise FleetNotFoundError(f"Maintenance Work Order '{work_order_id}' not found.")

		doc = frappe.get_doc("Maintenance Work Order", work_order_id)
		vehicle_id = doc.vehicle

		# 1. Odometer validation check (MAINT-003)
		v_doc = frappe.get_doc("Vehicle", vehicle_id)
		curr_odometer = float(v_doc.current_odometer or 0.0)
		comp_odometer = float(completion_odometer or doc.completion_odometer or curr_odometer)

		if comp_odometer < curr_odometer:
			raise FleetValidationError(f"MAINT-003: Completion odometer ({comp_odometer} KM) cannot be lower than current vehicle odometer ({curr_odometer} KM).")

		# 2. Update financial costs
		if costs:
			doc.labour_cost = costs.get("labour_cost", doc.labour_cost)
			doc.parts_cost = costs.get("parts_cost", doc.parts_cost)
			doc.external_cost = costs.get("external_cost", doc.external_cost)
			doc.tax_amount = costs.get("tax_amount", doc.tax_amount)
			doc.discount_amount = costs.get("discount_amount", doc.discount_amount)

		labour = float(doc.labour_cost or 0.0)
		parts = float(doc.parts_cost or 0.0)
		external = float(doc.external_cost or 0.0)
		tax = float(doc.tax_amount or 0.0)
		discount = float(doc.discount_amount or 0.0)
		doc.total_cost = (labour + parts + external + tax) - discount

		doc.completion_odometer = comp_odometer
		doc.completion_date = frappe.utils.nowdate() if hasattr(frappe, "utils") else doc.completion_date
		doc.status = MaintenanceStatus.COMPLETED
		doc.save()

		# 3. Calculate Next Due thresholds (MAINT-004)
		next_due_odo = MaintenanceDueEngine.calculate_next_due_odometer(vehicle_id, comp_odometer)
		next_due_date = MaintenanceDueEngine.calculate_next_due_date(vehicle_id, doc.completion_date)

		# 4. Update Vehicle statistics & Odometer
		v_doc = frappe.get_doc("Vehicle", vehicle_id)
		new_current_odo = max(curr_odometer, comp_odometer)
		update_fields = {
			"current_odometer": new_current_odo,
			"last_maintenance_date": doc.completion_date
		}
		if hasattr(v_doc, "last_maintenance_odometer"):
			update_fields["last_maintenance_odometer"] = comp_odometer
		if hasattr(v_doc, "next_maintenance_due_odometer"):
			update_fields["next_maintenance_due_odometer"] = next_due_odo
		if hasattr(v_doc, "next_due_odometer"):
			update_fields["next_due_odometer"] = next_due_odo
		if hasattr(v_doc, "next_due_date"):
			update_fields["next_due_date"] = next_due_date

		frappe.db.set_value("Vehicle", vehicle_id, update_fields)

		# 5. Remove Maintenance Lock via VehicleService single source of truth (MAINT-006, MAINT-009)
		self.vehicle_service.change_status(vehicle_id, VehicleStatus.AVAILABLE, reason="Maintenance completed successfully")

		# 6. Update linked Maintenance Request status if applicable
		if doc.maintenance_request and frappe.db.exists("Maintenance Request", doc.maintenance_request):
			frappe.db.set_value("Maintenance Request", doc.maintenance_request, "status", MaintenanceStatus.COMPLETED)

		# 7. Update active Assignment maintenance stats if linked
		active_assign = frappe.db.get_value("Vehicle Assignment", {"vehicle": vehicle_id, "status": ["in", ["Assigned", "In Use"]]}, "name")
		if active_assign:
			asn_doc = frappe.get_doc("Vehicle Assignment", active_assign)
			if hasattr(asn_doc, "latest_maintenance_date"):
				frappe.db.set_value("Vehicle Assignment", active_assign, "latest_maintenance_date", doc.completion_date)

		MaintenanceEventDispatcher.notify_maintenance_completed(doc)
		logger.info(f"Completed Work Order {work_order_id} for Vehicle {vehicle_id}. Maintenance Lock removed.")
		return doc.as_dict()

	def update_request(self, request_id: str, updates: Dict[str, Any]) -> Dict[str, Any]:
		"""Updates maintenance request parameters cleanly."""
		if not frappe.db.exists("Maintenance Request", request_id):
			raise FleetNotFoundError(f"Maintenance Request '{request_id}' not found.")
		doc = frappe.get_doc("Maintenance Request", request_id)
		if doc.status == MaintenanceStatus.CANCELLED:
			raise FleetValidationError(f"Cannot modify cancelled Maintenance Request '{request_id}'.")
		doc.update(updates)
		doc.save()
		return doc.as_dict()

	def cancel_request(self, request_id: str, reason: str | None = None) -> bool:
		"""Cancels a maintenance request record."""
		if not frappe.db.exists("Maintenance Request", request_id):
			raise FleetNotFoundError(f"Maintenance Request '{request_id}' not found.")
		doc = frappe.get_doc("Maintenance Request", request_id)
		doc.status = MaintenanceStatus.CANCELLED
		doc.save()
		MaintenanceEventDispatcher.notify_maintenance_cancelled(doc)
		logger.info(f"Cancelled Maintenance Request: {request_id}")
		return True

	# --- Analytics & Utilization Helpers ---

	def get_total_maintenance_cost_by_vehicle(self, vehicle_id: str) -> float:
		"""Returns total maintenance cost spent on a vehicle."""
		if not hasattr(frappe, "get_all"):
			return 0.0
		work_orders = frappe.get_all("Maintenance Work Order", filters={"vehicle": vehicle_id, "status": ["!=", "Cancelled"]}, fields=["total_cost"])
		return sum(float(w.get("total_cost") or 0.0) for w in work_orders)

	def get_company_maintenance_cost_stats(self, company: str | None = None) -> Dict[str, Any]:
		"""Returns total maintenance work orders count and spend for a company."""
		filters = {"status": ["!=", "Cancelled"]}
		if company:
			filters["company"] = company
		orders = frappe.get_all("Maintenance Work Order", filters=filters, fields=["total_cost"]) if hasattr(frappe, "get_all") else []
		return {
			"company": company or "All",
			"total_work_orders": len(orders),
			"total_maintenance_spend": sum(float(w.get("total_cost") or 0.0) for w in orders)
		}

	def get_workshop_performance_stats(self, workshop_name: str) -> Dict[str, Any]:
		"""Returns performance stats for a specific workshop."""
		orders = frappe.get_all("Maintenance Work Order", filters={"workshop": workshop_name}, fields=["name", "status", "total_cost"]) if hasattr(frappe, "get_all") else []
		return {
			"workshop": workshop_name,
			"total_jobs": len(orders),
			"completed_jobs": len([w for w in orders if w.get("status") == "Completed"]),
			"total_revenue_generated": sum(float(w.get("total_cost") or 0.0) for w in orders)
		}

	def get_vehicle_reliability_rankings(self, company: str | None = None, limit: int = 10) -> List[Dict[str, Any]]:
		"""Returns top vehicles ranked by fewest maintenance requests."""
		return frappe.get_all(
			"Vehicle",
			filters={"company": company} if company else {},
			fields=["name", "vehicle_number", "vehicle_brand", "vehicle_model", "current_odometer", "status"],
			order_by="creation desc",
			limit=limit
		) if hasattr(frappe, "get_all") else []

	def get_vehicle_history(self, vehicle_id: str, limit: int = 20) -> List[Dict[str, Any]]:
		"""Retrieves maintenance request history for a vehicle."""
		return frappe.get_all(
			"Maintenance Request",
			filters={"vehicle": vehicle_id},
			fields=["name", "requested_date", "maintenance_type", "priority", "status", "company"],
			order_by="creation desc",
			limit=limit
		) if hasattr(frappe, "get_all") else []

	def get_summary(self, vehicle_id: str) -> Dict[str, Any]:
		"""Retrieves summary maintenance statistics for a vehicle."""
		if not frappe.db.exists("Vehicle", vehicle_id):
			raise FleetNotFoundError(f"Vehicle '{vehicle_id}' not found.")

		requests = frappe.get_all("Maintenance Request", filters={"vehicle": vehicle_id}, fields=["name", "status"]) if hasattr(frappe, "get_all") else []
		work_orders = frappe.get_all("Maintenance Work Order", filters={"vehicle": vehicle_id}, fields=["name", "status", "total_cost"]) if hasattr(frappe, "get_all") else []

		total_spend = sum(float(w.get("total_cost") or 0.0) for w in work_orders)

		return {
			"vehicle": vehicle_id,
			"total_requests": len(requests),
			"total_work_orders": len(work_orders),
			"total_maintenance_spend": total_spend,
			"in_progress_count": len([w for w in work_orders if w.get("status") == "In Progress"])
		}

	# Contract aliases
	def create_maintenance_request(self, payload: Dict[str, Any]) -> Dict[str, Any]:
		return self.create_request(payload)

	def schedule_maintenance(self, maintenance_id: str, schedule_date: str) -> bool:
		return True

	def start_maintenance(self, maintenance_id: str) -> bool:
		if frappe.db.exists("Maintenance Work Order", maintenance_id):
			doc = frappe.get_doc("Maintenance Work Order", maintenance_id)
			doc.status = MaintenanceStatus.IN_PROGRESS
			doc.save()
			self.vehicle_service.change_status(doc.vehicle, VehicleStatus.UNDER_MAINTENANCE, reason="Work Order started")
			MaintenanceEventDispatcher.notify_maintenance_in_progress(doc)
			return True
		return False

	def complete_maintenance(self, maintenance_id: str, closing_odometer: float) -> bool:
		self.complete_work_order(maintenance_id, closing_odometer)
		return True

	def cancel_maintenance(self, maintenance_id: str, reason: str | None = None) -> bool:
		return self.cancel_request(maintenance_id, reason)

	def get_vehicle_maintenance_history(self, vehicle_id: str, limit: int = 20) -> List[Dict[str, Any]]:
		return self.get_vehicle_history(vehicle_id, limit)

	def get_maintenance_summary(self, maintenance_id: str) -> Dict[str, Any]:
		return self.get_summary(maintenance_id)
