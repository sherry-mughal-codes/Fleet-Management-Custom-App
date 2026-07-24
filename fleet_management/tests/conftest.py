"""
Pytest Fixtures for Fleet Management Test Architecture
"""

import pytest

@pytest.fixture(scope="session")
def mock_frappe_context():
	"""Session fixture initializing mock environment context for standalone unit tests."""
	return {
		"site": "fleet.localhost",
		"user": "Administrator"
	}
