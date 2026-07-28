"""
Demo Data Manager Service
Fleet Management System (Frappe v15)

Enterprise demo data generator for fleet simulation and end-to-end testing.
"""

from typing import Any, Dict
import frappe

from fleet_management.services.base_service import BaseService
from fleet_management.services.demo_data_service import DemoDataService
from fleet_management.utils.logger import get_logger

logger = get_logger("fleet_management.services.demo_data_manager")


class DemoDataManager(BaseService):
	"""
	Enterprise manager for generating demo data.
	"""

	def __init__(self):
		super().__init__()
		self.delegate = DemoDataService()

	def generate_demo_data(self) -> Dict[str, Any]:
		"""Generates comprehensive enterprise demo data."""
		logger.info("Generating demo fleet data via DemoDataManager")
		return self.delegate.generate_all()

	def wipe_demo_data(self) -> bool:
		"""Wipes generated demo fleet data."""
		logger.info("Wiping demo fleet data via DemoDataManager")
		return self.delegate.wipe_all()
