"""Crop a post's handwritten title -- its first ink block -- for the index.

The index should read as your own hand, not a typeset (or worse, a fake
handwriting-font) list. So instead of a font, each post's title in the index is
the *actual* first line of ink from its first page, cropped out.

A "title" is the first block the page segmenter finds (see :mod:`blocks`),
accepted only if it's short enough to be a heading rather than body text and
there's a distinct body block after it. Otherwise there's no clean title to
crop and the caller falls back to the typeset notebook name.
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
from PIL import Image

from .blocks import (
    GAP_FLOOR_PX,
    GAP_FRAC,
    INK_THRESHOLD,
    MIN_INK_ROW_FRAC,
    _segment,
)

TITLE_MAX_HEIGHT_FRAC = 0.20  # a first block taller than this is body text, not a title
TITLE_PAD_PX = 10  # breathing room around the cropped title ink


def crop_title(
    page_png: Path, out_png: Path, *, ink_threshold: int = INK_THRESHOLD
) -> bool:
    """Crop the handwritten title (first ink block) from a post's first page.

    Parameters
    ----------
    page_png : Path
        The post's first page image (already trimmed/centered).
    out_png : Path
        Where to write the cropped title strip.
    ink_threshold : int, optional
        Grayscale value below which a pixel counts as ink (0-255).

    Returns
    -------
    bool
        True if a title strip was written; False if the page has no clean
        title block (caller should fall back to the typeset name).
    """
    img = Image.open(page_png).convert("L")
    arr = np.asarray(img)
    height, width = arr.shape
    ink = arr < ink_threshold

    gap_thresh = max(GAP_FLOOR_PX, int(GAP_FRAC * height))
    min_ink_px = max(3, int(MIN_INK_ROW_FRAC * width))
    blocks = _segment(ink, gap_thresh, min_ink_px)

    # Need a distinct title block plus at least one body block below it.
    if len(blocks) < 2:
        return False
    r0, r1 = blocks[0]
    if (r1 - r0 + 1) > TITLE_MAX_HEIGHT_FRAC * height:
        return False  # first block is too tall to be a heading

    cols = np.flatnonzero(ink[r0 : r1 + 1].any(axis=0))
    if cols.size == 0:
        return False
    c0, c1 = int(cols[0]), int(cols[-1])

    top = max(0, r0 - TITLE_PAD_PX)
    bottom = min(height, r1 + 1 + TITLE_PAD_PX)
    left = max(0, c0 - TITLE_PAD_PX)
    right = min(width, c1 + 1 + TITLE_PAD_PX)
    img.crop((left, top, right, bottom)).save(out_png)
    return True
