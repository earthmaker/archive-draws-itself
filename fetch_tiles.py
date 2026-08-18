"""Download the FlyLight brain projections used as mosaic tiles.

The URLs live in manifest/tiles.tsv — public Janelia addresses, one per driver line,
so nothing here scrapes a website and the set is fixed and reproducible.

    python fetch_tiles.py            # all 9,241 lines (~1.4 GB, tens of minutes)
    python fetch_tiles.py --n 500    # a subset, to try the pipeline quickly

Images are Fly Brain Anatomy: FlyLight Gen1 and Split-GAL4 Imagery,
Janelia Research Campus, CC BY 4.0. They are not redistributed here.
"""
from __future__ import annotations

import argparse
import csv
import os
import ssl
import urllib.request
from concurrent.futures import ThreadPoolExecutor

import paths

UA = "archive-draws-itself/1.0 (reproducible-artwork; +https://github.com/earthmaker/archive-draws-itself)"

try:
    import certifi
    SSL_CTX = ssl.create_default_context(cafile=certifi.where())
except ImportError:
    SSL_CTX = ssl.create_default_context()


def rows():
    with open(paths.MANIFEST, encoding="utf-8") as f:
        for row in csv.DictReader(f, delimiter="\t"):
            yield row["line"], row["url"]


def grab(job) -> str | None:
    line, url = job
    dst = os.path.join(paths.TILES, f"{line}.jpg")
    if os.path.exists(dst) and os.path.getsize(dst) > 1024:
        return None
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    try:
        with urllib.request.urlopen(req, timeout=60, context=SSL_CTX) as r:
            data = r.read()
    except Exception as e:                       # noqa: BLE001
        return f"{line}: {type(e).__name__}"
    with open(dst, "wb") as f:
        f.write(data)
    return None


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--n", type=int, default=0, help="download only the first N lines")
    ap.add_argument("--jobs", type=int, default=8)
    a = ap.parse_args()

    paths.ensure()
    jobs = list(rows())
    if a.n:
        jobs = jobs[:a.n]
    print(f"{len(jobs)} lines -> {paths.TILES}")

    fails = []
    with ThreadPoolExecutor(max_workers=a.jobs) as ex:
        for i, err in enumerate(ex.map(grab, jobs), 1):
            if err:
                fails.append(err)
            if i % 500 == 0:
                print(f"  {i}/{len(jobs)}  failed {len(fails)}", flush=True)

    have = len([f for f in os.listdir(paths.TILES) if f.endswith(".jpg")])
    print(f"\ndone — {have} images on disk, {len(fails)} failures")
    for f in fails[:10]:
        print("  ", f)
if __name__ == "__main__":
    main()
