"""
API v1 - Fleet Analytics & Command Center REST Endpoints
Fleet Management System
"""

from fleet_management.api.analytics_api import (
	get_executive_dashboard_api,
	get_kpis_api,
	get_alerts_api,
	get_charts_api,
	get_vehicle_health_table_api,
	get_recent_activity_api,
)

__all__ = [
	"get_executive_dashboard_api",
	"get_kpis_api",
	"get_alerts_api",
	"get_charts_api",
	"get_vehicle_health_table_api",
	"get_recent_activity_api",
]
