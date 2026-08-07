"""
Vehicle Assignment Main Document Controller
Fleet Management System
"""

import frappe

from fleet_management.utils.base_document import BaseFleetDocument
from fleet_management.utils.helpers import get_doc_or_none
from fleet_management.validators.assignment_validator import AssignmentValidator
from fleet_management.validators.common_validators import validate_date_range


class VehicleAssignment(BaseFleetDocument):
	"""
	Vehicle Assignment Controller.
	Enforces Rule IDs ASN-001 through ASN-010 and auto-population cascades.
	"""
	doctype = "Vehicle Assignment"

	def before_validate_hook(self):
		if not self.naming_series:
			self.naming_series = "ASSIGN-.YYYY.-.#####"

		# Default status
		if not self.status:
			self.status = "Draft"

		# 1. Auto-fetch Company and Opening Odometer from Vehicle / Latest Fuel Entry
		if self.vehicle:
			v_doc = get_doc_or_none("Fleet Vehicle", self.vehicle)
			if v_doc and not self.company:
				self.company = v_doc.company

			# Default Opening Odometer from latest Fuel Entry odometer for this vehicle
			if not self.opening_odometer or self.opening_odometer == 0:
				latest_fuel_odo = frappe.db.get_value(
					"Fuel Entry",
					filters={"vehicle": self.vehicle, "docstatus": 1},
					fieldname="MAX(odometer)"
				) or 0.0

				odo = float(latest_fuel_odo)
				if not odo and v_doc:
					odo = float(v_doc.initial_odometer or 0.0)

				if odo:
					self.opening_odometer = odo

		# 2. Default assignment date to today if empty
		if not self.assignment_date and hasattr(frappe, "utils"):
			self.assignment_date = frappe.utils.nowdate()

		# 3. Auto-calculate distance travelled if closing odometer is present
		if self.closing_odometer and self.opening_odometer:
			self.distance_travelled = max(0.0, float(self.closing_odometer) - float(self.opening_odometer))

		# 4. Handle Status (Returned, Return Overdue, or Assigned)
		if self.return_date or self.closing_odometer:
			self.status = "Returned"
		elif self.status in ("Assigned", "Return Overdue") or self.docstatus == 1:
			if self.expected_return_date and hasattr(frappe, "utils"):
				today = frappe.utils.nowdate()
				if str(self.expected_return_date) < str(today):
					self.status = "Return Overdue"
				else:
					self.status = "Assigned"

		# 5. Run AssignmentValidator structural checks
		AssignmentValidator(self.as_dict()).raise_if_invalid()

		# 6. Validate Date Range
		if self.assignment_date and self.expected_return_date:
			validate_date_range(self.assignment_date, self.expected_return_date, "Assignment Date", "Expected Return Date")

	def on_submit(self):
		"""
		On Submit: Set assignment status to Assigned (or Return Overdue if date passed) and Vehicle status to Assigned.
		"""
		target_status = "Assigned"
		if self.expected_return_date and hasattr(frappe, "utils"):
			if str(self.expected_return_date) < str(frappe.utils.nowdate()):
				target_status = "Return Overdue"

		self.db_set("status", target_status)
		if self.vehicle:
			from fleet_management.enums import VehicleStatus
			from fleet_management.services.vehicle_service import VehicleService

			VehicleService().change_status(self.vehicle, VehicleStatus.ASSIGNED, reason=f"Assigned via Assignment {self.name}")

	def on_cancel(self):
		"""
		Cancellation disabled for Vehicle Assignments.
		"""
		frappe.throw("Cancellation is disabled for Vehicle Assignments.")
