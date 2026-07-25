"""
Distance Unit Controller
Fleet Management System
"""

from fleet_management.utils.base_document import BaseFleetDocument
from fleet_management.validators.common_validators import validate_required_fields, validate_positive_number


class DistanceUnit(BaseFleetDocument):
	"""
	Distance Unit Master Document Controller.
	Rule IDs: MASTER-011
	"""
	doctype = "Distance Unit"


	def before_validate_hook(self):
		validate_required_fields(self.as_dict(), ["unit_name"])
		# MASTER-011: Validate conversion multiplier
		if self.conversion_to_km is not None:
			validate_positive_number(self.conversion_to_km, "Conversion to KM", allow_zero=False)

