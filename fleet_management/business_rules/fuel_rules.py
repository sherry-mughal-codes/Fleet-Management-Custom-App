"""
Fuel Entry Business Rules Architecture Contract Interface
Fleet Management System
"""

from fleet_management.business_rules.base_rule import BaseBusinessRule


class FuelCapacityThresholdRule(BaseBusinessRule):
	"""
	Rule contract verifying fuel entry volume against tank capacity.
	"""

	def evaluate(self) -> bool:
		liters = float(self.context.get("fuel_amount", 0))
		max_capacity = float(self.context.get("max_capacity", 500))
		if liters > max_capacity:
			self.add_violation(f"Fuel quantity ({liters}L) exceeds maximum capacity threshold ({max_capacity}L).")
			return False
		return True
