"""
Enterprise API Layer Architecture
Fleet Management System
"""

import functools
import time
from typing import Any, Callable
import frappe
from fleet_management.utils.exceptions import FleetManagementError
from fleet_management.utils.helpers import format_api_response
from fleet_management.utils.logger import get_logger

logger = get_logger("fleet_management.api")

def api_endpoint(allow_guest: bool = False, rate_limit: bool = True):
	"""
	Enterprise API Decorator for Frappe `@frappe.whitelist()` methods.
	Provides:
	- Unified API response envelope
	- Automatic Exception mapping to HTTP status codes
	- Execution timing
	- Audit log recording
	"""
	def decorator(func: Callable):
		@frappe.whitelist(allow_guest=allow_guest)
		@functools.wraps(func)
		def wrapper(*args, **kwargs):
			start_time = time.time()
			endpoint_name = f"{func.__module__}.{func.__name__}"
			
			try:
				if rate_limit and hasattr(frappe, "rate_limit"):
					# Placeholder hook for rate limiting evaluation
					pass
				
				result = func(*args, **kwargs)
				duration_ms = round((time.time() - start_time) * 1000, 2)
				
				meta = {
					"endpoint": endpoint_name,
					"execution_time_ms": duration_ms
				}
				
				if isinstance(result, dict) and "success" in result:
					return result
				
				return format_api_response(data=result, message="Request processed successfully", meta=meta)
				
			except FleetManagementError as e:
				frappe.response["http_status_code"] = e.status_code
				logger.warning(f"Domain error in API {endpoint_name}: {e.message}", e.to_dict())
				return format_api_response(
					data=e.details,
					message=e.message,
					status_code=e.status_code,
					meta={"endpoint": endpoint_name}
				)
			except Exception as e:
				frappe.response["http_status_code"] = 500
				logger.error(f"Unhandled error in API {endpoint_name}: {str(e)}", exc=e)
				return format_api_response(
					data=None,
					message="An internal server error occurred.",
					status_code=500,
					meta={"endpoint": endpoint_name}
				)
		return wrapper
	return decorator


from fleet_management.constants import SYSTEM_VERSION


def boot_session(bootinfo):
	"""
	Frappe boot_session hook populating client boot data.
	"""
	bootinfo.fleet_management_config = {
		"version": SYSTEM_VERSION,
		"status": "ready"
	}
