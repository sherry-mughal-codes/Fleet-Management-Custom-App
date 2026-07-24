"""
Maintenance Summary Script Report Implementation
Fleet Management System
"""

import frappe
from fleet_management.services.maintenance_service import MaintenanceService

maintenance_service = MaintenanceService()


def execute(filters=None):
	columns = [
		{"label": "Request ID", "fieldname": "name", "fieldtype": "Link", "options": "Maintenance Request", "width": 140},
		{"label": "Vehicle", "fieldname": "vehicle", "fieldtype": "Link", "options": "Vehicle", "width": 140},
		{"label": "Type", "fieldname": "maintenance_type", "fieldtype": "Data", "width": 120},
		{"label": "Priority", "fieldname": "priority", "fieldtype": "Data", "width": 120},
		{"label": "Requested Date", "fieldname": "requested_date", "fieldtype": "Date", "width": 130},
		{"label": "Status", "fieldname": "status", "fieldtype": "Data", "width": 120},
		{"label": "Company", "fieldname": "company", "fieldtype": "Link", "options": "Company", "width": 140}
	]

	vehicle = filters.get("vehicle") if filters else None
	data = maintenance_service.get_vehicle_history(vehicle, limit=100) if vehicle else []

	return columns, data
