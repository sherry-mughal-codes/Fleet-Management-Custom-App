"""
Fuel Unit Controller
Fleet Management System
"""

from fleet_management.utils.base_document import BaseFleetDocument
from fleet_management.validators.common_validators import validate_required_fields, validate_positive_number


class FuelUnit(BaseFleetDocument):
	"""
	Fuel Unit Master Document Controller.
	Rule IDs: MASTER-012
	"""

	def before_validate_hook(self):
		validate_required_fields(self.as_dict(), ["unit_name"])
		# MASTER-012: Validate conversion multiplier
		if self.conversion_to_liters:
			validate_positive_number(self.conversion_to_liters, "Conversion to Liters", allow_zero=False)
