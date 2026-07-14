frappe.query_reports["SLA Compliance by Transporter"] = {
    "filters": [
        {
            "fieldname": "from_date",
            "label": __("From Date"),
            "fieldtype": "Date",
            "default": frappe.datetime.add_days(frappe.datetime.get_today(), -30),
        },
        {
            "fieldname": "to_date",
            "label": __("To Date"),
            "fieldtype": "Date",
            "default": frappe.datetime.get_today(),
        },
        {
            "fieldname": "transporter",
            "label": __("Transporter"),
            "fieldtype": "Link",
            "options": "Transporter",
        },
    ],
    "formatter": function (value, row, column, data, default_formatter) {
        value = default_formatter(value, row, column, data);
        if (column.fieldname === "compliance_pct" && data) {
            if (data.compliance_pct < 60) {
                value = `<span style="color:red;font-weight:bold">${value}</span>`;
            } else if (data.compliance_pct < 80) {
                value = `<span style="color:orange;font-weight:bold">${value}</span>`;
            } else {
                value = `<span style="color:green;font-weight:bold">${value}</span>`;
            }
        }
        return value;
    },
};
