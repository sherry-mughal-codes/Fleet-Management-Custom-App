"""
API v1 - Assignment Intelligence REST Endpoints
Fleet Management System
"""

from fleet_management.api.assignment_api import (
	search_assignments,
	get_assignment_summary,
	create_assignment,
	assign_vehicle_api,
	return_vehicle_api,
	close_assignment_api,
	cancel_assignment_api,
	get_assignment_timeline_api,
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
