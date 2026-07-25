"""
Central Document Event Registry Architecture
Fleet Management System
"""

from typing import Callable, Dict, List

from fleet_management.utils.logger import get_logger

logger = get_logger("fleet_management.events")


class DocumentEventRegistry:
	"""
	Central Event Registry dispatching doc_events hooks cleanly across modules.
	"""

	_subscribers: Dict[str, List[Callable]] = {}

	@classmethod
	def subscribe(cls, event_name: str, handler: Callable):
		"""Subscribe handler callable to document event."""
		if event_name not in cls._subscribers:
			cls._subscribers[event_name] = []
		cls._subscribers[event_name].append(handler)
		logger.info(f"Subscribed handler '{handler.__name__}' to event '{event_name}'")

	@classmethod
	def dispatch(cls, event_name: str, doc, method: str):
		"""Dispatch event to subscribed handlers."""
		handlers = cls._subscribers.get(event_name, [])
		for handler in handlers:
			try:
				handler(doc, method)
			except Exception as e:
				logger.error(f"Error executing event handler '{handler.__name__}': {str(e)}", exc=e)
