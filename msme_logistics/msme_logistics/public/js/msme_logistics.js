frappe.provide("msme_logistics");

// Realtime event listeners for logistics operations
frappe.realtime.on("msme_logistics:trip_in_transit", function (data) {
    frappe.show_alert({
        message: __("Trip {0} is now In Transit", [data.trip_name]),
        indicator: "blue",
    }, 5);
});

frappe.realtime.on("msme_logistics:trip_completed", function (data) {
    frappe.show_alert({
        message: __("Trip {0} completed ({1} stops)", [data.trip_name, data.total_stops]),
        indicator: "green",
    }, 5);
});

frappe.realtime.on("msme_logistics:pending_dispatch", function (data) {
    frappe.show_alert({
        message: data.message,
        indicator: "orange",
    }, 10);
});
