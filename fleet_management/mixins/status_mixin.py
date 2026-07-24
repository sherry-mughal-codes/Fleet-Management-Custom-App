"""
Status Mixin
Fleet Management System
"""

from typing import Dict, Sequence
from fleet_management.validators.common_validators import validate_status_transition

class StatusMixin:
	"""
	Mixin validating document status transitions against allowed state transitions.
	"""

	allowed_status_transitions: Dict[str, Sequence[str]] = {}

	def validate_status_change(self, target_status: str):
		current_status = getattr(self, "status", None)
		if current_status and self.allowed_status_transitions:
			validate_status_transition(
				current_status=current_status,
				target_status=target_status,
				allowed_transitions=self.allowed_status_transitions
			)
