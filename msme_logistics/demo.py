"""
msme_logistics — demo data generator.

Creates realistic demo records so users can immediately explore the app.

Usage on a site with the app installed:
    bench --site yoursitename.local execute msme_logistics.demo.after_install

Cleanup before uninstall:
    bench --site yoursitename.local execute msme_logistics.demo.before_uninstall
"""

import frappe
from frappe import _

# ---------------------------------------------------------------------------
# Demo data constants
# ---------------------------------------------------------------------------

DEMO_CUSTOMERS = [
    {
        "name": "New Delhi Electronics",
        "address_line1": "42, Connaught Place",
        "city": "Delhi",
        "pincode": "110001",
    },
    {
        "name": "Mumbai Pharma Distributors",
        "address_line1": "7, Andheri Industrial Estate",
        "city": "Mumbai",
        "pincode": "400001",
    },
    {
        "name": "Bangalore Retail Mart",
        "address_line1": "88, MG Road",
        "city": "Bangalore",
        "pincode": "560001",
    },
]

DEMO_WAREHOUSE = {
    "warehouse_name": "Logistics Hub - Main",
    "city": "Delhi",
}

DEMO_TRANSPORTER = {
    "transporter_name": "SwiftLogistics India",
    "contact_number": "+91-9876543210",
    "email": "dispatch@swiftlogistics.in",
    "vehicle_types": [
        {"vehicle_type": "Tata Ace", "capacity_kg": 750, "rate_per_km": 12},
        {"vehicle_type": "Bolero Pickup", "capacity_kg": 1500, "rate_per_km": 18},
        {"vehicle_type": "Eicher 14ft", "capacity_kg": 5000, "rate_per_km": 28},
    ],
    "service_areas": [
        {"pincode_from": "110001", "pincode_to": "110099", "area_name": "Delhi NCR"},
        {"pincode_from": "400001", "pincode_to": "400099", "area_name": "Mumbai Metro"},
        {"pincode_from": "560001", "pincode_to": "560099", "area_name": "Bangalore"},
    ],
}

DEMO_DRIVER = {
    "driver_name": "Rajesh Kumar",
    "driver_contact": "+91-9988776655",
    "vehicle_no": "DL-01-XX-1234",
}

DEMO_TRIP_STOPS = [
    {
        "customer": "New Delhi Electronics",
        "sequence_no": 1,
        "delivery_window_start": "09:00",
        "delivery_window_end": "11:00",
    },
    {
        "customer": "Mumbai Pharma Distributors",
        "sequence_no": 2,
        "delivery_window_start": "12:00",
        "delivery_window_end": "14:00",
    },
    {
        "customer": "Bangalore Retail Mart",
        "sequence_no": 3,
        "delivery_window_start": "15:00",
        "delivery_window_end": "17:00",
    },
]


# ---------------------------------------------------------------------------
# after_install — called by bench install-app
# ---------------------------------------------------------------------------


def after_install():
    """Create demo data on first install (idempotent)."""
    if frappe.db.exists("Transporter", DEMO_TRANSPORTER["transporter_name"]):
        frappe.log_error(
            title=_("MSME Logistics Demo"),
            message=_("Demo data already exists — skipping."),
        )
        return

    try:
        company = _get_default_company()

        _create_customers()
        _create_addresses(company)
        _create_warehouse(company)

        transporter = _create_transporter()
        _create_delivery_trip(transporter)

        frappe.db.commit()  # single commit at the end
        _print_success()

    except Exception:
        frappe.log_error(
            title=_("MSME Logistics Demo — Install Failed"),
            message=frappe.get_traceback(),
        )
        raise


# ---------------------------------------------------------------------------
# before_uninstall — clean up before removing the app
# ---------------------------------------------------------------------------


def before_uninstall():
    """Remove demo records created by this module (parent-to-child order)."""
    for doctype in ("Trip Cost Reconciliation", "Delivery Trip", "Transporter"):
        names = frappe.get_all(doctype, pluck="name")
        for name in names:
            try:
                frappe.delete_doc(doctype, name, force=True, ignore_permissions=True)
            except Exception:
                pass  # best-effort cleanup


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------


def _get_default_company():
    """Return the first company available on the site."""
    company = frappe.db.get_single_value("Global Defaults", "default_company")
    if company:
        return company

    companies = frappe.get_all("Company", pluck="name", limit=1)
    if companies:
        return companies[0]

    frappe.throw(
        _("No Company found. Create at least one Company before installing demo data.")
    )


