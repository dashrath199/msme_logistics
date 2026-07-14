import frappe
from frappe.model.document import Document


class DeliveryStop(Document):
    """Child table for Delivery Trip — individual stop with POD and SLA tracking."""

    def validate(self):
        """Business rule: delivery_window_end must be after delivery_window_start."""
        if self.delivery_window_start and self.delivery_window_end:
            if self.delivery_window_end <= self.delivery_window_start:
                frappe.throw(
                    frappe._("Delivery window end must be after delivery window start")
                )

    def before_save(self):
        """Auto-set actual_arrival_time on status change to terminal states."""
        terminal_states = {"Delivered", "Failed", "Rescheduled"}
        if self.status in terminal_states and not self.actual_arrival_time:
            self.actual_arrival_time = frappe.utils.now_datetime()
