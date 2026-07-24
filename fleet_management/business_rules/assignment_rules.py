"""
Assignment Business Rules Architecture Contract Interface
Fleet Management System
"""

from fleet_management.business_rules.base_rule import BaseBusinessRule


class DriverLicenseRule(BaseBusinessRule):
	"""
	Rule contract verifying driver license validity for assignment.
	"""

	def evaluate(self) -> bool:
		is_active = self.context.get("is_active_license", True)
		if not is_active:
			self.add_violation("Driver license is expired or invalid.")
			return False
		return True
