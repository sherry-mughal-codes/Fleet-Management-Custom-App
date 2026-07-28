"""
Fuel Manager Service
Fleet Management System (Frappe v15)

Manages Fuel Entry transactions, fuel efficiency engine integration,
maintenance lock enforcement, and transaction reversal on cancellation.
"""

from typing import Any, Dict, List, Optional
import frappe

from fleet_management.services.base_service import BaseService
from fleet_management.services.fuel_average_service import FuelAverageService
from fleet_management.services.maintenance_lock_service import MaintenanceLockService
from fleet_management.services.vehicle_state_manager import VehicleStateManager
from fleet_management.utils.exceptions import FleetNotFoundError, FleetValidationError
from fleet_management.utils.logger import get_logger

logger = get_logger("fleet_management.services.fuel_manager")


class FuelManager(BaseService):
	"""
	Enterprise manager for Fuel Entry transactions.
	"""

	def __init__(self):
		super().__init__()
		self.state_manager = VehicleStateManager()

	def create_fuel_entry(self, payload: Dict[str, Any]) -> Dict[str, Any]:
		"""Creates a new Fuel Entry document."""
		vehicle_id = payload.get("vehicle")
		odometer = payload.get("odometer")

		# Enforce Maintenance Lock
		if vehicle_id:
			MaintenanceLockService.enforce_maintenance_lock(vehicle_id, odometer)

		doc = frappe.get_doc({
			"doctype": "Fuel Entry",
			**payload
		})
		doc.insert()
		return doc.as_dict()

	def submit_fuel_entry(self, fuel_entry_id: str) -> Dict[str, Any]:
		"""Submits a Fuel Entry and triggers vehicle metrics update."""
		if not frappe.db.exists("Fuel Entry", fuel_entry_id):
			raise FleetNotFoundError(f"Fuel Entry '{fuel_entry_id}' not found.")

		doc = frappe.get_doc("Fuel Entry", fuel_entry_id)

		# Resolve vehicle via assignment (not a stored column)
		vehicle_id = doc.vehicle
		if vehicle_id:
			# Check maintenance lock
			MaintenanceLockService.enforce_maintenance_lock(vehicle_id, doc.odometer)

		if doc.docstatus == 0:
			doc.submit()

		# Trigger Vehicle summary sync and state recalculation
		if vehicle_id:
			from fleet_management.services.vehicle_service import sync_vehicle_operational_summary
			sync_vehicle_operational_summary(vehicle_id)
			self.state_manager.update_vehicle_state(vehicle_id, reason=f"Fuel Entry {fuel_entry_id} submitted")

		return doc.as_dict()

	def cancel_fuel_entry(self, fuel_entry_id: str, reason: Optional[str] = None) -> bool:
		"""
		Transaction Reversal for Fuel Entry:
		Cancels Fuel Entry, reverses fuel totals, recalculates mileage and vehicle statistics.
		"""
		if not frappe.db.exists("Fuel Entry", fuel_entry_id):
			raise FleetNotFoundError(f"Fuel Entry '{fuel_entry_id}' not found.")

		doc = frappe.get_doc("Fuel Entry", fuel_entry_id)
		vehicle_id = doc.vehicle  # resolve via @property before cancel

		if doc.docstatus == 1:
			doc.cancel()
		elif doc.docstatus == 0:
			frappe.delete_doc("Fuel Entry", fuel_entry_id)

		if vehicle_id:
			from fleet_management.services.vehicle_service import sync_vehicle_operational_summary
			sync_vehicle_operational_summary(vehicle_id)
			self.state_manager.update_vehicle_state(vehicle_id, reason=reason or f"Fuel Entry {fuel_entry_id} cancelled")

		logger.info(f"Cancelled Fuel Entry: {fuel_entry_id}")
		return True

	def get_fuel_summary(self, vehicle_id: str) -> Dict[str, Any]:
		"""Retrieves aggregated fuel statistics for target vehicle via assignment join."""
		if not hasattr(frappe, "db") or not frappe.db:
			return {"vehicle": vehicle_id, "total_entries": 0, "total_liters": 0.0, "total_spend": 0.0, "latest_fuel_average": 0.0}
		try:
			entries = frappe.db.sql("""
				SELECT fe.fuel_qty, fe.total_cost, fe.odometer, fe.fuel_average
				FROM `tabFuel Entry` fe
				INNER JOIN `tabVehicle Assignment` va ON va.name = fe.assignment
				WHERE va.vehicle = %s AND fe.docstatus = 1
			""", (vehicle_id,), as_dict=True)
		except Exception:
			entries = []

		total_liters = sum(float(e.get("fuel_qty") or 0.0) for e in entries)
		total_spend = sum(float(e.get("total_cost") or 0.0) for e in entries)
		averages = [float(e.get("fuel_average")) for e in entries if e.get("fuel_average") and float(e.get("fuel_average")) > 0]
		latest_avg = averages[0] if averages else 0.0

		return {
			"vehicle": vehicle_id,
			"total_entries": len(entries),
			"total_liters": round(total_liters, 2),
			"total_spend": round(total_spend, 2),
			"latest_fuel_average": round(latest_avg, 2)
		}
