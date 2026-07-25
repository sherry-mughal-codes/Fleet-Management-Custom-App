"""
Fuel Domain Event Dispatcher
Fleet Management System
"""

from typing import Any

from fleet_management.enums import FuelEventType
from fleet_management.events.registry import DocumentEventRegistry
from fleet_management.utils.logger import get_logger

logger = get_logger("fleet_management.events.fuel")


class FuelEventDispatcher:
	"""
	Central Event Dispatcher for Fuel Entry Lifecycle Events.
	"""

	@staticmethod
	def notify_fuel_created(fuel_doc: Any):
		logger.info(f"FUEL_EVENT: Created {fuel_doc.name}")
		DocumentEventRegistry.dispatch(FuelEventType.CREATED, fuel_doc, "on_fuel_created")

	@staticmethod
	def notify_fuel_submitted(fuel_doc: Any):
		logger.info(f"FUEL_EVENT: Submitted {fuel_doc.name}")
		DocumentEventRegistry.dispatch(FuelEventType.SUBMITTED, fuel_doc, "on_fuel_submitted")

	@staticmethod
	def notify_fuel_verified(fuel_doc: Any):
		logger.info(f"FUEL_EVENT: Verified {fuel_doc.name}")
		DocumentEventRegistry.dispatch(FuelEventType.VERIFIED, fuel_doc, "on_fuel_verified")

	@staticmethod
	def notify_fuel_cancelled(fuel_doc: Any):
		logger.info(f"FUEL_EVENT: Cancelled {fuel_doc.name}")
		DocumentEventRegistry.dispatch(FuelEventType.CANCELLED, fuel_doc, "on_fuel_cancelled")