def _create_customers():
    """Create demo Customers (idempotent)."""
    for cust in DEMO_CUSTOMERS:
        if frappe.db.exists("Customer", cust["name"]):
            continue
        doc = frappe.get_doc({
            "doctype": "Customer",
            "customer_name": cust["name"],
            "customer_type": "Company",
            "customer_group": _("All Customer Groups"),
            "territory": _("All Territories"),
        })
        doc.insert(ignore_permissions=True)


def _create_addresses(company):
    """Create demo Address records linked to each customer for route optimization."""
    for cust in DEMO_CUSTOMERS:
        if not frappe.db.exists("Customer", cust["name"]):
            continue

        addr_name = f"{cust['name']} - Demo"
        if frappe.db.exists("Address", addr_name):
            continue

        doc = frappe.get_doc({
            "doctype": "Address",
            "address_title": cust["name"],
            "address_line1": cust["address_line1"],
            "city": cust["city"],
            "pincode": cust["pincode"],
            "country": "India",
            "is_primary_address": 1,
            "links": [{"link_doctype": "Customer", "link_name": cust["name"]}],
        })
        doc.insert(ignore_permissions=True)


def _create_warehouse(company):
    """Create demo Warehouse (idempotent)."""
    if frappe.db.exists("Warehouse", DEMO_WAREHOUSE["warehouse_name"]):
        return
    doc = frappe.get_doc({
        "doctype": "Warehouse",
        "warehouse_name": DEMO_WAREHOUSE["warehouse_name"],
        "company": company,
        "city": DEMO_WAREHOUSE["city"],
    })
    doc.insert(ignore_permissions=True)


def _create_transporter():
    """Create a demo Transporter with vehicle types and service areas."""
    doc = frappe.get_doc({
        "doctype": "Transporter",
        "transporter_name": DEMO_TRANSPORTER["transporter_name"],
        "contact_number": DEMO_TRANSPORTER["contact_number"],
        "email": DEMO_TRANSPORTER["email"],
        "is_active": 1,
        "vehicle_types": DEMO_TRANSPORTER["vehicle_types"],
        "service_areas": DEMO_TRANSPORTER["service_areas"],
    })
    # The transporter_name serves as the document name (title_field)
    doc.insert(ignore_permissions=True)
    return doc


def _create_delivery_trip(transporter):
    """Create a demo Delivery Trip with stops.

    Bypasses validation (linked_delivery_notes, POD checks) since this is
    demo data intended for exploration, not a production workflow.
    """
    warehouse = frappe.get_value("Warehouse", DEMO_WAREHOUSE["warehouse_name"])
    if not warehouse:
        frappe.throw(_("Demo Warehouse not found — cannot create Delivery Trip."))

    delivery_stops = []
    for sd in DEMO_TRIP_STOPS:
        customer = frappe.db.get_value("Customer", sd["customer"], "name")
        if not customer:
            continue
        # Resolve the demo Address we created earlier
        address = frappe.db.get_value(
            "Dynamic Link",
            {"link_doctype": "Customer", "link_name": customer, "parenttype": "Address"},
            "parent",
        )
        delivery_stops.append({
            "customer": customer,
            "address": address,
            "sequence_no": sd["sequence_no"],
            "delivery_window_start": sd["delivery_window_start"],
            "delivery_window_end": sd["delivery_window_end"],
            "status": "Pending",
        })

    if not delivery_stops:
        frappe.throw(_("No delivery stops could be created."))

    doc = frappe.get_doc({
        "doctype": "Delivery Trip",
        "transporter": transporter.name,
        "driver_name": DEMO_DRIVER["driver_name"],
        "driver_contact": DEMO_DRIVER["driver_contact"],
        "vehicle_no": DEMO_DRIVER["vehicle_no"],
        "origin_warehouse": warehouse,
        "planned_dispatch_date": frappe.utils.today(),
        "trip_status": "Planned",
        "delivery_stops": delivery_stops,
        # Demo trips don't link real Delivery Notes — skip validation below
        "linked_delivery_notes": [],
    })

    # Bypass delivery-notes + POD validation for demo records
    doc.flags.ignore_validate = True
    doc.insert(ignore_permissions=True)


# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------


def _print_success():
    """Log a success message visible in Error Log and bench console."""
    msg = _(
        "MSME Logistics demo data created:\n"
        "  • 3 Customers with Addresses\n"
        "  • 1 Warehouse\n"
        "  • Transporter: {transporter} (3 vehicle types, 3 service areas)\n"
        "  • 1 Delivery Trip (Planned) with 3 Delivery Stops\n"
        "\nOpen the Logistics Dashboard from the Workspace menu to explore."
    ).format(transporter=DEMO_TRANSPORTER["transporter_name"])

    frappe.log_error(title=_("MSME Logistics Demo Installed"), message=msg)
    print("\n" + msg + "\n")
