"""
Maintenance Template DocType Controller
Fleet Management System (Frappe v15)
"""

import frappe
from fleet_management.utils.base_document import BaseFleetDocument
from fleet_management.utils.exceptions import FleetValidationError


class MaintenanceTemplate(BaseFleetDocument):
	"""
	Maintenance Template Master Controller.
	Defines maintenance schedules mapped to specific Vehicles.
	"""

	doctype = "Maintenance Template"

	def validate(self):
		"""Validation preventing a vehicle from being assigned to multiple templates."""
		super().validate()
		if not hasattr(frappe, "db") or not frappe.db:
			return

		template_name = self.name
		for row in getattr(self, "vehicles", []) or []:
			v_id = getattr(row, "vehicle", None) or (row.get("vehicle") if isinstance(row, dict) else None)
			if v_id and frappe.db.exists("Vehicle", v_id):
				curr_temp = frappe.db.get_value("Vehicle", v_id, "maintenance_template")
				if curr_temp and curr_temp != template_name:
					raise FleetValidationError(
						f"Vehicle '{v_id}' is already assigned to Maintenance Template '{curr_temp}'. A vehicle can only belong to one Maintenance Template."
					)

	def on_update(self):
		"""
		Auto-syncs 2-way relationship:
		Updates Vehicle.maintenance_template for all vehicles listed in the optional 'vehicles' child table.
		Unlinks vehicles that were removed from this template's child table.
		"""
		if not hasattr(frappe, "db") or not frappe.db:
			return

		template_name = self.name
		target_vehicles = set()
		for row in getattr(self, "vehicles", []) or []:
			v_id = getattr(row, "vehicle", None) or (row.get("vehicle") if isinstance(row, dict) else None)
			if v_id:
				target_vehicles.add(v_id)

		# 1. Update Vehicle.maintenance_template for newly linked vehicles & clear cache
		for v_id in target_vehicles:
			if frappe.db.exists("Vehicle", v_id):
				curr_temp = frappe.db.get_value("Vehicle", v_id, "maintenance_template")
				if curr_temp != template_name:
					frappe.db.set_value("Vehicle", v_id, "maintenance_template", template_name)
					frappe.clear_document_cache("Vehicle", v_id)

		# 2. Unlink vehicles that previously pointed to this template but were removed from child table
		linked_vehicles = frappe.get_all("Vehicle", filters={"maintenance_template": template_name}, fields=["name"]) if hasattr(frappe, "get_all") else []
		for v in linked_vehicles:
			v_name = v.name if hasattr(v, "name") else v.get("name")
			if v_name and v_name not in target_vehicles:
				frappe.db.set_value("Vehicle", v_name, "maintenance_template", None)
				frappe.clear_document_cache("Vehicle", v_name)

		frappe.db.commit()

	def on_trash(self):
		"""Unlinks all vehicles pointing to this template upon template deletion."""
		if hasattr(frappe, "db") and frappe.db:
			linked = frappe.get_all("Vehicle", filters={"maintenance_template": self.name}, fields=["name"]) if hasattr(frappe, "get_all") else []
			frappe.db.set_value("Vehicle", {"maintenance_template": self.name}, "maintenance_template", None)
			for v in linked:
				v_name = v.name if hasattr(v, "name") else v.get("name")
				if v_name:
					frappe.clear_document_cache("Vehicle", v_name)
			frappe.db.commit()
