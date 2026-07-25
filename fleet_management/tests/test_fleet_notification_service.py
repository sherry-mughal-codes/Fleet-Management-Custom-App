"""
Unit Tests for Fleet Notification Service & Extension Hooks
Fleet Management System
"""

import pytest
from fleet_management.notifications.service import FleetNotificationService, NotificationService
from fleet_management.enums import NotificationType


def test_notification_service_authorized_recipients():
	"""Verify recipient resolution for Fleet Manager role."""
	recipients = FleetNotificationService.get_authorized_recipients("Fleet Manager")
	assert isinstance(recipients, list)
	assert len(recipients) > 0


def test_notification_dispatch_sync():
	"""Verify synchronous notification dispatch logic."""
	res = FleetNotificationService.dispatch(
		notification_type=NotificationType.MAINTENANCE_DUE,
		recipients=["test_manager@example.com"],
		subject="Test Notification",
		message="This is a test notification payload.",
		enqueue_background=False
	)
	assert res is True


def test_channel_extension_stubs():
	"""Verify future channel extension stubs return skipped status gracefully."""
	sms_res = FleetNotificationService.send_sms(["+1234567890"], "Test SMS")
	assert sms_res["status"] == "skipped"
	assert sms_res["channel"] == "sms"

	wa_res = FleetNotificationService.send_whatsapp(["+1234567890"], "Test WhatsApp")
	assert wa_res["status"] == "skipped"
	assert wa_res["channel"] == "whatsapp"

	push_res = FleetNotificationService.send_push(["user123"], "Test Push")
	assert push_res["status"] == "skipped"
	assert push_res["channel"] == "push"
