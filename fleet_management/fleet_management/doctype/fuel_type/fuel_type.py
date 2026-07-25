"""
Fuel Type Controller
Fleet Management System
"""

from fleet_management.utils.base_document import BaseFleetDocument
from fleet_management.validators.common_validators import validate_required_fields, validate_positive_number


class FuelType(BaseFleetDocument):
	"""
	Fuel Type Master Document Controller.
	Rule IDs: MASTER-006
	"""
	doctype = "Fuel Type"


	def before_validate_hook(self):
		validate_required_fields(self.as_dict(), ["fuel_name"])
		# MASTER-006: Validate density if provided
		if self.default_density:
			validate_positive_number(self.default_density, "Default Density", allow_zero=False)
