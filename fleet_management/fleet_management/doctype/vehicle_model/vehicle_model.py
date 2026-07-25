"""
Vehicle Model Controller
Fleet Management System
"""

import datetime

import frappe

from fleet_management.utils.base_document import BaseFleetDocument
from fleet_management.utils.exceptions import FleetDuplicateEntryError
from fleet_management.validators.common_validators import (
	validate_positive_number,
	validate_range,
	validate_required_fields,
)


class VehicleModel(BaseFleetDocument):
	"""
	Vehicle Model Master Document Controller.
	Rule IDs: MASTER-002, MASTER-003, MASTER-004
	"""
	doctype = "Vehicle Model"


	def before_validate_hook(self):
		# MASTER-002: Required fields and Brand + Model combination uniqueness
		validate_required_fields(self.as_dict(), ["model_name", "vehicle_brand"])

		filters = {
			"vehicle_brand": self.vehicle_brand,
			"model_name": self.model_name
		}
		if self.name:
			filters["name"] = ["!=", self.name]

		if frappe.db.exists("Vehicle Model", filters):
			raise FleetDuplicateEntryError(
				f"Vehicle Model '{self.model_name}' already exists for Brand '{self.vehicle_brand}'."
			)

		# MASTER-003: Model year range validation
		if self.year:
			next_year = datetime.date.today().year + 1
			validate_range(self.year, 1900, next_year, "Year")

		# MASTER-004: Fuel average validation
		if self.default_fuel_average:
			validate_positive_number(self.default_fuel_average, "Default Fuel Average", allow_zero=False)
