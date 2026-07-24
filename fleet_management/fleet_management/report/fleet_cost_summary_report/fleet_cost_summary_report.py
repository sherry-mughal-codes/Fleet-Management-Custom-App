"""
Fleet Cost Summary Script Report Implementation
Fleet Management System
"""

import frappe
from fleet_management.services.fleet_cost_service import FleetCostService

cost_service = FleetCostService()


def execute(filters=None):
	columns = [
		{"label": "Company", "fieldname": "company", "fieldtype": "Link", "options": "Company", "width": 160},
		{"label": "Period", "fieldname": "period", "fieldtype": "Data", "width": 140},
		{"label": "Total Fuel Cost", "fieldname": "total_fuel_cost", "fieldtype": "Currency", "width": 160},
		{"label": "Total Fuel (L)", "fieldname": "total_fuel_liters", "fieldtype": "Float", "width": 140},
		{"label": "Total Maintenance Cost", "fieldname": "total_maintenance_cost", "fieldtype": "Currency", "width": 180},
		{"label": "Total Operating Cost", "fieldname": "total_fleet_operating_cost", "fieldtype": "Currency", "width": 180}
	]

	company = filters.get("company") if filters else None
	data = [cost_service.calculate_company_cost(company)]

	return columns, data
