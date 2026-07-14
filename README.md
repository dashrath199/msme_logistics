🚚 MSME Logistics
==================
**B2B Last-Mile Logistics Management for Indian MSMEs**

An ERPNext v15 Custom App — Portfolio / Demo

[![ERPNext v15](https://img.shields.io/badge/ERPNext-v15-blue)](https://erpnext.com)
[![CI](https://github.com/YOUR_USERNAME/msme_logistics/actions/workflows/ci.yml/badge.svg)](https://github.com/YOUR_USERNAME/msme_logistics/actions/workflows/ci.yml)
[![Python](https://img.shields.io/badge/Python-3.10%2B-brightgreen)](https://www.python.org)
[![License](https://img.shields.io/badge/License-MIT-yellow)](LICENSE)
![PRs Welcome](https://img.shields.io/badge/PRs-welcome-brightgreen)

---

📸 **Demo Screenshots**
*These are placeholder descriptions. Once installed on a Frappe Bench, capture actual screenshots and add them here.*

<details>
<summary>🖥️ Click to view screenshot mockups</summary>

| Workspace | Description |
|-----------|-------------|
| **Logistics Dashboard** | Overview with Number Cards (Trips In Transit Today, Avg Cost Per Stop) + Cost Per Delivery Trend line chart |
| **Trip Management** | List view of Delivery Trips with workflow-driven status indicators (Planned → Dispatched → In Transit → Completed → Reconciled) |
| **Delivery Trip Form** | Transporter info, origin warehouse, delivery stops table with sequence, time windows, POD capture |
| **Cost Reconciliation** | Per-trip cost breakdown — fuel, toll, payout, and cost-per-stop computation |
| **Reports** | Cost Per Delivery by Transporter (bar chart), Failed/Rescheduled Rate by Area, Trip Timeline |
</details>

---

✨ Features
-----------

| Feature | Description |
|---------|-------------|
| 🚛 **Transporter Management** | Register transporters with vehicle types, capacity (kg), rate cards (₹/km), and service area pincodes |
| 📍 **Delivery Trip Planning** | Batch delivery notes into trips with sequenced stops, delivery time windows, and SLA tracking |
| 🔄 **Workflow Engine** | 5-state workflow: Planned → Dispatched → In Transit → Completed → Reconciled. Transitions enforced via ERPNext Workflow |
| 📸 **Proof of Delivery (POD)** | Capture POD photos (Attach field) and digital signatures (Signature field) per stop. Blocks trip completion if POD is missing |
| 📊 **3 Query Reports** | Cost Per Delivery by Transporter (bar chart), Failed/Rescheduled Rate by Area, Trip Timeline |
| 📈 **Dashboard with Charts** | Number Cards for Trips In Transit Today & Avg Cost Per Stop. Line chart for Cost Per Delivery Trend |
| 🗺️ **Route Optimization API** | Whitelisted API endpoint that delegates stop sequencing to Google Directions / OSRM. Re-orders `sequence_no` on each stop |
| 📱 **Driver Stop Updates API** | Lightweight endpoint (`update_stop_status`) for mobile/PWA — update stop status, attach POD, auto-check trip completion |
| 🔔 **3 System Notifications** | Delivery Failed (on stop save with status=Failed), POD Missing at Trip Close (Before Workflow Transition), Trip Not Dispatched (Days After trigger) |
| ⏰ **Scheduled Task** | Daily cron checks for Planned trips past their dispatch date; publishes real-time alerts |
| 🎭 **Demo Data** | 3 customers with addresses, 1 warehouse, 1 transporter (3 vehicle types, 3 service areas), 3 delivery trips (Planned / In Transit / Completed), 1 cost reconciliation — auto-installed |

---

🚀 Quick Install
----------------

```bash
# 1. Get the app
bench get-app https://github.com/YOUR_USERNAME/msme_logistics

# 2. Create a site (if needed)
bench new-site logistics-demo.local --admin-password admin

# 3. Install the app
bench --site logistics-demo.local install-app msme_logistics

# 4. Set developer mode to explore DocTypes in UI
bench --site logistics-demo.local set-config developer_mode 1

# 5. Build and restart
bench build
bench restart
```

That's it. Demo data is loaded automatically during installation. Log in to `http://logistics-demo.local:8000` and explore the **Logistics Dashboard** workspace.

---

🧱 What's Inside
----------------

### DocTypes

| DocType | Key Fields | Behavior |
|---------|-----------|----------|
| **Transporter** | `transporter_name`, `contact_number`, `email`, `is_active` + child tables for `vehicle_types` (type, capacity_kg, rate_per_km) and `service_areas` (pincode_from, pincode_to, area_name) | Master data — title field is `transporter_name`. Linked from Delivery Trip |
| **Delivery Trip** | `transporter` (Link), `driver_name`, `driver_contact`, `vehicle_no`, `origin_warehouse` (Link/Warehouse), `planned_dispatch_date`, `actual_dispatch_datetime`, `trip_status` (Planned/Dispatched/In Transit/Completed/Reconciled), `total_stops`, `total_distance` | Submittable. 5-state workflow. `validate()` enforces at least 1 stop + 1 delivery note. Blocks completion if Delivered stops are missing POD. `before_save` syncs `total_stops` from child table |
| **Delivery Stop** (Child) | `customer` (Link/Customer), `address` (Link/Address), `sequence_no`, `delivery_window_start` (Time), `delivery_window_end` (Time), `status` (Pending/Delivered/Failed/Rescheduled), `actual_arrival_time`, `pod_image` (Attach), `pod_signature` (Signature), `notes` (Small Text) | Table child of Delivery Trip. SLA tracking via delivery windows. POD is per-stop |
| **Linked Delivery Note** (Child) | `delivery_note` (Link/Delivery Note) | Table child of Delivery Trip. Links standard ERPNext Delivery Notes to a trip |
| **Vehicle Types** (Child) | `vehicle_type` (Data), `capacity_kg` (Float), `rate_per_km` (Currency/INR) | Table child of Transporter. Rate card for cost estimation |
| **Service Areas** (Child) | `pincode_from` (Data), `pincode_to` (Data), `area_name` (Data) | Table child of Transporter. Defines which pincodes a transporter serves |
| **Trip Cost Reconciliation** | `delivery_trip` (Link/Delivery Trip), `fuel_cost`, `toll_charges`, `other_charges`, `transporter_payout`, `total_stops` (read-only), `cost_per_stop` (read-only), `reconciled_by` (Link/User), `reconciliation_date`, `remarks` | Per-trip cost analysis. `cost_per_stop` computed as `transporter_payout / total_stops`. Powers the Avg Cost Per Stop card and Cost Per Delivery Trend chart |

### Workflow: Delivery Trip Workflow

```
Planned ──[Dispatch]──→ Dispatched ──[Start Transit]──→ In Transit ──[Complete]──→ Completed ──[Reconcile]──→ Reconciled
   ↑                                                                                                                │
   └────────────────────────────[Cancel Trip]────────────────────────────────────────────────────────────────────────┘
```

| State | docstatus | Allowed Action | Next State | Allowed Role |
|-------|-----------|---------------|------------|-------------|
| Planned | Draft (0) | Dispatch | Dispatched | Dispatch Manager |
| Dispatched | Draft (0) | Start Transit | In Transit | Dispatch Manager |
| Dispatched | Draft (0) | Cancel Trip | Planned | Dispatch Manager |
| In Transit | Draft (0) | Complete | Completed | Dispatch Manager |
| Completed | Submitted (1) | Reconcile | Reconciled | Dispatch Manager |

### Reports (Query Reports)

| Report | SQL Logic | Use Case |
|--------|-----------|----------|
| **Cost Per Delivery by Transporter** | Aggregates `Trip Cost Reconciliation` by transporter — total fuel, toll, payout, stops, and `AVG(cost_per_stop)`. Bar chart | "Which transporter is most cost-effective?" |
| **Failed/Rescheduled Rate by Area** | Groups `Delivery Stop` statuses by Address pincode/city. Computes failure rate % (`Failed + Rescheduled / Total`). Bar chart | "Which areas have delivery problems?" |
| **Trip Timeline** | Report Builder on `Delivery Trip` | "What trips happened on a given date?" — ad-hoc filtering by status, transporter, driver |

### Workspaces

| Workspace | Contents |
|-----------|----------|
| **Logistics Dashboard** (Module Home) | Number Cards: Trips In Transit Today, Avg Cost Per Stop. Dashboard Chart: Cost Per Delivery Trend |
| **Trip Management** | Card link to Delivery Trip list view |
| **Masters** | Card link to Transporter list view |
| **Billing & Reconciliation** | Card link to Trip Cost Reconciliation list view |
| **Reports** | Card links to all 3 reports |

### Notifications

| Event | Condition | Action |
|-------|-----------|--------|
| `Delivery Stop` Saved with status = `Failed` | `doc.status == "Failed"` | System Notification to all Dispatch Manager users |
| `Delivery Trip` Before Workflow Transition to `Complete` | Any Delivered stop has no `pod_image` and no `pod_signature` | System Notification with list of stops missing POD |
| `Delivery Trip` Days After `planned_dispatch_date` | `doc.trip_status == "Planned"` (daily check) | System Notification — "Trip Not Dispatched" |

### Scheduled Tasks

| Task | Schedule | What It Does |
|------|----------|-------------|
| `check_pending_dispatches` | Daily | Queries Delivery Trips in `Planned` status past their `planned_dispatch_date`. Publishes real-time alert `msme_logistics:pending_dispatch` to Dispatch Managers. Logs count to Error Log |

### API Endpoints

**`POST /api/method/msme_logistics.api.optimize_route`**

Accepts a `trip_name` parameter. Resolves the origin warehouse address and all delivery stop addresses, then delegates to an external routing API (Google Directions / OSRM) for optimal stop sequencing. Re-orders the `sequence_no` field on each stop.

Placeholder implementation returns stops in original order. The TODO in `api.py` shows the actual integration pattern.

```bash
curl -X POST \
  https://logistics-demo.local/api/method/msme_logistics.api.optimize_route \
  -H "Content-Type: application/json" \
  -d '{"trip_name": "TRIP-2024-00001"}'
```

**`POST /api/method/msme_logistics.api.update_stop_status`**

Lightweight endpoint for driver mobile view. Updates a single stop's status and optionally attaches POD.

```bash
curl -X POST \
  https://logistics-demo.local/api/method/msme_logistics.api.update_stop_status \
  -H "Content-Type: application/json" \
  -d '{
    "stop_name": "some-stop-name",
    "status": "Delivered",
    "pod_signature": "base64-encoded-signature-data"
  }'
```

---

📁 Project Structure
--------------------

```
msme_logistics/
├── __init__.py
├── setup.py / setup.cfg / requirements.txt / MANIFEST.in
├── license.txt / .gitignore
├── README.md
└── msme_logistics/
    ├── __init__.py                  # App version & metadata
    ├── hooks.py                     # Frappe configuration — DocType classes, fixtures, scheduler
    ├── api.py                       # optimize_route + update_stop_status endpoints
    ├── demo.py                      # after_install / before_uninstall — seeds demo data
    ├── create_assets.py             # Generates placeholder splash.png + favicon.ico
    ├── load_fixtures.py             # Bulk-imports all fixtures from /fixtures directory
    ├── fix_workspace.py             # Diagnostic + fix for null workspace label/title sidebar crash
    ├── tasks.py                     # check_pending_dispatches — daily scheduler task
    ├── config/
    │   ├── desktop.py               # Module icon & color in the workspace menu
    │   └── docs.py                  # (placeholder)
    ├── doctype/
    │   ├── transporter/             # Master: transporter info + vehicle types + service areas
    │   ├── delivery_trip/           # Core: submittable, workflow-driven, POD validation
    │   ├── delivery_stop/           # Child table: per-stop status, windows, POD capture
    │   ├── linked_delivery_note/    # Child table: links standard Delivery Notes
    │   ├── vehicle_types/           # Child table: vehicle spec + rate card
    │   ├── service_areas/           # Child table: pincode range per transporter
    │   └── trip_cost_reconciliation/# Per-trip cost breakdown
    ├── fixtures/                    # Workflow, Roles, Notifications, Number Cards, Dashboard Chart
    ├── notification/
    │   ├── delivery_failed/         # System Notification — alert on failed delivery
    │   ├── pod_missing_at_trip_close/ # System Notification — alert before completing trip
    │   └── trip_not_dispatched/     # System Notification — daily overdue trips
    ├── public/
    │   ├── css/msme_logistics.css   # Custom styles: status color coding, card styling
    │   └── js/msme_logistics.js     # Realtime event listeners for trip notifications
    ├── report/
    │   ├── cost_per_delivery_by_transporter/   # Bar chart — cost efficiency by transporter
    │   ├── failed_rescheduled_rate_by_area/    # Bar chart — failure rate by pincode/city
    │   └── trip_timeline/                      # Report Builder — ad-hoc trip queries
    └── workspace/
        ├── logistics_dashboard/     # Module home with number cards + chart
        ├── trip_management/         # Card-based workspace for Delivery Trips
        ├── masters/                 # Card-based workspace for Transporters
        ├── billing_reconciliation/  # Card-based workspace for cost reconciliation
        └── reports/                 # Card-based workspace linking all 3 reports
```

---

⚠️ Architecture Rationale
-------------------------

This app demonstrates fluent Frappe/ERPNext v15 development — DocTypes, Workflows, Query Reports, Script Reports, Workspaces, Notifications, Scheduled Tasks, Fixtures, Patches, and API design.

It is a **portfolio/demo piece** that shows full-spectrum Frappe development skills. Here are the architectural considerations:

| Concern | ERPNext Approach | What a Real Logistics SaaS Might Use |
|---------|-----------------|--------------------------------------|
| **Driver Interface** | Desktop-grade Frappe Desk (or minimal mobile web) | Dedicated Driver App (React Native / Flutter) with GPS tracking |
| **Route Optimization** | External API delegate via server-side whitelisted method | Embedded OSRM / Valhalla engine or real-time Google Maps Routes API |
| **GPS Tracking** | Not implemented — stop status updates are manual | Live GPS pings at 30s intervals with geofence arrival detection |
| **Real-time Visibility** | Frappe real-time pub/sub for internal users | WebSocket-powered tracking portal for customers |
| **Billing Integration** | Manual Trip Cost Reconciliation doc | Automated e-invoice generation (GST) + Transporter payment settlement |
| **POD Workflow** | Attach/Signature fields per stop | OCR-based document scan + tamper-proof image hashing |
| **Offline Support** | Online-only (Frappe architecture) | PWA with IndexedDB queue for offline stop updates |
| **Scale** | Single MariaDB — suited for 10s of trips/day | Horizontally-scalable Postgres with read replicas for 1000s/day |

### The Real Architecture Might Look Like

```
┌──────────────┐     ┌──────────────────┐     ┌─────────────────────┐
│ Driver App   │────▶│ FastAPI Gateway   │────▶│ Trip Service        │
│ (React Native)│    │ + WebSocket Hub   │     │ (Postgres + Redis)  │
└──────────────┘     └──────────────────┘     └─────────────────────┘
                                                       │
┌──────────────┐                              ┌─────────────────────┐
│ Customer     │◀───── Tracking Portal ──────│ Notification Service │
│ (Browser)    │       (Next.js + Mapbox)     │ (WhatsApp / SMS)     │
└──────────────┘                              └─────────────────────┘
```

This ERPNext app shows I can build Frappe DocTypes, workflows, reports, workspaces, notifications, scheduled tasks, fixtures, and custom API endpoints fluently. It does not claim this is the right stack for a high-volume logistics SaaS product. It's a **portfolio piece** demonstrating Frappe/ERPNext development skills with full transparency about architectural trade-offs.

---

🛠️ Development Notes
---------------------

### Adding a New Field

```bash
# Edit the DocType JSON, then run:
bench --site yoursite.local migrate
```

### Adding a New Report

Create `report/<report_name>/<report_name>.json` with a SQL query. The report is auto-discovered — no `hooks.py` registration needed. Add a `<report_name>.js` file for filters.

### Loading Fixtures Manually

```bash
bench --site yoursite.local execute msme_logistics.load_fixtures.run
```

Then run:
```bash
bench --site yoursite.local migrate && bench clear-cache
```

### Diagnosing Workspace Sidebar Crash

If the sidebar shows a blank or crashes with `TypeError: Cannot read properties of null (reading 'toLowerCase')`:

```bash
bench --site yoursite.local execute msme_logistics.fix_workspace.diagnose
bench --site yoursite.local execute msme_logistics.fix_workspace.fix
```

### Generating Placeholder Assets

```bash
bench --site yoursite.local execute msme_logistics.create_assets.run
```

### Fixing Demo Trip docstatus

If Completed/Reconciled demo trips don't appear in the submitted list view:

```bash
bench --site yoursite.local execute msme_logistics.fix_workspace.fix_docstatus
```

### Cleaning Up Demo Data (Before Uninstall)

```bash
bench --site yoursite.local execute msme_logistics.demo.before_uninstall
```

### Testing the Route Optimization API

```bash
curl -X POST \
  https://yoursite.local/api/method/msme_logistics.api.optimize_route \
  -H "Content-Type: application/json" \
  -d '{"trip_name": "TRIP-2024-00001"}'
```

### Testing the Stop Status Update API

```bash
curl -X POST \
  https://yoursite.local/api/method/msme_logistics.api.update_stop_status \
  -H "Content-Type: application/json" \
  -d '{
    "stop_name": "stop-name-here",
    "status": "Delivered"
  }'
```

### Setting Up the External Routing API

The route optimization endpoint expects a routing service at a configurable URL. In a single-value doctype or site config:

```bash
bench --site yoursite.local set-config routing_api_url "https://api.openrouteservice.org/v2/directions/driving-car"
bench --site yoursite.local set-config routing_api_key "your-api-key"
```

Then update `api.py` to read these values and make the HTTP request (see the TODO in the `optimize_route` function).

---

📄 License
----------

MIT © 2026 MSME Logistics

[![Frappe](https://img.shields.io/badge/Built%20with-Frappe-blue)](https://frappeframework.com)
[![ERPNext](https://img.shields.io/badge/Powered%20by-ERPNext-green)](https://erpnext.com)

---

*Built with Frappe & ERPNext v15. For portfolio/demo purposes. Not recommended for production logistics deployments without significant hardening.*
