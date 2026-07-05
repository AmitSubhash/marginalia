# handwritten-blog

A blog written entirely by hand on a reMarkable tablet, published as a plain
static site via GitHub Pages. Inspired by
[handwritten.danieljanus.pl](https://handwritten.danieljanus.pl/).

## How it works

1. Create a folder named **"Blog"** on your reMarkable (via the normal UI —
   New Folder).
2. File any notebook you want published into that folder.
3. Run `python generate.py`. It pulls those notebooks over SSH, converts
   each page to a PNG via [`rmc`](https://github.com/ricklupton/rmc) +
   `rsvg-convert`, and writes a static site into `docs/`.
4. Commit and push — GitHub Pages serves straight from `docs/` on `main`.

Only notebooks explicitly filed into the "Blog" folder are ever published.
Everything else on the tablet stays private.

## Requirements

- SSH access to the tablet (see [rmscribe](https://github.com/AmitSubhash/rmscribe)
  for the same SSH setup)
- `rsync`, `rsvg-convert` (`brew install librsvg`)
- Python 3.10+

## Setup

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python generate.py
```

## Future ideas (not yet built)

- **Hyperlinks in handwriting**: [danieljanus's implementation](https://handwritten.danieljanus.pl/2022-10-01-hyperlinks-in-handwriting.html)
  overlays clickable HTML image-map regions on top of the page PNGs at
  manually-identified pixel coordinates. A lower-effort automated version
  could ask Claude's vision model for approximate bounding boxes of any
  URLs/references written on the page, at the cost of some positioning
  imprecision -- untested.
