"""
Vehicle Category Controller
Fleet Management System
"""

from fleet_management.utils.base_document import BaseFleetDocument
from fleet_management.validators.common_validators import validate_required_fields, validate_positive_number


class VehicleCategory(BaseFleetDocument):
	"""
	Vehicle Category Master Document Controller.
	Rule IDs: MASTER-005, MASTER-013
	"""
	doctype = "Vehicle Category"


	def before_validate_hook(self):
		validate_required_fields(self.as_dict(), ["category_name"])
		# MASTER-005: Validate maintenance interval
		if self.default_maintenance_interval:
			validate_positive_number(self.default_maintenance_interval, "Default Maintenance Interval", allow_zero=False)
		# MASTER-013: Validate display order
		if self.display_order:
			validate_positive_number(self.display_order, "Display Order", allow_zero=True)
