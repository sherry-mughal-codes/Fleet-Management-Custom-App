"""
Audit Mixin
Fleet Management System
"""

from fleet_management.permissions.audit import audit_document_change


class AuditMixin:
	"""
	Mixin automatically attaching audit tracking on document update and submit events.
	"""

	def on_update(self):
		audit_document_change(self, "on_update")
		if hasattr(super(), "on_update"):
			super().on_update()

	def on_submit(self):
		audit_document_change(self, "on_submit")
		if hasattr(super(), "on_submit"):
			super().on_submit()
