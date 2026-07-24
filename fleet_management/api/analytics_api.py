"""
Fleet Analytics & Command Center Whitelisted API Endpoints
Fleet Management System
"""

from typing import Any, Dict, Optional
import frappe
from fleet_management.api.base import api_endpoint
from fleet_management.api.responses import success_response
from fleet_management.services.fleet_analytics_service import FleetAnalyticsService

analytics_service = FleetAnalyticsService()


@api_endpoint(allow_guest=False)
def get_executive_dashboard_api(company: Optional[str] = None) -> Dict[str, Any]:
	"""Whitelisted API endpoint for retrieving full executive command center payload."""
	user = frappe.session.user if hasattr(frappe, "session") else "Administrator"
	data = analytics_service.get_dashboard_data(user, company)
	return success_response(data=data, message="Executive command center data retrieved successfully.")


@api_endpoint(allow_guest=False)
def get_kpis_api(company: Optional[str] = None) -> Dict[str, Any]:
	"""Whitelisted API endpoint for retrieving executive KPI cards."""
	kpis = analytics_service.get_executive_kpis(company)
	return success_response(data=kpis, message="Executive KPIs retrieved successfully.")


@api_endpoint(allow_guest=False)
def get_alerts_api(company: Optional[str] = None) -> Dict[str, Any]:
	"""Whitelisted API endpoint for retrieving smart severity alerts."""
	alerts = analytics_service.get_smart_alerts(company)
	return success_response(data=alerts, message="Smart alerts retrieved successfully.")


@api_endpoint(allow_guest=False)
def get_charts_api(company: Optional[str] = None) -> Dict[str, Any]:
	"""Whitelisted API endpoint for retrieving analytics chart data feeds."""
	charts = analytics_service.get_analytics_charts(company)
	return success_response(data=charts, message="Analytics charts retrieved successfully.")


@api_endpoint(allow_guest=False)
def get_vehicle_health_table_api(company: Optional[str] = None, limit: int = 20) -> Dict[str, Any]:
	"""Whitelisted API endpoint for retrieving vehicle health table data."""
	health = analytics_service.get_vehicle_health_summary(company, limit=limit)
	return success_response(data=health, message="Vehicle health table retrieved successfully.")


@api_endpoint(allow_guest=False)
def get_recent_activity_api(company: Optional[str] = None, limit: int = 10) -> Dict[str, Any]:
	"""Whitelisted API endpoint for retrieving recent activity timeline events."""
	activity = analytics_service.get_recent_activity_timeline(company, limit=limit)
	return success_response(data=activity, message="Recent activity timeline retrieved successfully.")
