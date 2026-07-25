"""
API v1 - Assignment Intelligence REST Endpoints
Fleet Management System
"""

from fleet_management.api.assignment_api import (
	assign_vehicle_api,
	cancel_assignment_api,
	close_assignment_api,
	create_assignment,
	get_assignment_summary,
	get_assignment_timeline_api,
	return_vehicle_api,
	search_assignments,
)

__all__ = [
	"search_assignments",
	"get_assignment_summary",
	"create_assignment",
	"assign_vehicle_api",
	"return_vehicle_api",
	"close_assignment_api",
	"cancel_assignment_api",
	"get_assignment_timeline_api",
]
