"""
Infrastructure Foundation Unit Tests
Fleet Management System
"""

import pytest
from fleet_management.utils.logger import get_logger
from fleet_management.utils.exceptions import (
	FleetManagementError,
	FleetValidationError,
	FleetPermissionError,
	FleetNotFoundError,
)
from fleet_management.utils.helpers import format_api_response, safe_json_parse
from fleet_management.validators.base_validator import BaseValidator
from fleet_management.services.base_service import BaseService
from fleet_management.permissions.evaluator import PermissionEvaluator


class DummyValidator(BaseValidator):
	def validate(self) -> bool:
		if "name" not in self.data:
			self.add_error("Name is required.")
			return False
		return True


def test_logger_initialization():
	logger = get_logger("test_module")
	assert logger is not None
	assert logger.module_name == "test_module"


def test_exception_hierarchy():
	err = FleetValidationError("Invalid payload", details={"field": "vin"})
	assert err.status_code == 422
	assert err.message == "Invalid payload"
	assert err.to_dict()["status_code"] == 422

	perm_err = FleetPermissionError()
	assert perm_err.status_code == 403

	not_found = FleetNotFoundError()
	assert not_found.status_code == 404


def test_api_response_envelope():
	response = format_api_response(data={"id": "V-001"}, message="Fetched", status_code=200)
	assert response["success"] is True
	assert response["status_code"] == 200
	assert response["data"]["id"] == "V-001"


def test_base_validator():
	valid_data = {"name": "Fleet Alpha"}
	validator = DummyValidator(valid_data)
	assert validator.validate() is True

	invalid_data = {}
	invalid_validator = DummyValidator(invalid_data)
	assert invalid_validator.validate() is False
	assert "Name is required." in invalid_validator.errors


def test_json_parse_helper():
	assert safe_json_parse('{"key": "value"}') == {"key": "value"}
	assert safe_json_parse('invalid json', default={}) == {}
