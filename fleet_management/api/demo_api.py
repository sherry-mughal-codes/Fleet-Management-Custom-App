"""
Demo Data Domain Whitelisted API Endpoints Implementation
Fleet Management System
"""

from typing import Any, Dict

import frappe

from fleet_management.services.demo_data_service import DemoDataService

demo_service = DemoDataService()


@frappe.whitelist(allow_guest=True)
def load_demo_data() -> Dict[str, Any]:
	"""Whitelisted API endpoint loading complete demo dataset."""
	frappe.set_user("Administrator")
	return demo_service.load_demo_data()


@frappe.whitelist(allow_guest=True)
def remove_demo_data() -> Dict[str, Any]:
	"""Whitelisted API endpoint removing demo dataset."""
	frappe.set_user("Administrator")
	return demo_service.remove_demo_data()


@frappe.whitelist(allow_guest=True)
def reload_demo_data() -> Dict[str, Any]:
	"""Whitelisted API endpoint reloading demo dataset."""
	frappe.set_user("Administrator")
	return demo_service.reload_demo_data()


@frappe.whitelist(allow_guest=True)
def get_demo_status() -> Dict[str, Any]:
	"""Whitelisted API endpoint getting demo data status."""
	frappe.set_user("Administrator")
	return demo_service.get_demo_status()
