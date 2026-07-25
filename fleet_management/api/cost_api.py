"""
Fleet Cost Domain Whitelisted API Endpoints Implementation
Fleet Management System
"""

from typing import Any, Dict

from fleet_management.api.base import api_endpoint
from fleet_management.api.responses import success_response
from fleet_management.services.fleet_cost_service import FleetCostService

cost_service = FleetCostService()


@api_endpoint(allow_guest=False)
def get_vehicle_cost_summary_api(vehicle: str) -> Dict[str, Any]:
	"""Whitelisted API endpoint for retrieving vehicle cost summary."""
	summary = cost_service.calculate_vehicle_cost(vehicle)
	return success_response(data=summary, message="Vehicle cost summary retrieved successfully.")


@api_endpoint(allow_guest=False)
def get_assignment_cost_summary_api(assignment: str) -> Dict[str, Any]:
	"""Whitelisted API endpoint for retrieving assignment operating cost summary."""
	summary = cost_service.calculate_assignment_cost(assignment)
	return success_response(data=summary, message="Assignment cost summary retrieved successfully.")


@api_endpoint(allow_guest=False)
def get_company_cost_summary_api(company: str | None = None, period: str = "lifetime") -> Dict[str, Any]:
	"""Whitelisted API endpoint for retrieving company fleet cost summary."""
	summary = cost_service.calculate_company_cost(company, period)
	return success_response(data=summary, message="Company cost summary retrieved successfully.")


@api_endpoint(allow_guest=False)
def get_cost_per_km_api(vehicle: str) -> Dict[str, Any]:
	"""Whitelisted API endpoint for calculating vehicle cost per kilometer."""
	cpkm = cost_service.calculate_cost_per_km(vehicle)
	return success_response(data={"vehicle": vehicle, "cost_per_km": cpkm}, message="Cost per kilometer calculated successfully.")


@api_endpoint(allow_guest=False)
def get_monthly_cost_api(company: str | None = None, year: int | None = None, month: int | None = None) -> Dict[str, Any]:
	"""Whitelisted API endpoint for monthly company cost summary."""
	summary = cost_service.calculate_monthly_cost(company, year, month)
	return success_response(data=summary, message="Monthly cost summary retrieved successfully.")


@api_endpoint(allow_guest=False)
def get_yearly_cost_api(company: str | None = None, year: int | None = None) -> Dict[str, Any]:
	"""Whitelisted API endpoint for yearly company cost summary."""
	summary = cost_service.calculate_yearly_cost(company, year)
	return success_response(data=summary, message="Yearly cost summary retrieved successfully.")
