"""
Company Master Document Controller
Fleet Management System
"""

from fleet_management.utils.base_document import BaseFleetDocument
from fleet_management.validators.common_validators import validate_required_fields


class Company(BaseFleetDocument):
	"""
	Company Master Document Controller.
	Provides company multi-tenant isolation support across Fleet Management entities.
	"""
	doctype = "Company"

	def before_validate_hook(self):
		validate_required_fields(self.as_dict(), ["company_name"])
		if not self.abbr and self.company_name:
			words = self.company_name.split()
			self.abbr = "".join([w[0].upper() for w in words if w])[:5]
