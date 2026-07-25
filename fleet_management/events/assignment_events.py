"""
Assignment Domain Event Dispatcher
Fleet Management System
"""

from typing import Any

from fleet_management.enums import AssignmentEventType
from fleet_management.events.registry import DocumentEventRegistry
from fleet_management.utils.logger import get_logger

logger = get_logger("fleet_management.events.assignment")


class AssignmentEventDispatcher:
	"""
	Central Event Dispatcher for Vehicle Assignment Lifecycle Events.
	"""

	@staticmethod
	def notify_assignment_created(assignment_doc: Any):
		logger.info(f"ASSIGNMENT_EVENT: Created {assignment_doc.name}")
		DocumentEventRegistry.dispatch(AssignmentEventType.CREATED, assignment_doc, "on_assignment_created")

	@staticmethod
	def notify_assignment_approved(assignment_doc: Any):
		logger.info(f"ASSIGNMENT_EVENT: Approved {assignment_doc.name}")
		DocumentEventRegistry.dispatch(AssignmentEventType.APPROVED, assignment_doc, "on_assignment_approved")

	@staticmethod
	def notify_handover(assignment_doc: Any):
		logger.info(f"ASSIGNMENT_EVENT: Vehicle Handover {assignment_doc.name}")
		DocumentEventRegistry.dispatch(AssignmentEventType.HANDOVER, assignment_doc, "on_vehicle_handover")

	@staticmethod
	def notify_returned(assignment_doc: Any):
		logger.info(f"ASSIGNMENT_EVENT: Vehicle Returned {assignment_doc.name}")
		DocumentEventRegistry.dispatch(AssignmentEventType.RETURNED, assignment_doc, "on_vehicle_returned")

	@staticmethod
	def notify_closed(assignment_doc: Any):
		logger.info(f"ASSIGNMENT_EVENT: Closed {assignment_doc.name}")
		DocumentEventRegistry.dispatch(AssignmentEventType.CLOSED, assignment_doc, "on_assignment_closed")

	@staticmethod
	def notify_cancelled(assignment_doc: Any):
		logger.info(f"ASSIGNMENT_EVENT: Cancelled {assignment_doc.name}")
		DocumentEventRegistry.dispatch(AssignmentEventType.CANCELLED, assignment_doc, "on_assignment_cancelled")
