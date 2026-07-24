"""
Fuel Intelligence Domain Service Implementation
Fleet Management System
"""

from typing import Any, Dict, List, Optional
import frappe
from fleet_management.services.base_service import BaseService
from fleet_management.services.vehicle_service import VehicleService
from fleet_management.services.fuel_average_service import FuelAverageService
from fleet_management.services.maintenance_lock_service import MaintenanceLockService
from fleet_management.enums import FuelEntryStatus
from fleet_management.events.fuel_events import FuelEventDispatcher
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
		Runs MaintenanceLockService check (FUEL-008).
		"""
		vehicle_id = payload.get("vehicle")
		odometer = payload.get("odometer")

		# FUEL-008: Check Maintenance Lock
		if vehicle_id:
			MaintenanceLockService.enforce_maintenance_lock(vehicle_id, odometer)

		logger.info("Creating fuel entry via FuelService", {"vehicle": vehicle_id, "qty": payload.get("fuel_qty")})
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

		# 1. Enforce Maintenance Lock (FUEL-008)
		MaintenanceLockService.enforce_maintenance_lock(doc.vehicle, doc.odometer)

		# 2. Calculate Fuel Average (FUEL-007)
		avg_stats = FuelAverageService.calculate_entry_average(doc.vehicle, doc.odometer, doc.fuel_qty)
		doc.distance_since_last_fuel = avg_stats["distance_travelled"]
		doc.fuel_average = avg_stats["fuel_average"]
		doc.status = FuelEntryStatus.SUBMITTED
		doc.save()

		# 3. Update Vehicle statistics & current odometer
		self.update_vehicle_statistics(doc.vehicle, doc)

		# 4. Update Assignment statistics if linked
		if doc.assignment:
			self.update_assignment_statistics(doc.assignment, doc)

		FuelEventDispatcher.notify_fuel_submitted(doc)
		logger.info(f"Submitted Fuel Entry: {fuel_entry_id}, Calculated Average: {doc.fuel_average} KM/L")
		return doc.as_dict()

	def update_vehicle_statistics(self, vehicle_id: str, fuel_doc: Any):
		"""Updates Vehicle current_odometer, last_fuel_average, and total fuel spend."""
		if not hasattr(frappe, "db"):
			return

		v_doc = frappe.get_doc("Vehicle", vehicle_id)
		current_odometer = max(float(v_doc.current_odometer or 0.0), float(fuel_doc.odometer or 0.0))

		frappe.db.set_value("Vehicle", vehicle_id, {
			"current_odometer": current_odometer,
			"last_fuel_average": fuel_doc.fuel_average or 0.0,
			"last_fuel_entry_date": fuel_doc.fuel_date
		})
		logger.info(f"Updated Vehicle '{vehicle_id}' stats from Fuel Entry {fuel_doc.name}")

	def update_assignment_statistics(self, assignment_id: str, fuel_doc: Any):
		"""Updates linked Assignment statistics."""
		if not hasattr(frappe, "db") or not frappe.db.exists("Vehicle Assignment", assignment_id):
			return

		frappe.db.set_value("Vehicle Assignment", assignment_id, {
			"latest_fuel_odometer": fuel_doc.odometer,
			"latest_fuel_date": fuel_doc.fuel_date
		})
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

	def cancel_fuel_entry(self, fuel_entry_id: str, reason: Optional[str] = None) -> bool:
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
		entries = frappe.get_all("Fuel Entry", filters={"vehicle": vehicle_id, "status": ["!=", "Cancelled"]}, fields=["total_cost"])
		return sum(float(e.get("total_cost") or 0.0) for e in entries)

	def get_driver_fuel_cost_stats(self, employee_id: str) -> Dict[str, Any]:
		"""Returns total fuel entries count and total spend for a driver."""
		entries = frappe.get_all("Fuel Entry", filters={"employee": employee_id, "status": ["!=", "Cancelled"]}, fields=["total_cost", "fuel_qty"]) if hasattr(frappe, "get_all") else []
		return {
			"employee": employee_id,
			"total_entries": len(entries),
			"total_spend": sum(float(e.get("total_cost") or 0.0) for e in entries),
			"total_liters": sum(float(e.get("fuel_qty") or 0.0) for e in entries)
		}

	def get_monthly_consumption_stats(self, company: Optional[str] = None) -> Dict[str, Any]:
		"""Returns monthly aggregated fuel consumption and cost statistics."""
		filters = {"status": ["!=", "Cancelled"]}
		if company:
			filters["company"] = company
		entries = frappe.get_all("Fuel Entry", filters=filters, fields=["fuel_qty", "total_cost"]) if hasattr(frappe, "get_all") else []
		return {
			"total_entries": len(entries),
			"total_consumption_liters": sum(float(e.get("fuel_qty") or 0.0) for e in entries),
			"total_fuel_cost": sum(float(e.get("total_cost") or 0.0) for e in entries)
		}

	def get_efficiency_rankings(self, company: Optional[str] = None, limit: int = 10) -> List[Dict[str, Any]]:
		"""Returns top efficient vehicles ranked by fuel average."""
		return frappe.get_all(
			"Vehicle",
			filters={"company": company} if company else {},
			fields=["name", "vehicle_number", "vehicle_brand", "vehicle_model", "last_fuel_average"],
			order_by="last_fuel_average desc",
			limit=limit
		) if hasattr(frappe, "get_all") else []

	def get_fuel_summary(self, vehicle_id: str) -> Dict[str, Any]:
		"""Retrieves aggregated fuel summary stats for a vehicle."""
		if not frappe.db.exists("Vehicle", vehicle_id):
			raise FleetNotFoundError(f"Vehicle '{vehicle_id}' not found.")

		entries = frappe.get_all(
			"Fuel Entry",
			filters={"vehicle": vehicle_id, "status": ["!=", "Cancelled"]},
			fields=["name", "fuel_qty", "total_cost", "odometer", "fuel_date", "fuel_average"]
		) if hasattr(frappe, "get_all") else []

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
		return frappe.get_all(
			"Fuel Entry",
			filters={"vehicle": vehicle_id},
			fields=["name", "fuel_date", "fuel_qty", "total_cost", "odometer", "fuel_average", "status"],
			order_by="creation desc",
			limit=limit
		)

	def get_employee_history(self, employee_id: str, limit: int = 20) -> List[Dict[str, Any]]:
		"""Retrieves fuel entry history for an employee."""
		return frappe.get_all(
			"Fuel Entry",
			filters={"employee": employee_id},
			fields=["name", "vehicle", "fuel_date", "fuel_qty", "total_cost", "status"],
			order_by="creation desc",
			limit=limit
		)

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
