"""
Vehicle Brand Controller
Fleet Management System
"""

from fleet_management.utils.base_document import BaseFleetDocument
from fleet_management.validators.common_validators import (
	validate_duplicate,
	validate_required_fields,
)


class VehicleBrand(BaseFleetDocument):
	"""
	Vehicle Brand Master Document Controller.
	Rule ID: MASTER-001
	"""

	doctype = "Vehicle Brand"

	def before_validate_hook(self):
		# MASTER-001: Validate required brand fields & uniqueness
		validate_required_fields(self.as_dict(), ["brand_name", "brand_code"])
		validate_duplicate("Vehicle Brand", "brand_code", self.brand_code, exclude_name=self.name)
