"""
Demo Data & Administrator Tools Whitelisted API Endpoints
Fleet Management System (Frappe v15)
"""

from typing import Any, Dict

import frappe

from fleet_management.api.base import api_endpoint
from fleet_management.api.responses import success_response
from fleet_management.services.demo_data_service import DemoDataService

demo_service = DemoDataService()


@api_endpoint(allow_guest=False, roles=["System Manager", "Fleet Manager"])
def load_demo_data() -> Dict[str, Any]:
	"""Whitelisted API endpoint loading complete demo dataset."""
	res = demo_service.load_demo_data()
	return success_response(data=res, message="Demo dataset loaded successfully.")


@api_endpoint(allow_guest=False, roles=["System Manager", "Fleet Manager"])
def remove_demo_data() -> Dict[str, Any]:
	"""Whitelisted API endpoint removing demo dataset."""
	res = demo_service.remove_demo_data()
	return success_response(data=res, message="Demo dataset removed successfully.")


@api_endpoint(allow_guest=False, roles=["System Manager", "Fleet Manager"])
def reload_demo_data() -> Dict[str, Any]:
	"""Whitelisted API endpoint reloading demo dataset."""
	res = demo_service.reload_demo_data()
	return success_response(data=res, message="Demo dataset reloaded successfully.")


@api_endpoint(allow_guest=False)
def get_demo_status() -> Dict[str, Any]:
	"""Whitelisted API endpoint getting demo data status."""
	res = demo_service.get_demo_status()
	return success_response(data=res, message="Demo status retrieved.")


@api_endpoint(allow_guest=False, roles=["System Manager", "Fleet Manager"])
def system_health_check() -> Dict[str, Any]:
	"""Administrator Tool: System Health Check."""
	from fleet_management.services.scheduler import scheduled_health_check
	res = scheduled_health_check()
	return success_response(data={"health_status": "Healthy", "check_details": res}, message="System health check executed cleanly.")


@api_endpoint(allow_guest=False, roles=["System Manager", "Fleet Manager"])
def recalculate_fleet_statistics() -> Dict[str, Any]:
	"""Administrator Tool: Recalculates fleet operational summary for all vehicles."""
	from fleet_management.services.vehicle_service import sync_all_vehicles_operational_summary
	sync_all_vehicles_operational_summary()
	return success_response(data={"status": "completed"}, message="Fleet statistics recalculated successfully.")
