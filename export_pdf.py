"""Turn the plate into the submitted PDF, and refuse to pass a broken one.

The gates are code, not a checklist. A build that quietly produces a two-page file or
a page 3 mm off A3 is worse than one that fails, so this exits non-zero instead.

⚠️ The caption is rasterised, not vector text. The brief says "image only"; the safest
   reading of that is a PDF with no text layer at all, and at 300 dpi nothing is lost.

Run:  python export_pdf.py [--quality 88]
"""
from __future__ import annotations

import argparse
import os
import sys

from PIL import Image

import paths

DPI = 300.0
A3_W_MM, A3_H_MM = 420.0, 297.0
MAX_MB = 100.0
TOL_MM = 0.6                 # pixel rounding


def gate(ok: bool, name: str, detail: str) -> bool:
    print(f"  {'PASS' if ok else 'FAIL'}  {name:28s} {detail}")
    return ok


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--quality", type=int, default=88)
    a = ap.parse_args()

    if not os.path.exists(paths.PLATE_PNG):
        raise SystemExit("no plate — run:  python compose_plate.py")
    img = Image.open(paths.PLATE_PNG)
    print(f"source {img.size[0]}x{img.size[1]} {img.mode}")

    img.convert("RGB").save(paths.PLATE_PDF, "PDF", resolution=DPI, quality=a.quality)
    size_mb = os.path.getsize(paths.PLATE_PDF) / 1e6
    print(f"pdf -> {paths.PLATE_PDF} ({size_mb:.1f} MB)\n")

    import fitz
    doc = fitz.open(paths.PLATE_PDF)
    page = doc[0]
    w_mm, h_mm = page.rect.width / 72 * 25.4, page.rect.height / 72 * 25.4
    text = page.get_text().strip()

    print("submission gates")
    oks = [
        gate(len(doc) == 1, "single page", f"{len(doc)}"),
        gate(abs(w_mm - A3_W_MM) < TOL_MM and abs(h_mm - A3_H_MM) < TOL_MM,
             "A3 landscape", f"{w_mm:.1f} x {h_mm:.1f} mm"),
        gate(len(text) == 0, "image only", f"{len(text)} extractable characters"),
        gate(size_mb <= MAX_MB, "under 100 MB", f"{size_mb:.1f} MB"),
        gate(abs(img.size[0] / (A3_W_MM / 25.4) - DPI) < 2,
             "300 dpi", f"{img.size[0] / (A3_W_MM / 25.4):.0f}"),
    ]
    doc.close()
    print()
    if not all(oks):
        sys.exit("a gate failed — do not submit this file")
    print("all gates passed")


if __name__ == "__main__":
    main()
