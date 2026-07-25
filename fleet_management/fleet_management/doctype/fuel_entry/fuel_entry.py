"""
Fuel Entry Main Document Controller
Fleet Management System
"""

import frappe

from fleet_management.services.fuel_average_service import FuelAverageService
from fleet_management.services.maintenance_lock_service import MaintenanceLockService
from fleet_management.utils.base_document import BaseFleetDocument
from fleet_management.utils.helpers import get_doc_or_none
from fleet_management.validators.fuel_validator import FuelValidator


class FuelEntry(BaseFleetDocument):
	"""
	Fuel Entry Controller.
	Enforces Rule IDs FUEL-001 through FUEL-010, Fuel Average Engine, and Maintenance Lock Engine.
	"""
	doctype = "Fuel Entry"


	def before_validate_hook(self):
		if not self.status:
			self.status = "Draft"
		if not self.naming_series:
			self.naming_series = "FUEL-.YYYY.-.#####"

		# 1. Structural validation via FuelValidator (FUEL-001..FUEL-010)

		FuelValidator(self.as_dict()).raise_if_invalid()

		# 2. Default fuel date to today if empty
		if not self.fuel_date and hasattr(frappe, "utils"):
			self.fuel_date = frappe.utils.nowdate()

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
				if not self.fuel_type:
					self.fuel_type = v_doc.fuel_type
				if not self.current_vehicle_status:
					self.current_vehicle_status = v_doc.status
				if not self.current_vehicle_odometer:
					self.current_vehicle_odometer = v_doc.current_odometer
				if not self.company:
					self.company = v_doc.company

				# Default Odometer Reading from Vehicle current odometer
				if (not self.odometer or self.odometer == 0) and v_doc.current_odometer:
					self.odometer = float(v_doc.current_odometer)

				# Auto-detect active Vehicle Assignment if blank
				if not self.assignment and hasattr(frappe, "db"):
					active_assign = frappe.db.get_value(
						"Vehicle Assignment",
						filters={"vehicle": self.vehicle, "status": ["in", ["Assigned", "In Use"]]},
						fieldname=["name", "employee", "employee_name", "department", "opening_odometer", "status"],
						as_dict=True
					)
					if active_assign:
						self.assignment = active_assign.name
						self.assignment_id = active_assign.name
						self.employee = active_assign.employee
						self.assigned_employee = active_assign.employee_name
						self.department = active_assign.department
						self.assignment_status = active_assign.status
						self.opening_odometer = active_assign.opening_odometer

		# 4. Auto-fetch Assignment details if assignment is specified directly
		if self.assignment and not self.assigned_employee:
			a_doc = get_doc_or_none("Vehicle Assignment", self.assignment)
			if a_doc:
				self.assignment_id = a_doc.name
				self.employee = a_doc.employee
				self.assigned_employee = a_doc.employee_name
				self.department = a_doc.department
				self.assignment_status = a_doc.status
				self.opening_odometer = a_doc.opening_odometer

		# 5. Enforce Maintenance Lock (FUEL-008)
		if self.vehicle:
			MaintenanceLockService.enforce_maintenance_lock(self.vehicle, self.odometer)

		# 6. Calculate Fuel Average (FUEL-007)
		if self.vehicle and self.odometer and self.fuel_qty:
			avg_stats = FuelAverageService.calculate_entry_average(self.vehicle, self.odometer, self.fuel_qty)
			self.distance_since_last_fuel = avg_stats["distance_travelled"]
			self.fuel_average = avg_stats["fuel_average"]
