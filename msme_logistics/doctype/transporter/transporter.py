import frappe
from frappe.model.document import Document


class Transporter(Document):
    """Registered transporter with vehicle types and service areas.

    Extends the Supplier concept — each Transporter links to an ERPNext Supplier
    for financial / purchasing integration.
    """

    def validate(self):
        self._validate_rate_cards()
        self._validate_service_areas()

    def _validate_rate_cards(self):
        """Ensure at least one vehicle type with rate is defined."""
        if not self.vehicle_types:
            frappe.throw(
                frappe._("At least one vehicle type with rate per km is required"),
                title=frappe._("Missing Rate Card"),
            )

    def _validate_service_areas(self):
        """Validate pincode ranges in service areas."""
        for area in self.service_areas:
            if area.pincode_from and area.pincode_to:
                if int(area.pincode_from) > int(area.pincode_to):
                    frappe.throw(
                        frappe._(
                            "Row #{0}: Pincode From ({1}) must be less than or equal to Pincode To ({2})"
                        ).format(area.idx, area.pincode_from, area.pincode_to),
                        title=frappe._("Invalid Pincode Range"),
                    )

    def before_save(self):
        """Derive transporter_name from linked supplier if not set explicitly."""
        if not self.transporter_name and self.supplier:
            supplier_name = frappe.db.get_value("Supplier", self.supplier, "supplier_name")
            if supplier_name:
                self.transporter_name = supplier_name
