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

# Subset of stops for shorter trips
DEMO_TRIP_STOPS_SHORT = [
    {
        "customer": "New Delhi Electronics",
        "sequence_no": 1,
        "delivery_window_start": "09:00",
        "delivery_window_end": "11:00",
    },
    {
        "customer": "Bangalore Retail Mart",
        "sequence_no": 2,
        "delivery_window_start": "14:00",
        "delivery_window_end": "16:00",
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
        warehouse = _get_warehouse_name()

        # Trip 1: Planned (existing demo)
        _create_delivery_trip(transporter, warehouse, "Planned")

        # Trip 2: In Transit — powers 'Trips In Transit Today' number card
        _create_delivery_trip(
            transporter, warehouse, "In Transit",
            driver="Suresh Patel", driver_contact="+91-8877665544", vehicle="DL-04-WW-5678",
            stops_status=["Delivered", "Pending"],
            actual_dispatch=frappe.utils.now_datetime(),
        )

        # Trip 3: Completed — powers 'Failed Deliveries This Week' via a 'Failed' stop
        _create_delivery_trip(
            transporter, warehouse, "Completed",
            driver="Amit Verma", driver_contact="+91-7766554433", vehicle="DL-05-ZZ-9012",
            stops_status=["Delivered", "Failed"],
            actual_dispatch=frappe.utils.add_to_date(frappe.utils.now_datetime(), hours=-6),
        )

        # Trip Cost Reconciliations — powers 'Avg Cost Per Stop' number card
        _create_trip_cost_reconciliation(transporter, warehouse)

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

    # Also clean up demo data created by this module
    warehouse_name = frappe.db.get_value(
        "Warehouse",
        {"warehouse_name": DEMO_WAREHOUSE["warehouse_name"]},
        "name",
    )
    if warehouse_name:
        try:
            frappe.delete_doc("Warehouse", warehouse_name, force=True, ignore_permissions=True)
        except Exception:
            pass

    for cust in DEMO_CUSTOMERS:
        # Clean up the demo Address linked to this customer
        addr_name = f"{cust['name']} - Demo"
        if frappe.db.exists("Address", addr_name):
            try:
                frappe.delete_doc("Address", addr_name, force=True, ignore_permissions=True)
            except Exception:
                pass
        try:
            frappe.delete_doc("Customer", cust["name"], force=True, ignore_permissions=True)
        except Exception:
            pass


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


def _get_customer_group():
    """Return a non-group Customer Group available on the site.

    Falls back to creating one if none exists.
    """
    group = frappe.db.get_value(
        "Customer Group",
        {"is_group": 0},
        "name",
        order_by="creation asc",
    )
    if group:
        return group

    # No non-group Customer Group exists yet — create one
    doc = frappe.get_doc({
        "doctype": "Customer Group",
        "customer_group_name": "Demo Customers",
        "is_group": 0,
    })
    doc.insert(ignore_permissions=True)
    return doc.name


def _get_territory():
    """Return a non-group Territory available on the site.

    Falls back to creating one if none exists.
    """
    territory = frappe.db.get_value(
        "Territory",
        {"is_group": 0},
        "name",
        order_by="creation asc",
    )
    if territory:
        return territory

    doc = frappe.get_doc({
        "doctype": "Territory",
        "territory_name": "Demo Territory",
        "is_group": 0,
    })
    doc.insert(ignore_permissions=True)
    return doc.name


def _create_customers():
    """Create demo Customers (idempotent)."""
    customer_group = _get_customer_group()
    territory = _get_territory()

    for cust in DEMO_CUSTOMERS:
        if frappe.db.exists("Customer", cust["name"]):
            continue
        doc = frappe.get_doc({
            "doctype": "Customer",
            "customer_name": cust["name"],
            "customer_type": "Company",
            "customer_group": customer_group,
            "territory": territory,
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
    # Frappe auto-names warehouses as "warehouse_name - company_abbr", so search by field
    existing = frappe.db.get_value(
        "Warehouse",
        {"warehouse_name": DEMO_WAREHOUSE["warehouse_name"]},
        "name",
    )
    if existing:
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


def _get_warehouse_name():
    """Get the actual warehouse name (with company abbreviation)."""
    warehouse = frappe.db.get_value(
        "Warehouse",
        {"warehouse_name": DEMO_WAREHOUSE["warehouse_name"]},
        "name",
    )
    if not warehouse:
        frappe.throw(_("Demo Warehouse not found — cannot create Delivery Trip."))
    return warehouse


def _build_delivery_stops(stop_configs, stops_status=None):
    """Build a list of delivery stop dicts from a stop config and optional status overrides."""
    stops_status = stops_status or ["Pending"] * len(stop_configs)
    delivery_stops = []
    for i, sd in enumerate(stop_configs):
        customer = frappe.db.get_value("Customer", sd["customer"], "name")
        if not customer:
            continue
        address = frappe.db.get_value(
            "Dynamic Link",
            {"link_doctype": "Customer", "link_name": customer, "parenttype": "Address"},
            "parent",
        )
        status = stops_status[i] if i < len(stops_status) else "Pending"
        stop = {
            "customer": customer,
            "address": address,
            "sequence_no": sd["sequence_no"],
            "delivery_window_start": sd["delivery_window_start"],
            "delivery_window_end": sd["delivery_window_end"],
            "status": status,
        }
        # Add actual arrival time for stops that are Delivered or Failed
        if status in ("Delivered", "Failed"):
            stop["actual_arrival_time"] = frappe.utils.now_datetime()
        delivery_stops.append(stop)
    return delivery_stops


def _create_delivery_trip(
    transporter, warehouse, status,
    driver=None, driver_contact=None, vehicle=None,
    stops_status=None, actual_dispatch=None,
):
    """Create a demo Delivery Trip with the given status and stops.

    Bypasses validation (linked_delivery_notes, POD checks) since this is
    demo data intended for exploration, not a production workflow.
    """
    if not warehouse:
        frappe.throw(_("Demo Warehouse not found — cannot create Delivery Trip."))

    # Use short stops for non-Planned trips, full stops for Planned
    stop_configs = DEMO_TRIP_STOPS_SHORT if status != "Planned" else DEMO_TRIP_STOPS
    delivery_stops = _build_delivery_stops(stop_configs, stops_status)

    if not delivery_stops:
        frappe.throw(_("No delivery stops could be created."))

    doc_data = {
        "doctype": "Delivery Trip",
        "transporter": transporter.name,
        "driver_name": driver or DEMO_DRIVER["driver_name"],
        "driver_contact": driver_contact or DEMO_DRIVER["driver_contact"],
        "vehicle_no": vehicle or DEMO_DRIVER["vehicle_no"],
        "origin_warehouse": warehouse,
        "planned_dispatch_date": frappe.utils.today(),
        "trip_status": status,
        "delivery_stops": delivery_stops,
        "linked_delivery_notes": [],
    }

    if actual_dispatch:
        doc_data["actual_dispatch_datetime"] = actual_dispatch

    # Must set trip_status = first workflow state ("Planned") during insert
    # because validate_workflow() blocks non-initial states for new documents
    original_status = doc_data.get("trip_status", "Planned")
    doc_data["trip_status"] = "Planned"

    doc = frappe.get_doc(doc_data)
    doc.flags.ignore_validate = True
    doc.insert(ignore_permissions=True, ignore_mandatory=True)

    # Now update to the actual desired status via direct SQL (bypasses workflow)
    if original_status != "Planned":
        frappe.db.set_value(
            "Delivery Trip",
            doc.name,
            "trip_status",
            original_status,
            update_modified=False,
        )

    # For 'Completed' and 'Reconciled' states, the workflow expects doc_status=1 (Submitted).
    # Since we bypass the workflow, set docstatus directly so these records appear in
    # the list view (which for submittable docs defaults to showing submitted records).
    if original_status in ("Completed", "Reconciled"):
        frappe.db.set_value(
            "Delivery Trip",
            doc.name,
            "docstatus",
            1,
            update_modified=False,
        )


def _create_trip_cost_reconciliation(transporter, warehouse):
    """Create Trip Cost Reconciliation records for the completed trip.

    These power the 'Avg Cost Per Stop' number card and 'Cost Per Delivery Trend' chart.
    """
    completed_trip_names = frappe.get_all(
        "Delivery Trip",
        filters={"transporter": transporter.name, "trip_status": "Completed"},
        pluck="name",
        limit=1,
    )
    if not completed_trip_names:
        return

    trip_name = completed_trip_names[0]
    total_stops = 2

    # Create reconciliation records with varying dates for the timeseries chart
    reconciliations = [
        {
            "delivery_trip": trip_name,
            "fuel_cost": 4500,
            "toll_charges": 800,
            "other_charges": 200,
            "transporter_payout": 12000,
            "total_stops": total_stops,
            "cost_per_stop": 6250,
            "reconciled_by": frappe.session.user,
            "reconciliation_date": frappe.utils.add_to_date(frappe.utils.today(), days=-2),
            "remarks": "Weekend run — all deliveries completed on time.",
        },
    ]

    for rec in reconciliations:
        doc = frappe.get_doc({
            "doctype": "Trip Cost Reconciliation",
            **rec,
        })
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
        "  • 1 Delivery Trip (In Transit) with 2 stops (1 Delivered)\n"
        "  • 1 Delivery Trip (Completed) with 2 stops (1 Delivered, 1 Failed)\n"
        "  • 1 Trip Cost Reconciliation record\n"
        "\nOpen the Logistics Dashboard from the Workspace menu to explore."
    ).format(transporter=DEMO_TRANSPORTER["transporter_name"])

    frappe.log_error(title=_("MSME Logistics Demo Installed"), message=msg)
    print("\n" + msg + "\n")
