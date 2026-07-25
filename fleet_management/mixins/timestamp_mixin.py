from frappe.utils import now_datetime


class TimestampMixin:

    """
    Base mixin for timestamp tracking.
    """

    def before_insert(self):
        if hasattr(self, "created_at"):
            self.created_at = now_datetime()

        if hasattr(super(), "before_insert"):
            super().before_insert()

    def validate(self):
        if hasattr(self, "updated_at"):
            self.updated_at = now_datetime()

        if hasattr(super(), "validate"):
            super().validate()

    def days_since_creation(self) -> int:
        """
        Returns number of days since document creation.
        """
        if not getattr(self, "creation", None):
            return 0

        delta = now_datetime() - self.creation
        return delta.days
