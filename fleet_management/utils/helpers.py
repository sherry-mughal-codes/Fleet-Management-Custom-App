"""
Reusable Helper Architecture
Fleet Management System
"""

import functools
from typing import Any, Callable, Dict, Optional
import frappe
from fleet_management.utils.logger import get_logger

logger = get_logger("fleet_management.helpers")

def safe_json_parse(value: str, default: Any = None) -> Any:
	"""Safely parse JSON string into dict or list."""
	if not value:
		return default
	try:
		return frappe.parse_json(value)
	except Exception as e:
		logger.warning("JSON parse failure", {"error": str(e), "value": value})
		return default


def format_api_response(
	data: Any = None,
	message: str = "Success",
	status_code: int = 200,
	meta: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
	"""Standardized envelope for all Frappe API endpoints."""
	return {
		"success": status_code >= 200 and status_code < 300,
		"status_code": status_code,
		"message": message,
		"data": data,
		"meta": meta or {}
	}


def cache_result(ttl_seconds: int = 300, key_prefix: str = "fleet_cache"):
	"""
	Method decorator for caching method execution results in Redis.
	"""
	def decorator(func: Callable):
		@functools.wraps(func)
		def wrapper(*args, **kwargs):
			cache_key = f"{key_prefix}:{func.__name__}:{hash(str(args) + str(kwargs))}"
			cached = frappe.cache().get_value(cache_key)
			if cached is not None:
				return cached
			result = func(*args, **kwargs)
			if result is not None:
				frappe.cache().set_value(cache_key, result, expires_in_sec=ttl_seconds)
			return result
		return wrapper
	return decorator
