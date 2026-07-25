"""
Vehicle Brand Controller
Fleet Management System
"""

from fleet_management.utils.base_document import BaseFleetDocument
from fleet_management.validators.common_validators import validate_required_fields, validate_positive_number, validate_duplicate


class VehicleBrand(BaseFleetDocument):
	"""
	Vehicle Brand Master Document Controller.
	Rule IDs: MASTER-001, MASTER-013
	"""
	doctype = "Vehicle Brand"


	def before_validate_hook(self):
		# MASTER-001: Validate required brand fields & uniqueness
		validate_required_fields(self.as_dict(), ["brand_name", "brand_code"])
		validate_duplicate("Vehicle Brand", "brand_code", self.brand_code, exclude_name=self.name)
		
		# MASTER-013: Validate display order
		if self.display_order:
			validate_positive_number(self.display_order, "Display Order", allow_zero=True)
