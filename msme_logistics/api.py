import frappe
from frappe import _

# ---------------------------------------------------------------------------
# Route Optimization
# ---------------------------------------------------------------------------


@frappe.whitelist()
def optimize_route(trip_name: str):
    """
    Call an external routing API (Google Directions / OSRM) with the delivery
    stop addresses and update the sequence_no of each stop to reflect the
    optimized order.

    This function does NOT implement TSP / routing logic inside Frappe.
    It delegates to an external routing engine via HTTP.

    Expected external API: POST /route
    Request body: { "origin": <warehouse_address>, "destinations": [<stop_addresses>] }
    Response: { "route_order": [2, 0, 1, 3, ...], "total_distance_km": ..., "total_duration_min": ... }
    """
    trip = frappe.get_doc("Delivery Trip", trip_name)
    if not trip:
        frappe.throw(_("Delivery Trip {0} not found").format(trip_name))

    if trip.trip_status not in ("Planned", "Dispatched"):
        frappe.throw(
            _("Route can only be optimized for trips with status 'Planned' or 'Dispatched'")
        )

    stops = trip.delivery_stops
    if not stops:
        frappe.throw(_("Delivery Trip {0} has no stops to optimize").format(trip_name))

    # Build addresses list for each stop
    origin_address = _get_warehouse_address(trip.origin_warehouse)
    destination_addresses = [_get_stop_address(stop) for stop in stops]

    # --- Call external routing API ---
    # TODO: Replace with actual API call to Google Directions / OSRM
    #
    # Example with requests:
    #   import requests
    #   routing_api_url = frappe.db.get_single_value("MSME Logistics Settings", "routing_api_url")
    #   api_key = frappe.db.get_single_value("MSME Logistics Settings", "routing_api_key")
    #   payload = {
    #       "origin": origin_address,
    #       "destinations": destination_addresses,
    #       "api_key": api_key,
    #   }
    #   resp = requests.post(routing_api_url, json=payload, timeout=30)
    #   resp.raise_for_status()
    #   result = resp.json()
    #   optimized_order = result.get("route_order", [])
    #   total_distance = result.get("total_distance_km", 0)

    # Placeholder: return stops in original order
    optimized_order = list(range(len(stops)))
    total_distance = 0.0

    # Update sequence_no on each stop based on optimized order
    for new_seq, original_idx in enumerate(optimized_order):
        stop = trip.delivery_stops[original_idx]
        stop.sequence_no = new_seq + 1  # 1-based ordering

    trip.total_distance = total_distance
    trip.save(ignore_permissions=True)

    frappe.msgprint(
        _("Route optimized for {0}. {1} stops re-sequenced.").format(
            trip_name, len(stops)
        )
    )
    return {
        "trip": trip_name,
        "stops_optimized": len(stops),
        "total_distance_km": total_distance,
    }


# ---------------------------------------------------------------------------
# Stop-level updates (intended for use by driver mobile view)
# ---------------------------------------------------------------------------


@frappe.whitelist()
def update_stop_status(stop_name: str, status: str, pod_image: str = None, pod_signature: str = None):
    """
    Update the status of a single Delivery Stop.
    Designed to be called from a lightweight driver-facing mobile view / PWA.
    """
    allowed_statuses = ("Pending", "Delivered", "Failed", "Rescheduled")
    if status not in allowed_statuses:
        frappe.throw(_("Invalid status. Allowed: {0}").format(", ".join(allowed_statuses)))

    stop = frappe.get_doc("Delivery Stop", stop_name)
    stop.status = status

    # Only set arrival time on first status change, don't overwrite on re-saves
    if not stop.actual_arrival_time:
        stop.actual_arrival_time = frappe.utils.now_datetime()

    if pod_image:
        stop.pod_image = pod_image
    if pod_signature:
        stop.pod_signature = pod_signature

    stop.save(ignore_permissions=True)

    # If all stops completed, check if trip should auto-transition
    _check_trip_completion(stop.parent)

    return {"status": "success", "stop": stop_name, "new_status": status}


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------


def _get_warehouse_address(warehouse_name: str) -> str:
    """Resolve a Warehouse to a full address string for routing."""
    warehouse = frappe.get_doc("Warehouse", warehouse_name)
    address = frappe.db.get_value(
        "Dynamic Link",
        {"link_doctype": "Warehouse", "link_name": warehouse_name, "parenttype": "Address"},
        "parent",
    )
    if address:
        addr = frappe.get_doc("Address", address)
        return _format_address(addr)
    return warehouse_name


def _get_stop_address(stop) -> str:
    """Resolve a Delivery Stop's customer address for routing."""
    address_name = stop.address
    if address_name:
        addr = frappe.get_doc("Address", address_name)
        return _format_address(addr)

    # Fall back to customer primary address
    customer = frappe.get_doc("Customer", stop.customer)
    primary_address = frappe.db.get_value(
        "Dynamic Link",
        {"link_doctype": "Customer", "link_name": customer.name, "parenttype": "Address"},
        "parent",
    )
    if primary_address:
        addr = frappe.get_doc("Address", primary_address)
        return _format_address(addr)

    return stop.customer


def _format_address(addr) -> str:
    """Format an Address document as a single-line string for geocoding."""
    parts = [
        addr.address_line1,
        addr.address_line2,
        addr.city,
        addr.state,
        addr.pincode,
        addr.country,
    ]
    return ", ".join(p for p in parts if p)


def _check_trip_completion(trip_name: str):
    """
    After a stop update, check whether all stops on the trip are marked
    Delivered / Failed / Rescheduled and auto-transition trip to Completed.
    """
    trip = frappe.get_doc("Delivery Trip", trip_name)
    terminal_statuses = {"Delivered", "Failed", "Rescheduled"}
    all_terminal = all(
        stop.status in terminal_statuses for stop in trip.delivery_stops
    )
    if all_terminal and trip.trip_status == "In Transit":
        # Use the workflow engine for the transition so state tracking is maintained
        frappe.workflow.docs.apply_workflow(trip, "Complete")
