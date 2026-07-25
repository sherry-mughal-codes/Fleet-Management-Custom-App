"""
Vehicle Colour Controller
Fleet Management System
"""

import re
from fleet_management.utils.base_document import BaseFleetDocument
from fleet_management.validators.common_validators import validate_required_fields
from fleet_management.utils.exceptions import FleetValidationError


class VehicleColour(BaseFleetDocument):
	"""
	Vehicle Colour Master Document Controller.
	Rule IDs: MASTER-010
	"""
	doctype = "Vehicle Colour"


	def before_validate_hook(self):
		validate_required_fields(self.as_dict(), ["colour_name"])
		# MASTER-010: Validate hex code format if provided
		if self.hex_code:
			if not re.match(r"^#(?:[0-9a-fA-F]{3}){1,2}$", self.hex_code.strip()):
				raise FleetValidationError(f"Invalid Hex Code '{self.hex_code}'. Must be in format #RRGGBB or #RGB.")
