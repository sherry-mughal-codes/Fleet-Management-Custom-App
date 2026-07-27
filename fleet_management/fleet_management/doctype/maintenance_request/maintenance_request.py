"""
Maintenance Request Main Document Controller
Fleet Management System
"""

import frappe

from fleet_management.services.maintenance_due_service import MaintenanceDueEngine
from fleet_management.utils.base_document import BaseFleetDocument
from fleet_management.utils.helpers import get_doc_or_none
from fleet_management.validators.maintenance_validator import MaintenanceValidator


class MaintenanceRequest(BaseFleetDocument):
	"""
	Maintenance Request Controller.
	Enforces Rule IDs MAINT-001 through MAINT-010 and auto-population cascades.
	"""
	doctype = "Maintenance Request"


	def before_validate_hook(self):
		if not self.status:
			self.status = "Draft"
		if not self.naming_series:
			self.naming_series = "MREQ-.YYYY.-.#####"

		# 1. Structural validation via MaintenanceValidator (MAINT-001..MAINT-010)


		MaintenanceValidator(self.as_dict()).raise_if_invalid()

		# 2. Default requested_date to today if empty
		if not self.requested_date and hasattr(frappe, "utils"):
			self.requested_date = frappe.utils.nowdate()

		# 3. Auto-fetch Vehicle details if blank
		if self.vehicle:
			v_doc = get_doc_or_none("Vehicle", self.vehicle)
			if v_doc:
				if not self.vehicle_number:
					self.vehicle_number = v_doc.vehicle_number
				if not self.vehicle_name:
					self.vehicle_name = v_doc.vehicle_name
				if not self.vehicle_brand:
					self.vehicle_brand = v_doc.vehicle_brand
				if not self.vehicle_model:
					self.vehicle_model = v_doc.vehicle_model
				if not self.current_odometer:
					self.current_odometer = v_doc.current_odometer
				if not self.current_vehicle_status:
					self.current_vehicle_status = v_doc.status
				if not self.company:
					self.company = v_doc.company
				if not self.last_maintenance_date:
					self.last_maintenance_date = v_doc.last_maintenance_date
				if not self.last_maintenance_odometer and hasattr(v_doc, "last_maintenance_odometer"):
					self.last_maintenance_odometer = v_doc.last_maintenance_odometer

				# Auto-detect active Vehicle Assignment if blank
				if not self.current_assignment and hasattr(frappe, "db"):
					active_assign = frappe.db.get_value(
						"Vehicle Assignment",
						filters={"vehicle": self.vehicle, "status": ["in", ["Assigned", "In Use"]]},
						fieldname=["name", "employee_name"],
						as_dict=True
					)
					if active_assign:
						self.current_assignment = active_assign.name
						self.assigned_employee = active_assign.employee_name

				# Calculate next due thresholds via MaintenanceDueEngine
				if not self.next_due_odometer:
					self.next_due_odometer = MaintenanceDueEngine.calculate_next_due_odometer(self.vehicle)
				if not self.next_due_date:
					self.next_due_date = MaintenanceDueEngine.calculate_next_due_date(self.vehicle)

	def on_update(self):
		if self.vehicle:
			from fleet_management.services.vehicle_service import sync_vehicle_operational_summary
			sync_vehicle_operational_summary(self.vehicle)

	def on_trash(self):
		if self.vehicle:
			from fleet_management.services.vehicle_service import sync_vehicle_operational_summary
			sync_vehicle_operational_summary(self.vehicle)
