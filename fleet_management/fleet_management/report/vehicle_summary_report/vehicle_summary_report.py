"""
Vehicle Summary Script Report Implementation
Fleet Management System
"""

import frappe
from fleet_management.services.fleet_analytics_service import FleetAnalyticsService

analytics_service = FleetAnalyticsService()


def execute(filters=None):
	columns = [
		{"label": "Vehicle", "fieldname": "vehicle", "fieldtype": "Link", "options": "Vehicle", "width": 140},
		{"label": "Vehicle Number", "fieldname": "vehicle_number", "fieldtype": "Data", "width": 130},
		{"label": "Vehicle Name", "fieldname": "vehicle_name", "fieldtype": "Data", "width": 140},
		{"label": "Brand", "fieldname": "brand", "fieldtype": "Link", "options": "Vehicle Brand", "width": 120},
		{"label": "Model", "fieldname": "model", "fieldtype": "Link", "options": "Vehicle Model", "width": 120},
		{"label": "Current Odometer (KM)", "fieldname": "current_odometer", "fieldtype": "Float", "width": 160},
		{"label": "Status", "fieldname": "status", "fieldtype": "Data", "width": 130},
		{"label": "Fuel Economy (KM/L)", "fieldname": "fuel_average", "fieldtype": "Float", "width": 160},
		{"label": "Total Fuel Cost", "fieldname": "total_fuel_cost", "fieldtype": "Currency", "width": 140},
		{"label": "Total Maintenance Cost", "fieldname": "total_maintenance_cost", "fieldtype": "Currency", "width": 160},
		{"label": "Total Operating Cost", "fieldname": "total_operating_cost", "fieldtype": "Currency", "width": 160},
		{"label": "Cost per KM", "fieldname": "cost_per_km", "fieldtype": "Currency", "width": 120}
	]

	company = filters.get("company") if filters else None
	data = analytics_service.get_vehicle_health_summary(company, limit=100)

	return columns, data
