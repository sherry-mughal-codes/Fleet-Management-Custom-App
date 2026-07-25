"""
Vehicle Domain Event Dispatcher
Fleet Management System
"""

from typing import Any

from fleet_management.enums import VehicleEventType
from fleet_management.events.registry import DocumentEventRegistry
from fleet_management.utils.logger import get_logger

logger = get_logger("fleet_management.events.vehicle")


class VehicleEventDispatcher:
	"""
	Central Event Dispatcher for Vehicle Lifecycle Events.
	"""

	@staticmethod
	def notify_vehicle_created(vehicle_doc: Any):
		logger.info(f"VEHICLE_EVENT: Created {vehicle_doc.name}")
		DocumentEventRegistry.dispatch(VehicleEventType.CREATED, vehicle_doc, "on_vehicle_created")

	@staticmethod
	def notify_vehicle_updated(vehicle_doc: Any):
		logger.info(f"VEHICLE_EVENT: Updated {vehicle_doc.name}")
		DocumentEventRegistry.dispatch(VehicleEventType.UPDATED, vehicle_doc, "on_vehicle_updated")

	@staticmethod
	def notify_status_changed(vehicle_doc: Any, old_status: str, new_status: str):
		logger.info(f"VEHICLE_EVENT: Status Changed {vehicle_doc.name} [{old_status} -> {new_status}]")
		DocumentEventRegistry.dispatch(
			VehicleEventType.STATUS_CHANGED,
			vehicle_doc,
			f"on_status_changed:{old_status}->{new_status}"
		)

	@staticmethod
	def notify_vehicle_archived(vehicle_doc: Any):
		logger.info(f"VEHICLE_EVENT: Archived {vehicle_doc.name}")
		DocumentEventRegistry.dispatch(VehicleEventType.ARCHIVED, vehicle_doc, "on_vehicle_archived")
