"""
Assignment Domain Security & Permission Architecture
Fleet Management System
"""


from fleet_management.enums import FleetRole
from fleet_management.permissions.evaluator import PermissionEvaluator
from fleet_management.utils.exceptions import FleetPermissionError


class AssignmentPermissionEvaluator:
	"""
	Central Security Evaluator for Vehicle Assignment records and lifecycle operations.
	"""

	@staticmethod
	def can_create_assignment(user: str | None = None) -> bool:
		"""Check if user is authorized to create an assignment."""
		return (
			PermissionEvaluator.has_role(FleetRole.MANAGER, user)
			or PermissionEvaluator.has_role(FleetRole.OFFICER, user)
			or PermissionEvaluator.has_role(FleetRole.DISPATCHER, user)
		)

	@staticmethod
	def can_approve_assignment(user: str | None = None) -> bool:
		"""Check if user is authorized to approve assignments."""
		return PermissionEvaluator.has_role(FleetRole.MANAGER, user) or PermissionEvaluator.has_role(FleetRole.OFFICER, user)

	@staticmethod
	def require_approval_permission(user: str | None = None):
		"""Raise FleetPermissionError if user cannot approve assignments."""
		if not AssignmentPermissionEvaluator.can_approve_assignment(user):
			raise FleetPermissionError("Permission denied: Assignment approval requires Fleet Manager or Officer role.")
