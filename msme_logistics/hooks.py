from . import __version__ as app_version

app_name = "msme_logistics"
app_title = "MSME Logistics"
app_publisher = "Your Company"
app_description = "MSME B2B Last-Mile Logistics Management"
app_email = "info@example.com"
app_license = "MIT"

# -----------------------------------------------
# DocType Classes
# -----------------------------------------------
doctype_js = {}
doctype_python = {
    "vehicle_types": "msme_logistics.msme_logistics.doctype.vehicle_types.vehicle_types",
    "service_areas": "msme_logistics.msme_logistics.doctype.service_areas.service_areas",
    "linked_delivery_note": "msme_logistics.msme_logistics.doctype.linked_delivery_note.linked_delivery_note",
    "delivery_stop": "msme_logistics.msme_logistics.doctype.delivery_stop.delivery_stop",
    "transporter": "msme_logistics.msme_logistics.doctype.transporter.transporter",
    "delivery_trip": "msme_logistics.msme_logistics.doctype.delivery_trip.delivery_trip",
    "trip_cost_reconciliation": "msme_logistics.msme_logistics.doctype.trip_cost_reconciliation.trip_cost_reconciliation",
}

# -----------------------------------------------
# Fixtures
# -----------------------------------------------
fixtures = [
    {"dt": "Client Script", "filters": [["module", "=", "MSME Logistics"]]},
    {"dt": "Server Script", "filters": [["module", "=", "MSME Logistics"]]},
    {"dt": "Workflow", "filters": [["name", "=", "Delivery Trip Workflow"]]},
    {"dt": "Workflow State", "filters": [["name", "in", ["Planned", "Dispatched", "In Transit", "Completed", "Reconciled"]]]},
    {"dt": "Workflow Action Master", "filters": [["name", "in", ["Dispatch", "Start Transit", "Complete", "Reconcile", "Cancel Trip"]]]},
    {"dt": "Role", "filters": [["name", "in", ["Dispatch Manager", "Driver"]]]},
    {"dt": "Notification", "filters": [["module", "=", "MSME Logistics"]]},
    {"dt": "Number Card", "filters": [["name", "in", ["Trips In Transit Today", "Avg Cost Per Stop"]]]},
    {"dt": "Dashboard Chart", "filters": [["name", "in", ["Cost Per Delivery Trend"]]]},
]

# -----------------------------------------------
# Install / Uninstall hooks
# -----------------------------------------------
after_install = "msme_logistics.demo.after_install"

# -----------------------------------------------
# Scheduler / Cron Jobs
# -----------------------------------------------
scheduler_events = {
    "daily": [
        "msme_logistics.tasks.check_pending_dispatches",
    ],
    "daily_long": [],
    "weekly": [],
    "monthly": [],
}

# -----------------------------------------------
# Boot Session / Before Request
# -----------------------------------------------
before_request = []
after_request = []

# App include JS/CSS — disabled until assets are properly linked
# app_include_js = "/assets/msme_logistics/js/msme_logistics.js"
# app_include_css = "/assets/msme_logistics/css/msme_logistics.css"

# Website Context
# website_context = {
#     "favicon": "/assets/msme_logistics/favicon.ico",
#     "splash_image": "/assets/msme_logistics/splash.png",
# }
