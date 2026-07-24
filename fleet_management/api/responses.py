"""
Standard API Response Helpers
Fleet Management System
"""

from typing import Any, Dict, List, Optional
from fleet_management.utils.helpers import format_api_response


def success_response(data: Any = None, message: str = "Operation completed successfully.", meta: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
	"""Return standard success API envelope."""
	return format_api_response(data=data, message=message, status_code=200, meta=meta)


def error_response(message: str = "An error occurred.", status_code: int = 400, details: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
	"""Return standard error API envelope."""
	return format_api_response(data=details, message=message, status_code=status_code)


def paginated_response(items: List[Any], total_count: int, page: int = 1, page_length: int = 20, message: str = "Records retrieved successfully.") -> Dict[str, Any]:
	"""Return paginated list API envelope."""
	total_pages = (total_count + page_length - 1) // page_length if page_length > 0 else 1
	meta = {
		"page": page,
		"page_length": page_length,
		"total_count": total_count,
		"total_pages": total_pages,
		"has_next": page < total_pages,
		"has_prev": page > 1
	}
	return format_api_response(data=items, message=message, status_code=200, meta=meta)


def validation_error_response(errors: List[str], message: str = "Validation failed for request payload.") -> Dict[str, Any]:
	"""Return standard validation error API envelope."""
	return format_api_response(data={"errors": errors}, message=message, status_code=422)
