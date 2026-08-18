"""Compose the A3 plate: mosaic, duotone, caption.

Judging for this piece named three things — composition, colour, finish — so the file
is organised that way.

  colour       A duotone from cold shadow through teal to a warm highlight. Luminance
               still carries the anatomy, and the green is the green the data was
               acquired in. Grey read as undecided; pure fluorescent green is the most
               worn cliche in biology and collapses in CMYK.
  composition  The reference is 2.1:1 and the page is 1.41:1, so vertical space is left
               over whatever you do. It becomes the caption band rather than dead paper.
  finish       A hair of dark between tiles. Butted together the mosaic reads as one
               photograph; separated it reads as what it is — thousands of observations.

Run:  python compose_plate.py [--n 9241] [--gap 0.06] [--preview]
"""
from __future__ import annotations

import argparse
import os

import numpy as np
from PIL import Image, ImageDraw, ImageFont

import build_mosaic as M
import paths

PX_PER_MM = M.PX_PER_MM
A3_W, A3_H = int(M.A3_W_MM * PX_PER_MM), int(M.A3_H_MM * PX_PER_MM)   # 4960 x 3507

DUOTONE = [
    (0.00, (4, 7, 11)), (0.18, (11, 34, 42)), (0.42, (28, 84, 88)),
    (0.66, (92, 148, 137)), (0.86, (186, 209, 189)), (1.00, (246, 243, 233)),
]
INK, TITLE, INK_DIM = (150, 166, 168), (122, 176, 162), (92, 104, 108)

TITLE_TEXT = "T H E   A R C H I V E   D R A W S   I T S E L F"
CREDIT = ("Fly Brain Anatomy: FlyLight Gen1 and Split-GAL4 Imagery, "
          "Janelia Research Campus — CC BY 4.0.")

FONTS = ["/System/Library/Fonts/HelveticaNeue.ttc", "/System/Library/Fonts/Helvetica.ttc",
         "/System/Library/Fonts/Supplemental/Arial.ttf",
         "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"]
FONTS_MONO = ["/System/Library/Fonts/SFNSMono.ttf", "/System/Library/Fonts/Menlo.ttc",
              "/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf"]


def ramp(lum: np.ndarray) -> np.ndarray:
    xs = np.array([a for a, _ in DUOTONE], dtype=np.float32)
    out = np.empty(lum.shape + (3,), dtype=np.uint8)
    for ch in range(3):
        ys = np.array([c[ch] for _, c in DUOTONE], dtype=np.float32)
        out[..., ch] = np.clip(np.interp(lum, xs, ys), 0, 255).astype(np.uint8)
    return out


