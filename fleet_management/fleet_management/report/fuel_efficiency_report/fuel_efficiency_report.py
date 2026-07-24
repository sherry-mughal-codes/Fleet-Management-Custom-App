"""
Fuel Efficiency Script Report Implementation
Fleet Management System
"""

import frappe
from fleet_management.services.fuel_service import FuelService

fuel_service = FuelService()


def execute(filters=None):
	columns = [
		{"label": "Fuel Entry", "fieldname": "name", "fieldtype": "Link", "options": "Fuel Entry", "width": 140},
		{"label": "Vehicle", "fieldname": "vehicle", "fieldtype": "Link", "options": "Vehicle", "width": 140},
		{"label": "Fuel Date", "fieldname": "fuel_date", "fieldtype": "Date", "width": 120},
		{"label": "Fuel Quantity (L)", "fieldname": "fuel_qty", "fieldtype": "Float", "width": 140},
		{"label": "Total Cost", "fieldname": "total_cost", "fieldtype": "Currency", "width": 120},
		{"label": "Odometer (KM)", "fieldname": "odometer", "fieldtype": "Float", "width": 140},
		{"label": "Fuel Average (KM/L)", "fieldname": "fuel_average", "fieldtype": "Float", "width": 160},
		{"label": "Status", "fieldname": "status", "fieldtype": "Data", "width": 120}
	]

	vehicle = filters.get("vehicle") if filters else None
	data = fuel_service.get_vehicle_history(vehicle, limit=100) if vehicle else []

	return columns, data
