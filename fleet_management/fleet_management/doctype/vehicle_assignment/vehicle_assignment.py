"""
Vehicle Assignment Main Document Controller
Fleet Management System
"""

import datetime
import frappe
from fleet_management.utils.base_document import BaseFleetDocument
from fleet_management.validators.assignment_validator import AssignmentValidator
from fleet_management.enums import AssignmentStatus
from fleet_management.utils.exceptions import FleetValidationError
from fleet_management.utils.helpers import get_doc_or_none
from fleet_management.validators.common_validators import validate_date_range


class VehicleAssignment(BaseFleetDocument):
	"""
	Vehicle Assignment Controller.
	Enforces Rule IDs ASN-001 through ASN-010 and auto-population cascades.
	"""
	doctype = "Vehicle Assignment"


	def before_validate_hook(self):
		if not self.status:
			self.status = AssignmentStatus.DRAFT
		if not self.naming_series:
			self.naming_series = "ASSIGN-.YYYY.-.#####"

		# ASSIGN-008: Closed / Cancelled read-only protection

		if not self.is_new() and self.db_get("status") in (AssignmentStatus.CLOSED, AssignmentStatus.CANCELLED):
			old_status = self.db_get("status")
			if self.status != old_status:
				raise FleetValidationError(f"ASSIGN-008: Assignment is '{old_status}' and cannot be modified.")

		# 1. Run AssignmentValidator structural checks (ASN-001..ASN-010)
		AssignmentValidator(self.as_dict()).raise_if_invalid()

		# 2. Default assignment date to today if empty
		if not self.assignment_date and hasattr(frappe, "utils"):
			self.assignment_date = frappe.utils.nowdate()

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
				if not self.vehicle_category:
					self.vehicle_category = v_doc.vehicle_category
				if not self.fuel_type:
					self.fuel_type = v_doc.fuel_type
				if not self.current_odometer:
					self.current_odometer = v_doc.current_odometer
				if not self.company:
					self.company = v_doc.company
				if not self.vehicle_status_indicator:
					self.vehicle_status_indicator = v_doc.status

				# Default Opening Odometer from Vehicle current odometer
				if (not self.opening_odometer or self.opening_odometer == 0) and v_doc.current_odometer:
					self.opening_odometer = float(v_doc.current_odometer)

		# 4. Auto-fetch Employee details if blank
		if self.employee:
			emp_doc = get_doc_or_none("User", self.employee)
			if emp_doc:
				if not self.employee_name:
					self.employee_name = emp_doc.full_name or emp_doc.name

		# 5. Validate Date Range
		if self.assignment_date and self.expected_return_date:
			validate_date_range(self.assignment_date, self.expected_return_date, "Assignment Date", "Expected Return Date")
