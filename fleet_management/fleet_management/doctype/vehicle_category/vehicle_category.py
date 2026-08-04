"""
Vehicle Category Controller
Fleet Management System
"""

from fleet_management.utils.base_document import BaseFleetDocument
from fleet_management.validators.common_validators import (
	validate_required_fields,
)


class VehicleCategory(BaseFleetDocument):
	"""
	Vehicle Category Master Document Controller.
	"""

	doctype = "Vehicle Category"

	def before_validate_hook(self):
		validate_required_fields(self.as_dict(), ["category_name"])
