import frappe
from frappe.model.document import Document


class DeliveryTrip(Document):
    """A delivery trip batches multiple delivery notes into a planned route.

    Workflow: Planned → Dispatched → In Transit → Completed → Reconciled
    """

    def validate(self):
        self._validate_stops()
        self._validate_delivery_notes()
        self._validate_pod_on_completion()

    def before_save(self):
        self._update_total_stops()

    def on_update(self):
        """Trigger notifications on status changes."""
        if self.trip_status == "In Transit":
            self._notify_trip_in_transit()
        elif self.trip_status == "Completed":
            self._notify_trip_completed()

    # ------------------------------------------------------------------
    # Validators
    # ------------------------------------------------------------------

    def _validate_stops(self):
        """Ensure at least one delivery stop and no duplicate sequences."""
        if not self.delivery_stops:
            frappe.throw(
                frappe._("At least one delivery stop is required"),
                title=frappe._("Missing Stops"),
            )

        seqs = [stop.sequence_no for stop in self.delivery_stops if stop.sequence_no]
        if len(seqs) != len(set(seqs)):
            frappe.throw(
                frappe._("Duplicate sequence numbers found in delivery stops"),
                title=frappe._("Validation Error"),
            )

    def _validate_delivery_notes(self):
        """Ensure at least one linked delivery note."""
        if not self.linked_delivery_notes:
            frappe.throw(
                frappe._("At least one linked Delivery Note is required"),
                title=frappe._("Missing Delivery Notes"),
            )

    def _validate_pod_on_completion(self):
        """
        Block the transition to Completed if any Delivered stop is missing its POD.
        This is the critical business rule: completed trips must have proof of delivery.
        """
        if self.trip_status != "Completed":
            return

        pod_missing = [
            stop.idx
            for stop in self.delivery_stops
            if stop.status == "Delivered" and not stop.pod_image and not stop.pod_signature
        ]

        if pod_missing:
            frappe.throw(
                frappe._(
                    "Cannot complete trip — POD missing for stop(s) #{0}. "
                    "Every delivered stop must have either a POD image or signature."
                ).format(", ".join(str(i) for i in pod_missing)),
                title=frappe._("Missing Proof of Delivery"),
            )

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _update_total_stops(self):
        """Keep the total_stops count in sync with the child table."""
        self.total_stops = len(self.delivery_stops)

    def _notify_trip_in_transit(self):
        """System notification when trip goes In Transit."""
        frappe.publish_realtime(
            "msme_logistics:trip_in_transit",
            {
                "trip_name": self.name,
                "transporter": self.transporter,
                "driver_name": self.driver_name,
            },
            after_commit=True,
        )

    def _notify_trip_completed(self):
        """System notification when trip is Completed."""
        frappe.publish_realtime(
            "msme_logistics:trip_completed",
            {
                "trip_name": self.name,
                "total_stops": self.total_stops,
            },
            after_commit=True,
        )
