"""
Maintenance Business Rules Architecture Contract Interface
Fleet Management System
"""

from fleet_management.business_rules.base_rule import BaseBusinessRule


class MaintenanceScheduleRule(BaseBusinessRule):
	"""
	Rule contract evaluating maintenance service trigger intervals.
	"""

	def evaluate(self) -> bool:
		current_km = self.context.get("current_odometer", 0)
		next_due_km = self.context.get("next_due_odometer", 0)
		if next_due_km > 0 and current_km >= next_due_km:
			self.add_violation(f"Vehicle has reached or exceeded maintenance due odometer ({next_due_km} KM).")
			return False
		return True
