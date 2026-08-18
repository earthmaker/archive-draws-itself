"""Everything, in order, from an empty checkout.

    python run_all.py            full run (downloads ~1.4 GB, takes a while)
    python run_all.py --n 800    small run, to see the machinery work

Steps: fetch tiles -> fetch reference -> compose plate -> export PDF.
Each step skips work it has already done, so re-running is cheap.
"""
from __future__ import annotations

import argparse
import subprocess
import sys
import os

HERE = os.path.dirname(os.path.abspath(__file__))


def run(*args: str) -> None:
    print(f"\n$ python {' '.join(args)}", flush=True)
    r = subprocess.run([sys.executable, *[os.path.join(HERE, args[0])], *args[1:]])
    if r.returncode != 0:
        sys.exit(f"step failed: {args[0]}")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--n", type=int, default=0, help="use only N lines (quick trial)")
    a = ap.parse_args()

    run("fetch_tiles.py", *(["--n", str(a.n)] if a.n else []))
    run("fetch_reference.py")
    run("compose_plate.py", *(["--n", str(a.n)] if a.n else []))
    run("export_pdf.py")
    print("\ndone — see out/")


if __name__ == "__main__":
    main()
