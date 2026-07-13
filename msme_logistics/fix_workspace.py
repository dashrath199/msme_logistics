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
    """List all workspaces — find any with null label."""
    workspaces = frappe.db.sql(
        "SELECT name, label, module, public FROM `tabWorkspace` ORDER BY sequence_id",
        as_dict=True,
    )
    print(f"\n{'='*70}")
    print(f"Found {len(workspaces)} workspace(s):")
    print(f"{'='*70}")
    for ws in workspaces:
        null_flag = " ⚠️ NULL LABEL!" if not ws.label else ""
        print(f"  • {ws.name}: label={ws.label!r}, module={ws.module}, public={ws.public}{null_flag}")
    print(f"{'='*70}\n")

    # Find culprits
    bad = [ws for ws in workspaces if not ws.label]
    if bad:
        print(f"❌ {len(bad)} workspace(s) with null label FOUND — sidebar will crash.")
        for ws in bad:
            print(f"   → Delete with: frappe.delete_doc('Workspace', {ws.name!r}, force=True)")
    else:
        print("✅ No workspaces with null label found. The issue may be a cached asset.")


def fix():
    """Delete workspaces with null labels and set label = name for any that have one missing."""
    bad = frappe.db.sql(
        "SELECT name, label FROM `tabWorkspace` WHERE label IS NULL OR label = ''",
        as_dict=True,
    )
    if not bad:
        print("✅ No workspaces with null/empty label found.")

    for ws in bad:
        print(f"Fix 1: Setting label = {ws.name!r} for workspace {ws.name!r}")
        frappe.db.set_value("Workspace", ws.name, "label", ws.name)

    # Also check Logistics Dashboard specifically
    if frappe.db.exists("Workspace", "Logistics Dashboard"):
        label = frappe.db.get_value("Workspace", "Logistics Dashboard", "label")
        if not label:
            print("⚠️ Logistics Dashboard has null label — setting it now.")
            frappe.db.set_value("Workspace", "Logistics Dashboard", "label", "Logistics Dashboard")
        else:
            print(f"✅ Logistics Dashboard label is OK: {label!r}")

    frappe.db.commit()
    print("\n✅ Fix applied. Run `bench clear-cache` and hard refresh your browser.")
