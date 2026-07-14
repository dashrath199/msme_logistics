"""Diagnose and fix the workspace sidebar crash.

The error:
    TypeError: Cannot read properties of null (reading 'toLowerCase')
        at Object.slug (router.js:581)
        at append_item (workspace.js:252)

This means a workspace has a null label/title.

Usage:
    bench --site mysite.local execute msme_logistics.fix_workspace.diagnose
    bench --site mysite.local execute msme_logistics.fix_workspace.fix
"""

import frappe


def diagnose():
    """List all workspaces — find any with null label or title."""
    workspaces = frappe.db.sql(
        "SELECT name, label, title, module, public FROM `tabWorkspace` ORDER BY sequence_id",
        as_dict=True,
    )
    print(f"\n{'='*70}")
    print(f"Found {len(workspaces)} workspace(s):")
    print(f"{'='*70}")
    for ws in workspaces:
        flags = []
        if not ws.label:
            flags.append("⚠️ NULL LABEL")
        if not ws.title:
            flags.append("⚠️ NULL TITLE")
        flag_str = " — " + ", ".join(flags) if flags else ""
        print(f"  • {ws.name}: label={ws.label!r}, title={ws.title!r}, module={ws.module}, public={ws.public}{flag_str}")
    print(f"{'='*70}\n")

    bad_labels = [ws for ws in workspaces if not ws.label]
    bad_titles = [ws for ws in workspaces if not ws.title]
    if bad_labels:
        print(f"❌ {len(bad_labels)} workspace(s) with null label FOUND.")
        for ws in bad_labels:
            print(f"   • {ws.name}")
    if bad_titles:
        print(f"❌ {len(bad_titles)} workspace(s) with null title FOUND — THIS IS THE SIDEBAR CRASH CAUSE!")
        for ws in bad_titles:
            print(f"   • {ws.name}")
    if not bad_labels and not bad_titles:
        print("✅ All workspaces have both label and title. The issue may be cached assets.")


def fix():
    """Set title for workspaces that have null title but have a label."""
    bad_titles = frappe.db.sql(
        "SELECT name, label FROM `tabWorkspace` WHERE title IS NULL OR title = ''",
        as_dict=True,
    )
    if bad_titles:
        print(f"Found {len(bad_titles)} workspace(s) with null title:")
        for ws in bad_titles:
            new_title = ws.label or ws.name
            print(f"  • {ws.name}: setting title = {new_title!r}")
            frappe.db.set_value("Workspace", ws.name, "title", new_title)
    else:
        print("✅ No workspaces with null/empty title found.")

    # Also fix label if any are null
    bad_labels = frappe.db.sql(
        "SELECT name FROM `tabWorkspace` WHERE label IS NULL OR label = ''",
        as_dict=True,
    )
    for ws in bad_labels:
        print(f"  • {ws.name}: setting label = {ws.name!r}")
        frappe.db.set_value("Workspace", ws.name, "label", ws.name)

    frappe.db.commit()
    print("\n✅ Fix applied. Run `bench clear-cache` and hard refresh your browser.")


def fix_docstatus():
    """Fix docstatus for Completed/Reconciled trips that are stuck as Draft (docstatus=0)."""
    trips = frappe.db.sql(
        """
        SELECT name, trip_status, docstatus
        FROM `tabDelivery Trip`
        WHERE trip_status IN ('Completed', 'Reconciled')
          AND docstatus = 0
        """,
        as_dict=True,
    )
    if not trips:
        print("✅ No trips need docstatus fix.")
        return

    for t in trips:
        frappe.db.set_value("Delivery Trip", t.name, "docstatus", 1, update_modified=False)
        print(f"  • {t.name}: docstatus 0 → 1 (status={t.trip_status})")

    frappe.db.commit()
    print(f"\n✅ Fixed {len(trips)} trip(s). Run `bench clear-cache` then refresh.")
