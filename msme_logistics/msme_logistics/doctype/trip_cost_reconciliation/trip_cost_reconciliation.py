import frappe
from frappe.model.document import Document


class TripCostReconciliation(Document):
    """Per-trip cost reconciliation for transporter payout negotiation.

    Computes cost_per_stop as:
        (fuel_cost + toll_charges + other_charges + transporter_payout) / total_stops
    """

    def validate(self):
        self._fetch_trip_data()
        self._compute_cost_per_stop()

    def _fetch_trip_data(self):
        """Pull total_stops from the linked Delivery Trip."""
        if self.delivery_trip:
            self.total_stops = frappe.db.get_value(
                "Delivery Trip", self.delivery_trip, "total_stops"
            ) or 0

    def _compute_cost_per_stop(self):
        """Compute cost_per_stop as total cost divided by number of stops."""
        if self.total_stops <= 0:
            self.cost_per_stop = 0
            return

        total_cost = (
            (self.fuel_cost or 0.0)
            + (self.toll_charges or 0.0)
            + (self.other_charges or 0.0)
            + (self.transporter_payout or 0.0)
        )

        self.cost_per_stop = round(total_cost / self.total_stops, 2)
