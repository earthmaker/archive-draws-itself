"""Where things live. Everything is relative to this repository.

Nothing here points outside the checkout, so the pipeline runs from an empty clone.
Override with environment variables if you keep the data elsewhere:

    ADI_DATA=/big/disk/data  ADI_OUT=/big/disk/out  python run_all.py
"""
from __future__ import annotations

import os

ROOT = os.path.dirname(os.path.abspath(__file__))

DATA = os.environ.get("ADI_DATA", os.path.join(ROOT, "data"))
OUT = os.environ.get("ADI_OUT", os.path.join(ROOT, "out"))

TILES = os.path.join(DATA, "tiles")        # downloaded FlyLight brain projections
CACHE = os.path.join(DATA, "cache")        # derived tile array + reference
MANIFEST = os.path.join(ROOT, "manifest", "tiles.tsv")

REF_NPY = os.path.join(CACHE, "ref_neuropil.npy")
REF_PNG = os.path.join(CACHE, "ref_neuropil.png")
REF_RAW = os.path.join(CACHE, "ref_stack.png")

PLATE_PNG = os.path.join(OUT, "plate.png")
PLATE_PDF = os.path.join(OUT, "plate_A3.pdf")


def ensure() -> None:
    for d in (DATA, OUT, TILES, CACHE):
        os.makedirs(d, exist_ok=True)