def font(pt: float, mono: bool = False, bold: bool = False):
    px = int(round(pt * 300 / 72))
    for p in (FONTS_MONO if mono else FONTS):
        if os.path.exists(p):
            for idx in ((2, 0) if bold else (0, 1)):
                try:
                    return ImageFont.truetype(p, px, index=idx)
                except Exception:      # noqa: BLE001
                    continue
    return ImageFont.load_default()


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--n", type=int, default=9241, help="target number of tiles")
    ap.add_argument("--gap", type=float, default=0.06, help="gap as a fraction of tile")
    ap.add_argument("--contrast", type=float, default=2.0, help="tone curve on the target")
    ap.add_argument("--preview", action="store_true", help="skip the full-size PNG")
    a = ap.parse_args()
    paths.ensure()

    ref = M.load_ref()
    rh, rw = ref.shape
    side_margin = int(M.MARGIN_MM * PX_PER_MM)
    bw = A3_W - 2 * side_margin
    bh = int(round(rh * bw / rw))
    cols = max(1, int(round(np.sqrt(a.n * bw / bh))))
    rows = max(1, int(round(a.n / cols)))
    side = int(round(min(bw / cols, bh / rows)))
    cols, rows = int(bw // side), int(bh // side)
    n = cols * rows
    gap = max(1, int(round(side * a.gap)))
    inner = side - gap
    print(f"grid {cols}x{rows} = {n} cells | tile {side}px = {side / PX_PER_MM:.2f} mm "
          f"| gap {gap / PX_PER_MM:.2f} mm")

    tgt = np.asarray(Image.fromarray((ref * 255).astype(np.uint8)).resize(
        (cols, rows), Image.LANCZOS), dtype=np.float32).ravel() / 255.0
    tgt = np.clip(tgt, 0, 1) ** a.contrast     # the reference is bright and flat

    lines = M.tile_lines()
    if len(lines) < n:
        raise SystemExit(f"only {len(lines)} tiles on disk, {n} needed — "
                         f"fetch more or lower --n")
    print(f"loading {len(lines)} tiles at {inner}px ...", flush=True)
    tiles = M.load_tiles(lines, inner)
    lvl = tiles.reshape(len(tiles), -1).mean(axis=1)

    # Spread the choice across the whole brightness range rather than taking the top N.
    pick = np.argsort(lvl, kind="stable")[np.linspace(0, len(tiles) - 1, n).astype(int)]
    tiles, lvl = tiles[pick], lvl[pick]
    used = [lines[i] for i in pick]

    # Brightest cell gets the brightest tile. Rank matching, nothing cleverer.
    place = np.empty(n, dtype=np.int64)
    place[np.argsort(-tgt, kind="stable")] = np.argsort(-lvl, kind="stable")

    slack = A3_H - rows * side
    top = int(round(slack * 0.34))             # brain above centre, caption below
    ox, oy = (A3_W - cols * side) // 2, top

    lum = np.zeros((A3_H, A3_W), dtype=np.float32)
    exps = np.empty(n, dtype=np.float32)
    for k in range(n):
        t = np.clip(tiles[place[k]], 0.0, 1.0)
        p = M.solve_exponent(t, float(tgt[k]))
        exps[k] = p
        r, c = divmod(k, cols)
        y, x = oy + r * side, ox + c * side
        lum[y:y + inner, x:x + inner] = t ** p
    got = np.array([float((np.clip(tiles[place[k]], 0, 1) ** exps[k]).mean())
                    for k in range(n)])
    print(f"tone exponent median {np.median(exps):.2f} "
          f"(quartiles {np.percentile(exps, 25):.2f}-{np.percentile(exps, 75):.2f})")
    print(f"target reproduced: r = {np.corrcoef(got, tgt)[0, 1]:.4f}")

    page = Image.fromarray(ramp(lum))
    d = ImageDraw.Draw(page)

    plate_bottom = oy + rows * side
    spec_px = int(round(17.0 * PX_PER_MM))
    spec_y = plate_bottom + int(round(24.0 * PX_PER_MM))
    x0, tx = ox, ox + spec_px + int(round(6.0 * PX_PER_MM))

    spec_i = int(np.argsort(-lvl)[len(lvl) // 6])
    spec = np.clip(tiles[spec_i], 0, 1) ** M.solve_exponent(np.clip(tiles[spec_i], 0, 1), 0.42)
    page.paste(Image.fromarray(ramp(spec)).resize((spec_px, spec_px), Image.LANCZOS),
               (x0, spec_y))
    d.rectangle([x0, spec_y, x0 + spec_px, spec_y + spec_px], outline=INK_DIM, width=2)

    f_lab, f_eye, f_ttl, f_cap = (font(7.0, mono=True), font(8.5, bold=True),
                                  font(13.0), font(7.5))
    d.text((x0, spec_y + spec_px + int(2.0 * PX_PER_MM)),
           f"{used[spec_i]} · ×6", font=f_lab, fill=INK_DIM)
    d.text((tx, spec_y - int(0.5 * PX_PER_MM)), TITLE_TEXT, font=f_eye, fill=TITLE)
    d.text((tx, spec_y + int(5.0 * PX_PER_MM)),
           f"One fruit fly brain, made of {n:,} pictures of its neurons",
           font=f_ttl, fill=INK)
    mm = side / PX_PER_MM
    for i, ln in enumerate((
            "Each tile is a crop from a fluorescence image showing a different set of "
            "neurons in the Drosophila brain.",
            "The tiles are tone-matched and arranged so that together they reproduce a "
            f"photograph of the brain's own anatomy. Each measures {mm:.1f} mm on this print.",
            CREDIT)):
        d.text((tx, spec_y + int((11.5 + i * 4.2) * PX_PER_MM)), ln, font=f_cap, fill=INK_DIM)

    prev = os.path.join(paths.OUT, "plate_preview.png")
    page.resize((A3_W // 3, A3_H // 3), Image.LANCZOS).save(prev)
    print(f"preview -> {prev}")
    if not a.preview:
        page.save(paths.PLATE_PNG)
        print(f"full {A3_W}x{A3_H} -> {paths.PLATE_PNG} "
              f"({os.path.getsize(paths.PLATE_PNG) / 1e6:.1f} MB)")


if __name__ == "__main__":
    main()
