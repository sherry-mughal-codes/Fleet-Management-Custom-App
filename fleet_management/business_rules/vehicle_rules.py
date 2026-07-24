"""
Vehicle Business Rules Architecture Contract Interface
Fleet Management System
"""

from typing import Dict, Any
from fleet_management.business_rules.base_rule import BaseBusinessRule


class VehicleAvailabilityRule(BaseBusinessRule):
	"""
	Rule contract verifying vehicle availability status.
	"""

	def evaluate(self) -> bool:
		vehicle_status = self.context.get("status")
		if vehicle_status == "Out of Service" or vehicle_status == "Disposed":
			self.add_violation(f"Vehicle status '{vehicle_status}' is unavailable for operations.")
			return False
		return True
