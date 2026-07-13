"""Import fixtures for msme_logistics into the database.

Run after install if fixtures weren't loaded properly:
    bench --site mysite.local execute msme_logistics.load_fixtures.run
"""

import os
import json

import frappe
from frappe.core.utils import find
from frappe.modules.import_file import import_file_by_path
from frappe.custom.doctype.custom_field.custom_field import create_custom_fields


def run():
    """Import all fixture files for msme_logistics."""
    app = frappe.get_app_path("msme_logistics")
    fixtures_dir = os.path.join(app, "fixtures")
    imported = 0
    skipped = 0

    if not os.path.exists(fixtures_dir):
        print(f"Fixtures directory not found: {fixtures_dir}")
        return

    for fname in sorted(os.listdir(fixtures_dir)):
        if not fname.endswith(".json"):
            continue

        fpath = os.path.join(fixtures_dir, fname)
        with open(fpath) as f:
            data = json.load(f)

        doctype = data.get("doctype")
        name = data.get("name")

        if not doctype or not name:
            print(f"⚠️  Skipping {fname}: missing doctype or name")
            skipped += 1
            continue

        if frappe.db.exists(doctype, name):
            print(f"⏭️  {doctype} '{name}' already exists — skipping")
            skipped += 1
            continue

        try:
            doc = frappe.get_doc(data)
            doc.flags.ignore_permissions = True
            doc.flags.ignore_mandatory = True
            doc.insert()
            print(f"✅ Created {doctype} '{name}'")
            imported += 1
        except Exception as e:
            print(f"❌ Failed to create {doctype} '{name}': {e}")
            skipped += 1

    frappe.db.commit()
    print(f"\n{'='*50}")
    print(f"Done: {imported} imported, {skipped} skipped")
    print(f"{'='*50}")
