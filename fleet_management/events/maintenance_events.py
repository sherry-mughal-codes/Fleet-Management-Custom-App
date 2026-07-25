"""
Maintenance Domain Event Dispatcher
Fleet Management System
"""

from typing import Any

from fleet_management.enums import MaintenanceEventType
from fleet_management.events.registry import DocumentEventRegistry
from fleet_management.utils.logger import get_logger

logger = get_logger("fleet_management.events.maintenance")


class MaintenanceEventDispatcher:
	"""
	Central Event Dispatcher for Maintenance Lifecycle Events.
	"""

	@staticmethod
	def notify_maintenance_created(maint_doc: Any):
		logger.info(f"MAINTENANCE_EVENT: Created {maint_doc.name}")
		DocumentEventRegistry.dispatch(MaintenanceEventType.CREATED, maint_doc, "on_maintenance_created")

	@staticmethod
	def notify_maintenance_scheduled(maint_doc: Any):
		logger.info(f"MAINTENANCE_EVENT: Scheduled {maint_doc.name}")
		DocumentEventRegistry.dispatch(MaintenanceEventType.SCHEDULED, maint_doc, "on_maintenance_scheduled")

	@staticmethod
	def notify_maintenance_in_progress(maint_doc: Any):
		logger.info(f"MAINTENANCE_EVENT: In Progress {maint_doc.name}")
		DocumentEventRegistry.dispatch(MaintenanceEventType.IN_PROGRESS, maint_doc, "on_maintenance_in_progress")

	@staticmethod
	def notify_maintenance_completed(maint_doc: Any):
		logger.info(f"MAINTENANCE_EVENT: Completed {maint_doc.name}")
		DocumentEventRegistry.dispatch(MaintenanceEventType.COMPLETED, maint_doc, "on_maintenance_completed")

	@staticmethod
	def notify_maintenance_cancelled(maint_doc: Any):
		logger.info(f"MAINTENANCE_EVENT: Cancelled {maint_doc.name}")
		DocumentEventRegistry.dispatch(MaintenanceEventType.CANCELLED, maint_doc, "on_maintenance_cancelled")
