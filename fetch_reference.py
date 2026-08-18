"""Fetch the reference brain and extract its neuropil channel.

The macro image of the mosaic is a real photograph, not an average: one aligned MCFO
stack from the public FlyLight archive. Its grey channel is the nc82 neuropil
counterstain, so taking min(R, G, B) drops the coloured MCFO neurons and leaves the
anatomy — optic lobes, glomeruli, the oesophageal foramen, the SEZ.

⚠️ This step is not optional decoration. The first versions of the plate used an
   average of the whole collection as the target and were too blurred to read as a
   brain. A single real photograph is what brings the structure back.

Run:  python fetch_reference.py     ->  data/cache/ref_neuropil.npy
"""
from __future__ import annotations

import os
import ssl
import urllib.request

import numpy as np
from PIL import Image

import paths

try:
    import certifi
    SSL_CTX = ssl.create_default_context(cafile=certifi.where())
except ImportError:
    SSL_CTX = ssl.create_default_context()

BASE = ("https://janelia-flylight-imagery.s3.amazonaws.com/"
        "Annotator%20Gen1%20MCFO/R10A06/"
        "R10A06-20161028_28_D1-m-20x-brain-GAL4-JRC2018_MALE_20x_HR")
URL = f"{BASE}-aligned_stack.png"
UA = "archive-draws-itself/1.0 (+https://github.com/earthmaker/archive-draws-itself)"


def main() -> None:
    paths.ensure()
    if not os.path.exists(paths.REF_RAW):
        print(f"downloading {URL}")
        req = urllib.request.Request(URL, headers={"User-Agent": UA})
        with urllib.request.urlopen(req, timeout=120, context=SSL_CTX) as r:
            data = r.read()
        with open(paths.REF_RAW, "wb") as f:
            f.write(data)
        print(f"  {len(data) / 1e6:.1f} MB")
    else:
        print(f"already have {paths.REF_RAW}")

    a = np.asarray(Image.open(paths.REF_RAW).convert("RGB")).astype(np.float32)
    grey = a.min(axis=2)                      # drop the coloured MCFO labels
    m = grey > 12                             # trim the black surround
    ys, xs = np.nonzero(m)
    c = grey[ys.min():ys.max() + 1, xs.min():xs.max() + 1]
    lo, hi = np.percentile(c, 1), np.percentile(c, 99.7)
    g = np.clip((c - lo) / max(hi - lo, 1e-6), 0, 1).astype(np.float32)

    np.save(paths.REF_NPY, g)
    Image.fromarray((g * 255).astype(np.uint8)).save(paths.REF_PNG)
    print(f"reference {g.shape[1]}x{g.shape[0]}, mean {g.mean():.3f} -> {paths.REF_NPY}")
    print("\nImage credit — Fly Brain Anatomy: FlyLight Gen1 and Split-GAL4 Imagery,")
    print("               Janelia Research Campus. CC BY 4.0.")


if __name__ == "__main__":
    main()
