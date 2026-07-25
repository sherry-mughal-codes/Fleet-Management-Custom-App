"""
API v1 - Vehicle Intelligence REST Endpoints
Fleet Management System
"""

from fleet_management.api.vehicle_api import (
	change_vehicle_status,
	create_vehicle,
	get_vehicle_asset_summary,
	get_vehicle_dashboard_summary,
	get_vehicle_documents,
	get_vehicle_images,
	get_vehicle_quick_actions,
	get_vehicle_summary,
	get_vehicle_timeline_api,
	search_vehicles,
)

__all__ = [
	"search_vehicles",
	"get_vehicle_summary",
	"create_vehicle",
	"change_vehicle_status",
	"get_vehicle_dashboard_summary",
	"get_vehicle_timeline_api",
	"get_vehicle_quick_actions",
	"get_vehicle_documents",
	"get_vehicle_images",
	"get_vehicle_asset_summary",
]
