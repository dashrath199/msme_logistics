frappe.query_reports["Cost Per Delivery by Transporter"] = {
    "filters": [
        {
            "fieldname": "transporter",
            "label": __("Transporter"),
            "fieldtype": "Link",
            "options": "Transporter",
        },
        {
            "fieldname": "from_date",
            "label": __("From Date"),
            "fieldtype": "Date",
        },
        {
            "fieldname": "to_date",
            "label": __("To Date"),
            "fieldtype": "Date",
        },
    ],
};
