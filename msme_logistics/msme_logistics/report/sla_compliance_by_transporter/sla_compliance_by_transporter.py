import frappe
from frappe import _


def execute(filters=None):
    columns = [
        {"label": _("Transporter"), "fieldname": "transporter", "fieldtype": "Link", "options": "Transporter", "width": 200},
        {"label": _("Total Stops"), "fieldname": "total_stops", "fieldtype": "Int", "width": 100},
        {"label": _("On-Time Stops"), "fieldname": "on_time_stops", "fieldtype": "Int", "width": 120},
        {"label": _("Delayed Stops"), "fieldname": "delayed_stops", "fieldtype": "Int", "width": 120},
        {"label": _("Failed Stops"), "fieldname": "failed_stops", "fieldtype": "Int", "width": 100},
        {"label": _("SLA Compliance %"), "fieldname": "compliance_pct", "fieldtype": "Percent", "width": 140},
        {"label": _("Avg Delay (min)"), "fieldname": "avg_delay_min", "fieldtype": "Float", "width": 130},
    ]

    data = frappe.db.sql(
        """
        SELECT
            trip.transporter,
            COUNT(ds.name) AS total_stops,
            SUM(CASE
                WHEN ds.status = 'Delivered'
                    AND ds.delivery_window_start IS NOT NULL
                    AND ds.delivery_window_end IS NOT NULL
                    AND TIME(ds.actual_arrival_time) BETWEEN ds.delivery_window_start AND ds.delivery_window_end
                THEN 1 ELSE 0
            END) AS on_time_stops,
            SUM(CASE
                WHEN ds.status = 'Delivered'
                    AND ds.delivery_window_end IS NOT NULL
                    AND TIME(ds.actual_arrival_time) > ds.delivery_window_end
                THEN 1 ELSE 0
            END) AS delayed_stops,
            SUM(CASE WHEN ds.status = 'Failed' THEN 1 ELSE 0 END) AS failed_stops
        FROM
            `tabDelivery Stop` ds
        INNER JOIN
            `tabDelivery Trip` trip ON trip.name = ds.parent
        WHERE
            ds.docstatus < 2
            {conditions}
        GROUP BY
            trip.transporter
        ORDER BY
            compliance_pct DESC
        """.format(conditions=_get_conditions(filters)),
        filters,
        as_dict=1,
    )

    for row in data:
        row.compliance_pct = (row.on_time_stops / row.total_stops * 100) if row.total_stops else 0
        row.delayed_stops = row.get("delayed_stops") or 0
        row.failed_stops = row.get("failed_stops") or 0

    chart = {
        "data": {
            "labels": [d.transporter for d in data],
            "datasets": [
                {"name": _("SLA Compliance %"), "values": [d.compliance_pct for d in data]},
            ],
        },
        "type": "bar",
        "colors": ["#4F46E5"],
    }

    return columns, data, None, chart


def _get_conditions(filters):
    conditions = []
    if filters and filters.get("from_date"):
        conditions.append("trip.planned_dispatch_date >= %(from_date)s")
    if filters and filters.get("to_date"):
        conditions.append("trip.planned_dispatch_date <= %(to_date)s")
    if filters and filters.get("transporter"):
        conditions.append("trip.transporter = %(transporter)s")
    return " AND ".join(conditions) if conditions else ""
