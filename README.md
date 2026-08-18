# The Archive Draws Itself

**One fruit fly brain, made of 8,905 pictures of its neurons.**

A photomosaic in which both the tiles and the picture they reproduce come from the
same public archive. Every tile is one *Drosophila* driver line's fluorescence
projection — a separate experiment, showing a few of the brain's cells and never the
whole organ. Arranged by brightness they rebuild the anatomy they came from.

Submitted to the AI Art Track of AI4Sci Korea 2026.

---

## Reproduce it

```bash
git clone https://github.com/earthmaker/archive-draws-itself
cd archive-draws-itself
pip install -r requirements.txt

python run_all.py --n 800     # a quick look: 800 tiles, a few minutes
python run_all.py             # the real thing: 9,241 tiles, ~1.4 GB, a while
```

Output lands in `out/` — `plate.png` at 4960 × 3507 px and `plate_A3.pdf`, which is
checked against the submission spec before it is allowed to exist.

Nothing points outside the checkout. `data/` and `out/` are created on first run and
are not tracked; images are fetched from Janelia, not redistributed here.

## The pipeline

| step | what it does |
|---|---|
| `fetch_tiles.py` | downloads the projections listed in `manifest/tiles.tsv` |
| `fetch_reference.py` | downloads one aligned stack and pulls its neuropil channel out of the colour |
| `build_mosaic.py` | loading, cropping, and the tone curve — shared helpers |
| `compose_plate.py` | placement, duotone, caption, the A3 page |
| `export_pdf.py` | PDF, plus gates that fail the build rather than ship a bad file |

Roughly 700 lines of Python. It was vibe-coded with Claude (Anthropic) over about six
hours, and most of that time went into the three decisions below.

## Three things that were not obvious

**The macro image cannot be an average.** Averaging the whole collection gives a
plausible-looking brain that is too blurred to read — no part of it is distinct. Using
a single real neuropil photograph instead brings the anatomy back: the two visual
lobes, the central brain, the grooves between them.

**Tiles cannot be whole brains.** Every projection carries the same brain-shaped
silhouette on black. Repeat that shape across a page and it drowns out the picture the
tiles are meant to build — the target is measurably there and still invisible. Cropping
each tile to its central 45 % turns it into texture and the macro image appears.

**Brightness cannot be multiplied.** The tiles are far darker than the photograph they
reproduce. Scaling them up destroys their bright parts — at a 2.5× ceiling, 81 % of
tiles clipped. Each tile is instead lifted along a power curve, which pins black at
black and white at white and preserves the rank of every pixel: tone changes, structure
does not. No pixel is generated; the exponents are reported when the plate is built.

## Licences, in three layers

- **Code** — MIT, see `LICENSE`.
- **Images** — Fly Brain Anatomy: FlyLight Gen1 and Split-GAL4 Imagery, Janelia
  Research Campus, **CC BY 4.0**. Not mine to relicense; fetched at run time.
- **The finished plate** — a derivative of those images, so **CC BY 4.0** as well.

## Citation

Archived on Zenodo with a DOI; see the badge above once released.

Please also credit the FlyLight Project Team at Janelia Research Campus for the
underlying imagery.
