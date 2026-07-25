"""
API v1 - Demo Data REST Endpoints
Fleet Management System
"""

from fleet_management.api.demo_api import (
	get_demo_status,
	load_demo_data,
	reload_demo_data,
	remove_demo_data,
)

__all__ = [
	"load_demo_data",
	"remove_demo_data",
	"reload_demo_data",
	"get_demo_status",
]
