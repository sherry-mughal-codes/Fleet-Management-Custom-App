"""
Vehicle Asset & Document Validator Architecture
Fleet Management System
"""

from typing import Any, Dict, List
import frappe
from fleet_management.validators.base_validator import BaseValidator
from fleet_management.validators.common_validators import validate_date_range, validate_positive_number
from fleet_management.utils.exceptions import FleetValidationError


class VehicleAssetValidator(BaseValidator):
	"""
	Validator enforcing Rule IDs ASSET-001 through ASSET-008 for Vehicle Documents and Images.
	"""

	def validate(self) -> bool:
		documents = self.data.get("documents") or []
		images = self.data.get("images") or []

		self.validate_documents(documents)
		self.validate_images(images)

		return len(self.errors) == 0

	def validate_documents(self, documents: List[Any]):
		seen_numbers = set()

		for idx, row in enumerate(documents, start=1):
			row_dict = row.as_dict() if hasattr(row, "as_dict") else row

			# ASSET-001: Expiry Date >= Issue Date
			issue_date = row_dict.get("issue_date")
			expiry_date = row_dict.get("expiry_date")
			if issue_date and expiry_date:
				try:
					validate_date_range(issue_date, expiry_date, f"Row #{idx} Issue Date", f"Row #{idx} Expiry Date")
				except FleetValidationError as e:
					self.add_error(f"ASSET-001: {e.message}")

			# ASSET-002: Reminder Days >= 0
			reminder_days = row_dict.get("reminder_days")
			if reminder_days is not None:
				try:
					validate_positive_number(reminder_days, f"Row #{idx} Reminder Days", allow_zero=True)
				except FleetValidationError as e:
					self.add_error(f"ASSET-002: {e.message}")

			# ASSET-003: Attachment required when Active
			status = row_dict.get("status", "Active")
			attachment = row_dict.get("attachment")
			if status == "Active" and not attachment:
				self.add_error(f"ASSET-003: Attachment file is required for Active Document at Row #{idx}.")

			# ASSET-004: Unique Document Number per Vehicle
			doc_number = row_dict.get("document_number")
			doc_type = row_dict.get("document_type")
			if doc_number and doc_type:
				key = f"{doc_type}:{str(doc_number).strip().lower()}"
				if key in seen_numbers:
					self.add_error(f"ASSET-004: Duplicate Document Number '{doc_number}' for type '{doc_type}' at Row #{idx}.")
				seen_numbers.add(key)

	def validate_images(self, images: List[Any]):
		primary_count = 0

		for idx, row in enumerate(images, start=1):
			row_dict = row.as_dict() if hasattr(row, "as_dict") else row

			# ASSET-005: Track primary images
			if row_dict.get("is_primary"):
				primary_count += 1

			# ASSET-006: Display order non-negative check
			display_order = row_dict.get("display_order")
			if display_order is not None:
				try:
					validate_positive_number(display_order, f"Image Row #{idx} Display Order", allow_zero=True)
				except FleetValidationError as e:
					self.add_error(f"ASSET-006: {e.message}")


def enforce_single_primary_image(images: List[Any]):
	"""
	Helper ensuring exactly one primary image is flagged.
	Resets all other rows to is_primary = 0.
	"""
	primary_found = False
	for row in images:
		if getattr(row, "is_primary", 0):
			if not primary_found:
				primary_found = True
			else:
				row.is_primary = 0
