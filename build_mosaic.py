"""Loading and preparing the pieces of the mosaic.

Two jobs only, both shared with compose_plate.py:

  load_ref()    the macro image — a real neuropil photograph, cropped to the tissue
  load_tiles()  the tiles — one fluorescence projection per driver line

⚠️ Tiles are cropped to their central 45 %. Used whole, every tile carries the same
   brain-shaped silhouette; repeated across the page that one shape drowns out the
   picture the tiles are supposed to build. Cropping turns each tile into texture.
   The macro image is carried by tone, not by the outline of each piece.
"""
from __future__ import annotations

import os

import numpy as np
from PIL import Image

import paths

PX_PER_MM = 300.0 / 25.4          # 300 dpi, expressed in millimetres
A3_W_MM, A3_H_MM = 420.0, 297.0   # landscape
MARGIN_MM = 12.0
DECODE = 256                      # JPEG draft decode size; tiles end up much smaller
CROP = 0.45                       # central fraction of each source image kept


def load_ref() -> np.ndarray:
    """Reference photograph, background trimmed. Values in [0, 1]."""
    if not os.path.exists(paths.REF_NPY):
        raise SystemExit("reference missing — run:  python fetch_reference.py")
    g = np.load(paths.REF_NPY)
    m = g > 0.06
    ys, xs = np.nonzero(m)
    return g[ys.min():ys.max() + 1, xs.min():xs.max() + 1]


def tile_lines() -> list[str]:
    """Driver lines that have an image on disk, in a fixed order."""
    if not os.path.isdir(paths.TILES):
        raise SystemExit("no tiles — run:  python fetch_tiles.py")
    names = sorted(f[:-4] for f in os.listdir(paths.TILES) if f.endswith(".jpg"))
    if not names:
        raise SystemExit("no tiles — run:  python fetch_tiles.py")
    return names


def load_tiles(lines: list[str], px: int, crop: float = CROP) -> np.ndarray:
    """Read each image, keep its central `crop`, shrink to `px`. No per-tile contrast."""
    out = np.zeros((len(lines), px, px), dtype=np.float32)
    for i, ln in enumerate(lines):
        with Image.open(os.path.join(paths.TILES, f"{ln}.jpg")) as im:
            im.draft("L", (DECODE, DECODE))     # decode small: most of the speed
            a = im.convert("L")
            if crop < 1.0:
                w, h = a.size
                s = int(min(w, h) * crop)
                a = a.crop(((w - s) // 2, (h - s) // 2, (w + s) // 2, (h + s) // 2))
            a = a.resize((px, px), Image.LANCZOS)
        out[i] = np.asarray(a, dtype=np.float32) / 255.0
        if (i + 1) % 2000 == 0:
            print(f"    {i + 1}/{len(lines)} tiles", flush=True)
    return out


def solve_exponent(t: np.ndarray, want: float) -> float:
    """Find p so that mean(t**p) == want.

    ⚠️ Tiles are far darker than the photograph they must reproduce, and multiplying
    their brightness destroys the bright parts — measured, 81 % of tiles clipped even
    at a 2.5x ceiling. A power curve fixes 0 at 0 and 1 at 1 and preserves the rank of
    every pixel, so a tile can be lifted without anything being erased or invented.
    """
    if want <= 1e-4:
        return 8.0
    lo, hi = 0.05, 12.0
    for _ in range(24):
        mid = (lo + hi) / 2
        lo, hi = (mid, hi) if (t ** mid).mean() > want else (lo, mid)
    return (lo + hi) / 2
