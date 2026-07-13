import frappe
from frappe import _
from frappe.utils import nowdate


def check_pending_dispatches():
    """Daily job: notify Dispatch Manager about trips still in Planned status past their dispatch date."""
    overdue_trips = frappe.db.get_all(
        "Delivery Trip",
        filters={
            "trip_status": "Planned",
            "planned_dispatch_date": ("<", nowdate()),
        },
        fields=["name", "planned_dispatch_date", "transporter"],
    )

    for trip in overdue_trips:
        frappe.publish_realtime(
            "msme_logistics:pending_dispatch",
            {
                "trip_name": trip.name,
                "planned_date": str(trip.planned_dispatch_date),
                "message": _(
                    "Trip {0} (Transporter: {1}) was planned for {2} but has not been dispatched."
                ).format(trip.name, trip.transporter, trip.planned_dispatch_date),
            },
            after_commit=True,
        )

    if overdue_trips:
        frappe.log_error(
            title=_("Pending Dispatches Check"),
            message=_("{0} trips overdue for dispatch.").format(len(overdue_trips)),
        )

    return len(overdue_trips)
