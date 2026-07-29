"""
Enterprise API Layer Architecture
Fleet Management System
"""

import functools
import time
from typing import Callable

import frappe

from fleet_management.utils.exceptions import FleetManagementError
from fleet_management.utils.helpers import format_api_response
from fleet_management.utils.logger import get_logger

logger = get_logger("fleet_management.api")

def api_endpoint(allow_guest: bool = False, rate_limit: bool = True, roles: list = None):
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
				if roles and hasattr(frappe, "get_roles") and hasattr(frappe, "session") and getattr(frappe.session, "user", None) != "Administrator":
					user_roles = set(frappe.get_roles())
					if not any(r in user_roles for r in roles):
						raise FleetManagementError("Permission Denied: Insufficient Role Privileges", status_code=403)

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


def boot_session(bootinfo):
	"""
	Frappe boot_session hook populating client boot data.
	"""
	try:
		from fleet_management.constants import SYSTEM_VERSION
		version = SYSTEM_VERSION
	except Exception:
		version = "1.0.0"

	bootinfo.fleet_management_config = {
		"version": version,
		"status": "ready"
	}
