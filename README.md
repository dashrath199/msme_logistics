# MSME Logistics

MSME B2B Last-Mile Logistics Management for ERPNext v15.

## Features

- **Transporter Management** — Register transporters with vehicle types, capacity, rate cards, and service area pincodes
- **Delivery Trip Management** — Batch delivery notes into optimized trips with stop-by-stop tracking
- **Proof of Delivery** — Capture POD photos and signatures at each stop
- **SLA Compliance** — Track on-time delivery performance against delivery windows
- **Cost Reconciliation** — Per-trip cost analysis with cost-per-stop computation
- **Route Optimization** — External API integration (Google Directions/OSRM) for stop sequencing
- **Notifications** — Alerts for failed deliveries, pending dispatches, and missing PODs

## Installation

```bash
cd ~/frappe-bench
bench get-app msme_logistics
bench --site yoursite.local install-app msme_logistics
```

## Workflow

1. Sales Order → Delivery Note (standard ERPNext)
2. Delivery Trip created (batch Delivery Notes by area)
3. Route optimized via external API
4. Trip dispatched → In Transit
5. Stop-by-stop status updates with POD capture
6. Trip completed → Cost reconciled

## Roles

- **Dispatch Manager** — Full access to all logistics operations
- **Driver** — Restricted access for stop-by-stop updates
