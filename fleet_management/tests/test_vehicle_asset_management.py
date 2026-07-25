"""
Unit Tests for Vehicle Digital Asset & Document Management
Fleet Management System
"""

from fleet_management.fleet_management.doctype.vehicle_document_detail.vehicle_document_detail import (
	VehicleDocumentDetail,
)
from fleet_management.fleet_management.doctype.vehicle_image_detail.vehicle_image_detail import (
	VehicleImageDetail,
)
from fleet_management.validators.vehicle_asset_validator import (
	VehicleAssetValidator,
	enforce_single_primary_image,
)


def test_asset_validator_document_expiry_valid():
	payload = {
		"documents": [
			{
				"document_type": "Registration",
				"document_number": "REG-1001",
				"issue_date": "2026-01-01",
				"expiry_date": "2027-01-01",
				"attachment": "/files/reg.pdf",
				"status": "Active"
			}
		],
		"images": []
	}
	validator = VehicleAssetValidator(payload)
	assert validator.validate() is True


def test_asset_validator_document_expiry_invalid():
	payload = {
		"documents": [
			{
				"document_type": "Registration",
				"document_number": "REG-1001",
				"issue_date": "2026-06-01",
				"expiry_date": "2026-01-01",
				"attachment": "/files/reg.pdf",
				"status": "Active"
			}
		],
		"images": []
	}
	validator = VehicleAssetValidator(payload)
	assert validator.validate() is False
	assert any("ASSET-001" in err for err in validator.errors)


def test_asset_validator_active_attachment_required():
	payload = {
		"documents": [
			{
				"document_type": "Insurance",
				"document_number": "INS-2002",
				"issue_date": "2026-01-01",
				"expiry_date": "2027-01-01",
				"attachment": None,
				"status": "Active"
			}
		],
		"images": []
	}
	validator = VehicleAssetValidator(payload)
	assert validator.validate() is False
	assert any("ASSET-003" in err for err in validator.errors)


def test_asset_validator_duplicate_document_number():
	payload = {
		"documents": [
			{
				"document_type": "Registration",
				"document_number": "REG-1001",
				"attachment": "/files/reg1.pdf",
				"status": "Active"
			},
			{
				"document_type": "Registration",
				"document_number": "REG-1001",
				"attachment": "/files/reg2.pdf",
				"status": "Active"
			}
		],
		"images": []
	}
	validator = VehicleAssetValidator(payload)
	assert validator.validate() is False
	assert any("ASSET-004" in err for err in validator.errors)


def test_enforce_single_primary_image():
	img1 = VehicleImageDetail({"title": "Front", "image": "/files/front.jpg", "is_primary": 1})
	img2 = VehicleImageDetail({"title": "Side", "image": "/files/side.jpg", "is_primary": 1})
	img3 = VehicleImageDetail({"title": "Rear", "image": "/files/rear.jpg", "is_primary": 0})

	images = [img1, img2, img3]
	enforce_single_primary_image(images)

	assert img1.is_primary == 1
	assert img2.is_primary == 0
	assert img3.is_primary == 0


def test_vehicle_document_detail_days_remaining():
	doc = VehicleDocumentDetail({
		"document_type": "Insurance",
		"expiry_date": "2099-12-31"
	})
	assert doc.get_days_until_expiry() > 0
	assert doc.is_expired() is False
