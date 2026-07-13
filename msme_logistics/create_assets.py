"""Generate placeholder asset images for msme_logistics app.

Usage:
    bench --site mysite.local execute msme_logistics.create_assets.run
"""

import os
import struct
import zlib

import frappe


def _create_png(width, height, r, g, b):
    """Create a minimal valid PNG of a solid color."""
    def chunk(chunk_type, data):
        c = chunk_type + data
        return struct.pack(">I", len(data)) + c + struct.pack(">I", zlib.crc32(c) & 0xFFFFFFFF)

    header = b"\x89PNG\r\n\x1a\n"
    ihdr = chunk(b"IHDR", struct.pack(">IIBBBBB", width, height, 8, 2, 0, 0, 0))

    raw = b""
    for _ in range(height):
        raw += b"\x00"  # filter none
        for _ in range(width):
            raw += bytes([r, g, b])

    idat = chunk(b"IDAT", zlib.compress(raw))
    iend = chunk(b"IEND", b"")
    return header + ihdr + idat + iend


def run():
    app_path = frappe.get_app_path("msme_logistics")
    public_path = os.path.join(app_path, "public")

    splash_path = os.path.join(public_path, "splash.png")
    if not os.path.exists(splash_path):
        png = _create_png(256, 256, 79, 70, 229)  # Indigo blue
        with open(splash_path, "wb") as f:
            f.write(png)
        print(f"Created {splash_path}")

    favicon_path = os.path.join(public_path, "favicon.ico")
    if not os.path.exists(favicon_path):
        # ICO is just a PNG wrapped in ICO header
        png = _create_png(32, 32, 79, 70, 229)  # Same indigo
        # ICO header: reserved(2) + type=1(2) + count=1(2)
        # ICO entry: w(1) + h(1) + palette(1) + reserved(1) + planes(2) + bpp(2) + size(4) + offset(4)
        ico_header = struct.pack("<HHH", 0, 1, 1)
        ico_entry = struct.pack("<BBBBHHII", 32, 32, 0, 0, 1, 32, len(png), 22)
        ico = ico_header + ico_entry + png
        with open(favicon_path, "wb") as f:
            f.write(ico)
        print(f"Created {favicon_path}")

    print("All assets created.")
