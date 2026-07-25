import frappe
import pytest


@pytest.fixture(scope="session", autouse=True)
def initialize_frappe():
	"""Initializes Frappe context and database connection for pytest suite."""
	if not getattr(frappe, "db", None):
		frappe.init(site="fleet.localhost", sites_path="sites")
		frappe.connect()
	yield




@pytest.fixture(scope="session")
def mock_frappe_context():
	"""Session fixture initializing mock environment context for standalone unit tests."""
	return {
		"site": "fleet.localhost",
		"user": "Administrator"
	}

