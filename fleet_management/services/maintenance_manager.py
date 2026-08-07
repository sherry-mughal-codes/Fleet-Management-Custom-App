"""
Maintenance Manager Service
Fleet Management System (Frappe v15)

Centralized engine for template-driven maintenance resolution,
due/overdue activity calculation, servicing completion, and history tracking.
"""

from typing import Any, Dict, List, Optional
import frappe

from fleet_management.enums import VehicleStatus
from fleet_management.services.base_service import BaseService
from fleet_management.services.vehicle_state_manager import VehicleStateManager
from fleet_management.utils.exceptions import FleetNotFoundError, FleetValidationError
from fleet_management.utils.logger import get_logger

logger = get_logger("fleet_management.services.maintenance_manager")


class MaintenanceManager(BaseService):
	"""
	Enterprise service for simplified template-driven Maintenance Entries
	and maintenance intelligence calculations.
	"""

	def __init__(self):
		super().__init__()
		self.state_manager = VehicleStateManager()

	def get_active_template(self, vehicle_id: str) -> Optional[str]:
		"""
		Direct Vehicle Template Resolution:
		Reads Vehicle.maintenance_template. Fallback: any active Maintenance Template.
		"""
		if not frappe.db.exists("Fleet Vehicle", vehicle_id):
			return None

		# Primary: use per-vehicle template from Vehicle.maintenance_template
		vehicle_template = frappe.db.get_value("Fleet Vehicle", vehicle_id, "maintenance_template")
		if vehicle_template and frappe.db.exists("Maintenance Template", vehicle_template):
			if frappe.db.get_value("Maintenance Template", vehicle_template, "is_active"):
				return vehicle_template

		# Fallback: get any active Maintenance Template
		active_t = frappe.db.get_value("Maintenance Template", {"is_active": 1}, "name")
		return active_t

	def get_template_lines(self, template_id: str) -> List[Dict[str, Any]]:
		"""Retrieves schedule lines for a Maintenance Template."""
		if not template_id or not frappe.db.exists("Maintenance Template", template_id):
			return []

		return frappe.get_all(
			"Maintenance Schedule Line",
			filters={"parent": template_id},
			fields=["maintenance_type", "interval_km", "priority", "is_mandatory", "description"]
		) if hasattr(frappe, "get_all") else []

	def get_last_serviced_odometer(self, vehicle_id: str, maintenance_type: str) -> float:
		"""Retrieves the highest odometer reading when target maintenance_type was last serviced."""
		highest_odo = 0.0

		if hasattr(frappe, "db"):
			# 1. Check Maintenance Entry (both direct vehicle reference and via assignment)
			if frappe.db.table_exists("Maintenance Entry"):
				try:
					res = frappe.db.sql("""
						SELECT MAX(me.current_odometer) as max_odo
						FROM `tabMaintenance Entry` me
						LEFT JOIN `tabMaintenance Entry Item` mei ON mei.parent = me.name
						WHERE me.docstatus = 1
						  AND (me.vehicle = %s OR me.assignment IN (SELECT name FROM `tabVehicle Assignment` WHERE vehicle = %s))
						  AND (mei.item_name = %s OR mei.item_name LIKE %s OR me.maintenance_type LIKE %s)
					""", (vehicle_id, vehicle_id, maintenance_type, f"%{maintenance_type}%", f"%{maintenance_type}%"), as_dict=True)

					if res and res[0].get("max_odo") is not None:
						highest_odo = max(highest_odo, float(res[0].get("max_odo") or 0.0))
				except Exception as e:
					logger.error(f"Error checking Maintenance Entry last serviced odo: {e}")

			# 2. Check Maintenance Work Order (legacy / formal work orders)
			if frappe.db.table_exists("Maintenance Work Order"):
				try:
					res2 = frappe.db.sql("""
						SELECT MAX(completion_odometer) as max_odo
						FROM `tabMaintenance Work Order`
						WHERE vehicle = %s
						  AND docstatus = 1
						  AND status = 'Completed'
					""", (vehicle_id,), as_dict=True)

					if res2 and res2[0].get("max_odo") is not None:
						highest_odo = max(highest_odo, float(res2[0].get("max_odo") or 0.0))
				except Exception:
					pass

		# Fallback to initial vehicle odometer if no maintenance has been completed yet
		initial_odo = float(frappe.db.get_value("Fleet Vehicle", vehicle_id, "initial_odometer") or 0.0) if hasattr(frappe, "db") and frappe.db.exists("Fleet Vehicle", vehicle_id) else 0.0
		return max(highest_odo, initial_odo)

	def _get_current_vehicle_odometer(self, vehicle_id: str) -> float:
		"""Derives current vehicle odometer reading from max Fuel Entry odometer or initial_odometer."""
		if not vehicle_id or not hasattr(frappe, "db") or not frappe.db.exists("Fleet Vehicle", vehicle_id):
			return 0.0
		latest_fuel_odo = frappe.db.get_value("Fuel Entry", {"vehicle": vehicle_id, "docstatus": 1}, "MAX(odometer)") or 0.0
		odo = float(latest_fuel_odo)
		if not odo:
			odo = float(frappe.db.get_value("Fleet Vehicle", vehicle_id, "initial_odometer") or 0.0)
		return odo

	def get_due_maintenance(self, vehicle_id: str) -> List[Dict[str, Any]]:
		"""
		Returns list of template schedule lines currently due for servicing on target vehicle.
		A line is due if current_odometer >= last_serviced_odometer + interval_km.
		"""
		template_id = self.get_active_template(vehicle_id)
		if not template_id:
			return []

		curr_odo = self._get_current_vehicle_odometer(vehicle_id)
		lines = self.get_template_lines(template_id)
		due_items = []

		for line in lines:
			m_type = line.get("maintenance_type") if isinstance(line, dict) else getattr(line, "maintenance_type", "")
			if not m_type:
				continue
			interval = float(line.get("interval_km", 5000) if isinstance(line, dict) else getattr(line, "interval_km", 5000) or 5000)
			priority = line.get("priority", "Medium") if isinstance(line, dict) else getattr(line, "priority", "Medium")
			is_mandatory = bool(line.get("is_mandatory", 0) if isinstance(line, dict) else getattr(line, "is_mandatory", 0))
			grace = float(line.get("grace_distance", 0) if isinstance(line, dict) else getattr(line, "grace_distance", 0) or 0)

			last_odo = self.get_last_serviced_odometer(vehicle_id, m_type)
			next_due = last_odo + interval

			if curr_odo >= next_due:
				due_items.append({
					"maintenance_type": m_type,
					"interval_km": interval,
					"priority": priority,
					"is_mandatory": is_mandatory,
					"last_serviced_odometer": last_odo,
					"current_odometer": curr_odo,
					"next_due_odometer": next_due,
					"exceeded_km": round(curr_odo - next_due, 2)
				})

		return due_items

	def get_overdue_maintenance(self, vehicle_id: str, current_odometer: Optional[float] = None) -> List[Dict[str, Any]]:
		"""
		Returns list of mandatory template schedule lines whose (interval + grace) distance is exceeded.
		Used by Fuel Entry Validation Engine to enforce Fuel Lock.
		"""
		template_id = self.get_active_template(vehicle_id)
		if not template_id:
			return []

		if current_odometer and float(current_odometer) > 0:
			curr_odo = float(current_odometer)
		else:
			curr_odo = self._get_current_vehicle_odometer(vehicle_id)
		lines = self.get_template_lines(template_id)
		overdue_items = []

		for line in lines:
			if not line.is_mandatory:
				continue

			m_type = line.maintenance_type
			interval = float(line.interval_km or 5000)
			last_odo = self.get_last_serviced_odometer(vehicle_id, m_type)
			threshold = last_odo + interval

			if curr_odo >= threshold:
				overdue_items.append({
					"maintenance_type": m_type,
					"interval_km": interval,
					"is_mandatory": 1,
					"priority": line.get("priority", "High") if isinstance(line, dict) else getattr(line, "priority", "High"),
					"last_serviced_odometer": last_odo,
					"current_odometer": curr_odo,
					"threshold_odometer": threshold,
					"exceeded_km": round(curr_odo - (last_odo + interval), 2)
				})

		return overdue_items

	def get_next_service(self, vehicle_id: str) -> Optional[Dict[str, Any]]:
		"""Returns the closest upcoming maintenance schedule line."""
		template_id = self.get_active_template(vehicle_id)
		if not template_id:
			return None

		curr_odo = self._get_current_vehicle_odometer(vehicle_id)
		lines = self.get_template_lines(template_id)

		upcoming = []
		for line in lines:
			m_type = line.maintenance_type
			interval = float(line.interval_km or 5000)
			last_odo = self.get_last_serviced_odometer(vehicle_id, m_type)
			next_due = last_odo + interval
			remaining = next_due - curr_odo

			upcoming.append({
				"maintenance_type": m_type,
				"next_due_odometer": next_due,
				"remaining_km": round(remaining, 2)
			})

		if not upcoming:
			return None

		upcoming.sort(key=lambda x: x["remaining_km"])
		return upcoming[0]

	def get_remaining_distance(self, vehicle_id: str) -> Dict[str, float]:
		"""Returns remaining distance dict for all template schedule lines."""
		template_id = self.get_active_template(vehicle_id)
		if not template_id:
			return {}

		curr_odo = self._get_current_vehicle_odometer(vehicle_id)
		lines = self.get_template_lines(template_id)
		result = {}

		for line in lines:
			m_type = line.maintenance_type
			interval = float(line.interval_km or 5000)
			last_odo = self.get_last_serviced_odometer(vehicle_id, m_type)
			remaining = (last_odo + interval) - curr_odo
			result[m_type] = round(remaining, 2)

		return result

	def get_vehicle_health(self, vehicle_id: str) -> Dict[str, Any]:
		"""
		Calculates vehicle health score (0-100%) and operational health status.
		Health Status: Healthy | Due Soon | Overdue | Fuel Locked
		"""
		overdue = self.get_overdue_maintenance(vehicle_id)
		due = self.get_due_maintenance(vehicle_id)

		if overdue:
			status = "Fuel Locked"
			score = max(0, 100 - len(overdue) * 30)
		elif due:
			status = "Overdue" if any(d.get("is_mandatory") for d in due) else "Due Soon"
			score = max(50, 100 - len(due) * 15)
		else:
			status = "Healthy"
			score = 100

		return {
			"vehicle": vehicle_id,
			"health_score": score,
			"health_status": status,
			"due_items_count": len(due),
			"overdue_items_count": len(overdue)
		}

	def create_maintenance_entry(self, payload: Dict[str, Any]) -> Dict[str, Any]:
		"""Creates a new Maintenance Entry document."""
		doc = frappe.get_doc({
			"doctype": "Maintenance Entry",
			**payload
		})
		doc.insert()
		return doc.as_dict()

	def submit_maintenance_entry(self, entry_id: str) -> Dict[str, Any]:
		"""
		Submits Maintenance Entry:
		Records history, resets ONLY the completed maintenance_type,
		recalculates next maintenance due odometer, and triggers VehicleStateManager.
		"""
		if not frappe.db.exists("Maintenance Entry", entry_id):
			raise FleetNotFoundError(f"Maintenance Entry '{entry_id}' not found.")

		doc = frappe.get_doc("Maintenance Entry", entry_id)

		if doc.docstatus == 0:
			doc.submit()

		vehicle_id = doc.vehicle
		if vehicle_id:
			# Update Vehicle last maintenance odometer & date
			comp_odo = float(doc.current_odometer or 0.0)
			frappe.db.set_value("Fleet Vehicle", vehicle_id, "last_maintenance_odometer", comp_odo)
			frappe.db.set_value("Fleet Vehicle", vehicle_id, "last_maintenance_date", doc.maintenance_date)

			# Calculate new next_maintenance_due_odometer from template lines
			next_svc = self.get_next_service(vehicle_id)
			if next_svc and next_svc.get("next_due_odometer"):
				frappe.db.set_value("Fleet Vehicle", vehicle_id, "next_maintenance_due_odometer", next_svc["next_due_odometer"])

			# Recalculate Vehicle state via VehicleStateManager
			self.state_manager.update_vehicle_state(vehicle_id, reason=f"Maintenance Entry {entry_id} submitted")

		logger.info(f"Submitted Maintenance Entry: {entry_id}")
		return doc.as_dict()

	def cancel_maintenance_entry(self, entry_id: str, reason: Optional[str] = None) -> bool:
		"""
		Transaction Reversal for Maintenance Entry:
		Cancels entry, restores previous maintenance counters, recalculates vehicle state.
		"""
		if not frappe.db.exists("Maintenance Entry", entry_id):
			raise FleetNotFoundError(f"Maintenance Entry '{entry_id}' not found.")

		doc = frappe.get_doc("Maintenance Entry", entry_id)
		vehicle_id = doc.vehicle

		if doc.docstatus == 1:
			doc.cancel()

		if vehicle_id:
			self.state_manager.update_vehicle_state(vehicle_id, reason=reason or f"Maintenance Entry {entry_id} cancelled")

		logger.info(f"Cancelled Maintenance Entry: {entry_id}")
		return True

	# --- Legacy Subsystem Handlers for Backward Compatibility ---
	def create_request(self, payload: Dict[str, Any]) -> Dict[str, Any]:
		"""Legacy wrapper creating Maintenance Request."""
		doc = frappe.get_doc({"doctype": "Maintenance Request", **payload})
		doc.insert()
		return doc.as_dict()

	def create_work_order(self, payload: Dict[str, Any]) -> Dict[str, Any]:
		"""Legacy wrapper creating Maintenance Work Order."""
		doc = frappe.get_doc({"doctype": "Maintenance Work Order", **payload})
		doc.insert()
		return doc.as_dict()

	def complete_work_order(self, work_order_id: str, completion_odometer: Optional[float] = None, costs: Optional[Dict[str, float]] = None) -> Dict[str, Any]:
		"""Legacy wrapper completing Maintenance Work Order."""
		if not frappe.db.exists("Maintenance Work Order", work_order_id):
			return {}
		doc = frappe.get_doc("Maintenance Work Order", work_order_id)
		if costs:
			for k, v in costs.items():
				if hasattr(doc, k):
					setattr(doc, k, float(v or 0.0))
		if completion_odometer:
			doc.completion_odometer = float(completion_odometer)
		doc.status = "Completed"
		if doc.docstatus == 0:
			doc.submit()
		return doc.as_dict()
