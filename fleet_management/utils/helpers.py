"""
Reusable Helper Architecture
Fleet Management System
"""

import datetime
import functools
import re
from typing import Any, Callable, Dict

import frappe

from fleet_management.utils.logger import get_logger

logger = get_logger("fleet_management.helpers")


# --- JSON & Response Helpers ---

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
	meta: Dict[str, Any] | None = None
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
	"""Method decorator for caching method execution results in Redis."""
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


# --- Date & Time Helpers ---

def get_days_between(start_date: Any, end_date: Any) -> int:
	"""Calculate difference in days between two dates."""
	s = frappe.utils.getdate(start_date)
	e = frappe.utils.getdate(end_date)
	return (e - s).days


def add_days_to_date(date_val: Any, days: int) -> datetime.date:
	"""Add or subtract days from a given date."""
	base = frappe.utils.getdate(date_val)
	return base + datetime.timedelta(days=days)


def is_past_date(date_val: Any) -> bool:
	"""Check if date is earlier than today."""
	target = frappe.utils.getdate(date_val)
	today = frappe.utils.getdate(frappe.utils.nowdate())
	return target < today


def is_future_date(date_val: Any) -> bool:
	"""Check if date is later than today."""
	target = frappe.utils.getdate(date_val)
	today = frappe.utils.getdate(frappe.utils.nowdate())
	return target > today


# --- Number Helpers ---

def round_currency(val: float, precision: int = 2) -> float:
	"""Round float to currency precision."""
	return round(float(val or 0), precision)


def calculate_percentage(part: float, total: float, precision: int = 2) -> float:
	"""Safely calculate percentage without ZeroDivisionError."""
	if not total or total == 0:
		return 0.0
	return round((part / total) * 100, precision)


def safe_float(val: Any, default: float = 0.0) -> float:
	"""Safely convert value to float."""
	try:
		return float(val)
	except (ValueError, TypeError):
		return default


# --- String Helpers ---

def slugify(text: str) -> str:
	"""Convert string into clean slug format."""
	text = text.lower().strip()
	text = re.sub(r"[^\w\s-]", "", text)
	return re.sub(r"[\s_-]+", "-", text)


def sanitize_string(text: str) -> str:
	"""Remove special tags or non-printable characters."""
	if not text:
		return ""
	return re.sub(r"<[^>]*>", "", str(text)).strip()


def truncate(text: str, max_length: int = 50, suffix: str = "...") -> str:
	"""Truncate long string gracefully."""
	if not text or len(text) <= max_length:
		return text or ""
	return text[: max_length - len(suffix)] + suffix


# --- Document Helpers ---

def get_doc_or_none(doctype: str, name: str) -> Any | None:
	"""Safely retrieve Document or None if it doesn't exist."""
	if not doctype or not name:
		return None
	try:
		if frappe.db.exists(doctype, name):
			return frappe.get_doc(doctype, name)
	except Exception:
		pass
	return None


def has_field(doctype: str, fieldname: str) -> bool:
	"""Check if Frappe DocType contains a given field."""
	try:
		meta = frappe.get_meta(doctype)
		return meta.has_field(fieldname)
	except Exception:
		return False


# --- Formatting Helpers ---

def format_distance(distance_val: int | float, unit: str = "KM") -> str:
	"""Format distance with units."""
	return f"{distance_val:,.0f} {unit}"


def format_fuel(fuel_val: int | float, unit: str = "Liters") -> str:
	"""Format fuel quantity with units."""
	return f"{fuel_val:,.2f} {unit}"
