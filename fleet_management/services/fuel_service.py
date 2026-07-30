"""
Fuel Intelligence Domain Service Implementation
Fleet Management System
"""

from typing import Any, Dict, List

import frappe

from fleet_management.enums import FuelEntryStatus
from fleet_management.events.fuel_events import FuelEventDispatcher
from fleet_management.services.base_service import BaseService
from fleet_management.services.fuel_average_service import FuelAverageService
from fleet_management.services.maintenance_lock_service import MaintenanceLockService
from fleet_management.services.vehicle_service import VehicleService
from fleet_management.utils.exceptions import FleetNotFoundError, FleetValidationError
from fleet_management.utils.logger import get_logger

logger = get_logger("fleet_management.services.fuel")


class FuelService(BaseService):
	"""
	Enterprise service managing business operations for Fuel Entry records.
	Executes Fuel Average Engine, Maintenance Lock Engine, and Vehicle / Assignment updates.
	"""

	def __init__(self):
		super().__init__()
		self.vehicle_service = VehicleService()

	def create_fuel_entry(self, payload: Dict[str, Any]) -> Dict[str, Any]:
		"""
		Creates a new Fuel Entry using minimal Category A fields.
		Runs MaintenanceLockService check (FUEL-008) if vehicle can be resolved.
		"""
		# Resolve vehicle from assignment if available (for maintenance lock check)
		vehicle_id = None
		assignment_id = payload.get("assignment")
		if assignment_id and hasattr(frappe, "db") and frappe.db:
			vehicle_id = frappe.db.get_value("Vehicle Assignment", assignment_id, "vehicle")
		if not vehicle_id:
			vehicle_id = payload.get("vehicle")

		# FUEL-008: Check Maintenance Lock
		if vehicle_id:
			MaintenanceLockService.enforce_maintenance_lock(vehicle_id, payload.get("odometer"))

		logger.info("Creating fuel entry via FuelService", {"assignment": assignment_id, "qty": payload.get("fuel_qty")})
		doc = frappe.get_doc({
			"doctype": "Fuel Entry",
			**payload
		})
		doc.insert()
		FuelEventDispatcher.notify_fuel_created(doc)
		return doc.as_dict()

	def submit_fuel_entry(self, fuel_entry_id: str) -> Dict[str, Any]:
		"""
		Submits a fuel entry, calculates fuel average, updates Vehicle & Assignment statistics.
		"""
		if not frappe.db.exists("Fuel Entry", fuel_entry_id):
			raise FleetNotFoundError(f"Fuel Entry '{fuel_entry_id}' not found.")

		doc = frappe.get_doc("Fuel Entry", fuel_entry_id)
		if doc.docstatus == 0:
			doc.submit()

		FuelEventDispatcher.notify_fuel_submitted(doc)
		logger.info(f"Submitted Fuel Entry: {fuel_entry_id}")
		return doc.as_dict()

	def update_vehicle_statistics(self, vehicle_id: str, fuel_doc: Any):
		"""Updates Vehicle fuel stats (average, last date) from submitted Fuel Entry."""
		if not hasattr(frappe, "db"):
			return

		v_doc = frappe.get_doc("Vehicle", vehicle_id)

		update_fields = {}
		if hasattr(v_doc, "average_fuel_economy"):
			update_fields["average_fuel_economy"] = fuel_doc.fuel_average or 0.0
		if hasattr(v_doc, "last_fuel_average"):
			update_fields["last_fuel_average"] = fuel_doc.fuel_average or 0.0
		if hasattr(v_doc, "last_fuel_date"):
			update_fields["last_fuel_date"] = fuel_doc.fuel_date
		if hasattr(v_doc, "last_fuel_entry_date"):
			update_fields["last_fuel_entry_date"] = fuel_doc.fuel_date

		if update_fields:
			frappe.db.set_value("Vehicle", vehicle_id, update_fields)
		logger.info(f"Updated Vehicle '{vehicle_id}' stats from Fuel Entry {fuel_doc.name}")

	def update_assignment_statistics(self, assignment_id: str, fuel_doc: Any):
		"""Updates linked Assignment statistics."""
		if not hasattr(frappe, "db") or not frappe.db.exists("Vehicle Assignment", assignment_id):
			return

		asn_doc = frappe.get_doc("Vehicle Assignment", assignment_id)
		update_fields = {}
		if hasattr(asn_doc, "latest_fuel_odometer"):
			update_fields["latest_fuel_odometer"] = fuel_doc.odometer
		if hasattr(asn_doc, "latest_fuel_date"):
			update_fields["latest_fuel_date"] = fuel_doc.fuel_date

		if update_fields:
			frappe.db.set_value("Vehicle Assignment", assignment_id, update_fields)
		logger.info(f"Updated Assignment '{assignment_id}' stats from Fuel Entry {fuel_doc.name}")

	def update_fuel_entry(self, fuel_entry_id: str, updates: Dict[str, Any]) -> Dict[str, Any]:
		"""Updates fuel entry parameters cleanly."""
		if not frappe.db.exists("Fuel Entry", fuel_entry_id):
			raise FleetNotFoundError(f"Fuel Entry '{fuel_entry_id}' not found.")
		doc = frappe.get_doc("Fuel Entry", fuel_entry_id)
		if doc.status == FuelEntryStatus.CANCELLED:
			raise FleetValidationError(f"Cannot modify cancelled Fuel Entry '{fuel_entry_id}'.")
		doc.update(updates)
		doc.save()
		return doc.as_dict()

	def cancel_fuel_entry(self, fuel_entry_id: str, reason: str | None = None) -> bool:
		"""Cancels a fuel entry record."""
		if not frappe.db.exists("Fuel Entry", fuel_entry_id):
			raise FleetNotFoundError(f"Fuel Entry '{fuel_entry_id}' not found.")
		doc = frappe.get_doc("Fuel Entry", fuel_entry_id)
		doc.status = FuelEntryStatus.CANCELLED
		doc.save()
		FuelEventDispatcher.notify_fuel_cancelled(doc)
		logger.info(f"Cancelled Fuel Entry: {fuel_entry_id}")
		return True

	# --- Analytics & Utilization Helpers ---

	def get_total_fuel_cost_by_vehicle(self, vehicle_id: str) -> float:
		"""Returns total fuel cost spent on a vehicle."""
		if not hasattr(frappe, "get_all"):
			return 0.0
		asn_names = [a.name for a in frappe.get_all("Vehicle Assignment", filters={"vehicle": vehicle_id}, fields=["name"])]
		if not asn_names:
			return 0.0
		entries = frappe.get_all("Fuel Entry", filters={"assignment": ["in", asn_names], "docstatus": ["!=", 2]}, fields=["total_cost"])
		return sum(float(e.get("total_cost") or 0.0) for e in entries)

	def get_driver_fuel_cost_stats(self, employee_id: str) -> Dict[str, Any]:
		"""Returns total fuel entries count and total spend for a driver."""
		asn_names = [a.name for a in frappe.get_all("Vehicle Assignment", filters={"employee": employee_id}, fields=["name"])]
		entries = frappe.get_all("Fuel Entry", filters={"assignment": ["in", asn_names], "docstatus": ["!=", 2]}, fields=["total_cost", "fuel_qty"]) if (asn_names and hasattr(frappe, "get_all")) else []
		return {
			"employee": employee_id,
			"total_entries": len(entries),
			"total_spend": sum(float(e.get("total_cost") or 0.0) for e in entries),
			"total_liters": sum(float(e.get("fuel_qty") or 0.0) for e in entries)
		}

	def get_monthly_consumption_stats(self, company: str | None = None) -> Dict[str, Any]:
		"""Returns monthly aggregated fuel consumption and cost statistics."""
		filters = {"docstatus": ["!=", 2]}
		entries = frappe.get_all("Fuel Entry", filters=filters, fields=["fuel_qty", "total_cost"]) if hasattr(frappe, "get_all") else []
		return {
			"total_entries": len(entries),
			"total_consumption_liters": sum(float(e.get("fuel_qty") or 0.0) for e in entries),
			"total_fuel_cost": sum(float(e.get("total_cost") or 0.0) for e in entries)
		}

	def get_efficiency_rankings(self, company: str | None = None, limit: int = 10) -> List[Dict[str, Any]]:
		"""Returns top efficient vehicles ranked by fuel average."""
		return frappe.get_all(
			"Vehicle",
			filters={"company": company} if company else {},
			fields=["name", "vehicle_number", "vehicle_brand", "vehicle_model", "average_fuel_economy"],
			order_by="average_fuel_economy desc",
			limit=limit
		) if hasattr(frappe, "get_all") else []

	def get_fuel_summary(self, vehicle_id: str) -> Dict[str, Any]:
		"""Retrieves aggregated fuel summary stats for a vehicle."""
		if not frappe.db.exists("Vehicle", vehicle_id):
			raise FleetNotFoundError(f"Vehicle '{vehicle_id}' not found.")

		asn_names = [a.name for a in frappe.get_all("Vehicle Assignment", filters={"vehicle": vehicle_id}, fields=["name"])]
		entries = frappe.get_all(
			"Fuel Entry",
			filters={"assignment": ["in", asn_names], "docstatus": ["!=", 2]},
			fields=["name", "fuel_qty", "total_cost", "odometer", "fuel_date"]
		) if (asn_names and hasattr(frappe, "get_all")) else []

		total_liters = sum(float(e.get("fuel_qty") or 0.0) for e in entries)
		total_cost = sum(float(e.get("total_cost") or 0.0) for e in entries)
		lifetime_avg = FuelAverageService.get_lifetime_vehicle_average(vehicle_id)

		return {
			"vehicle": vehicle_id,
			"total_fuel_entries": len(entries),
			"total_liters": total_liters,
			"total_cost": total_cost,
			"lifetime_fuel_average": lifetime_avg
		}

	def get_vehicle_history(self, vehicle_id: str, limit: int = 20) -> List[Dict[str, Any]]:
		"""Retrieves fuel entry history for a vehicle."""
		asn_names = [a.name for a in frappe.get_all("Vehicle Assignment", filters={"vehicle": vehicle_id}, fields=["name"])]
		if not asn_names:
			return []
		return frappe.get_all(
			"Fuel Entry",
			filters={"assignment": ["in", asn_names]},
			fields=["name", "fuel_date", "fuel_qty", "total_cost", "odometer", "docstatus"],
			order_by="creation desc",
			limit=limit
		) if hasattr(frappe, "get_all") else []

	def get_employee_history(self, employee_id: str, limit: int = 20) -> List[Dict[str, Any]]:
		"""Retrieves fuel entry history for an employee via assignment join."""
		if not hasattr(frappe, "db") or not frappe.db:
			return []
		try:
			return frappe.db.sql("""
				SELECT fe.name, fe.assignment, fe.fuel_date, fe.fuel_qty, fe.total_cost, fe.fuel_average, fe.docstatus
				FROM `tabFuel Entry` fe
				INNER JOIN `tabVehicle Assignment` va ON va.name = fe.assignment
				WHERE va.employee = %s
				ORDER BY fe.fuel_date DESC, fe.creation DESC
				LIMIT %s
			""", (employee_id, limit), as_dict=True)
		except Exception as e:
			logger.warning(f"get_employee_history failed for {employee_id}: {e}")
			return []

	def validate_entry(self, payload: Dict[str, Any]) -> bool:
		return True

	def calculate_average(self, vehicle_id: str, odometer_reading: float, fuel_qty: float) -> float:
		stats = FuelAverageService.calculate_entry_average(vehicle_id, odometer_reading, fuel_qty)
		return stats["fuel_average"]

	def validate_maintenance_lock(self, vehicle_id: str) -> bool:
		return MaintenanceLockService.is_maintenance_locked(vehicle_id)

	def validate_odometer(self, vehicle_id: str, odometer_reading: float) -> bool:
		if hasattr(frappe, "db"):
			v_odometer = frappe.db.get_value("Vehicle", vehicle_id, "current_odometer") or 0.0
			return float(odometer_reading) >= float(v_odometer)
		return True
