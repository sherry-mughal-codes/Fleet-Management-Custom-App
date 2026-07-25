"""
Base Fleet Document Controller Architecture
Fleet Management System
"""

from frappe.model.document import Document

from fleet_management.mixins.audit_mixin import AuditMixin
from fleet_management.mixins.permission_mixin import PermissionMixin
from fleet_management.mixins.status_mixin import StatusMixin
from fleet_management.mixins.timestamp_mixin import TimestampMixin
from fleet_management.utils.logger import get_logger

logger = get_logger("fleet_management.base_document")


class BaseFleetDocument(Document, TimestampMixin, AuditMixin, StatusMixin, PermissionMixin):
	"""
	Abstract Base Class for all Fleet Management DocType controllers.
	Combines Document lifecycle hooks with audit, status, timestamp, and permission mixins.
	"""

	def __init__(self, *args, **kwargs):
		if args and isinstance(args[0], dict):
			if "doctype" not in args[0] and getattr(self, "doctype", None):
				args[0]["doctype"] = self.doctype
		super().__init__(*args, **kwargs)

	def validate(self):

		super().validate()
		self.before_validate_hook()

	def before_validate_hook(self):
		"""Extension hook for subclasses."""
		pass

	def on_update(self):
		super().on_update()
		logger.info(f"Document updated: {self.doctype}/{self.name}")

	def on_trash(self):
		super().on_trash()
		logger.info(f"Document deleted: {self.doctype}/{self.name}")
