"""
Maintenance Work Order Main Document Controller
Fleet Management System
"""

from fleet_management.utils.base_document import BaseFleetDocument
from fleet_management.utils.helpers import get_doc_or_none
from fleet_management.validators.maintenance_validator import MaintenanceValidator


class MaintenanceWorkOrder(BaseFleetDocument):
	"""
	Maintenance Work Order Controller.
	Manages work order execution details and task checklist child tables.
	"""
	doctype = "Maintenance Work Order"


	def before_validate_hook(self):
		if not self.status:
			self.status = "Draft"
		if not self.naming_series:
			self.naming_series = "MWO-.YYYY.-.#####"

		# 1. Auto-fetch vehicle and company from maintenance request if linked

		if self.maintenance_request and not self.vehicle:
			req_doc = get_doc_or_none("Maintenance Request", self.maintenance_request)
			if req_doc:
				self.vehicle = req_doc.vehicle
				if not self.company:
					self.company = req_doc.company
				if not self.workshop:
					self.workshop = req_doc.workshop_name

		# 2. Structural validation via MaintenanceValidator
		MaintenanceValidator(self.as_dict()).raise_if_invalid()

		# 3. Calculate total cost (labour + parts + external + tax - discount)
		labour = float(self.labour_cost or 0.0)
		parts = float(self.parts_cost or 0.0)
		external = float(self.external_cost or 0.0)
		tax = float(self.tax_amount or 0.0)
		discount = float(self.discount_amount or 0.0)
		self.total_cost = round((labour + parts + external + tax) - discount, 2)
