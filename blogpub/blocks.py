"""Center each content block of a handwritten page independently.

A scanned handwritten page usually holds several distinct blocks -- a short
heading, a paragraph, a row of icons, a footer -- separated by vertical
whitespace. Centering the whole page by one global shift can't center each of
those on its own: correcting a left-drifted heading would drag an
already-centered paragraph off to the side.

This module segments the page into blocks by their vertical whitespace gaps
(a row-projection profile: rows with ink vs empty rows; a gap taller than a
threshold starts a new block) and horizontally centers each block on its own,
preserving vertical positions and the gaps between blocks.

Safety rails keep it from looking algorithmic: a dead-zone leaves
already-near-centered blocks untouched, and a max-shift cap stops a wildly
off block from being yanked across the page.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import numpy as np
from PIL import Image


@dataclass(frozen=True)
class BlockShift:
    """Debug record of how one block was moved.

    Parameters
    ----------
    rows : tuple of int
        ``(top, bottom)`` inclusive row range of the block.
    cols : tuple of int
        ``(left, right)`` ink extent of the block.
    raw_shift : int
        The shift that would perfectly center the block.
    applied_shift : int
        The shift actually applied after the dead-zone and cap.
    """

    rows: tuple[int, int]
    cols: tuple[int, int]
    raw_shift: int
    applied_shift: int


def center_blocks(
    in_path: Path,
    out_path: Path,
    *,
    gap_frac: float = 0.022,
    deadzone_frac: float = 0.015,
    max_shift_frac: float = 0.16,
    ink_threshold: int = 128,
) -> list[BlockShift]:
    """Segment a page into vertical blocks and horizontally center each one.

    Parameters
    ----------
    in_path : Path
        Source page PNG (dark ink on a light background).
    out_path : Path
        Where to write the result (may equal ``in_path``).
    gap_frac : float, optional
        A vertical whitespace gap at least this tall (as a fraction of image
        height) starts a new block. ~0.022 groups lines into paragraphs while
        still splitting paragraph-to-paragraph gaps.
    deadzone_frac : float, optional
        Blocks whose required shift is smaller than this (fraction of width)
        are left untouched -- only clear leans get corrected.
    max_shift_frac : float, optional
        A block is never shifted more than this fraction of the width, so a
        wildly-placed block isn't dragged across the page.
    ink_threshold : int, optional
        Grayscale value below which a pixel counts as ink (0-255).

    Returns
    -------
    list of BlockShift
        One record per detected block (for debugging / logging).
    """
    img = Image.open(in_path).convert("L")
    arr = np.asarray(img)
    height, width = arr.shape
    ink = arr < ink_threshold

    gap_thresh = max(8, int(gap_frac * height))
    deadzone = int(deadzone_frac * width)
    max_shift = int(max_shift_frac * width)
    page_center = width / 2.0

    ink_rows = np.flatnonzero(ink.any(axis=1))
    if ink_rows.size == 0:
        img.save(out_path)
        return []

    blocks: list[tuple[int, int]] = []
    start = prev = int(ink_rows[0])
    for r in ink_rows[1:]:
        r = int(r)
        if r - prev - 1 >= gap_thresh:
            blocks.append((start, prev))
            start = r
        prev = r
    blocks.append((start, prev))

    out = np.full_like(arr, 255)
    shifts: list[BlockShift] = []
    for r0, r1 in blocks:
        band = ink[r0 : r1 + 1]
        cols = np.flatnonzero(band.any(axis=0))
        if cols.size == 0:
            continue
        left, right = int(cols[0]), int(cols[-1])
        raw_shift = int(round(page_center - (left + right) / 2.0))

        shift = 0 if abs(raw_shift) < deadzone else raw_shift
        shift = max(-max_shift, min(max_shift, shift))
        # Never push ink off either edge.
        if left + shift < 0:
            shift = -left
        if right + shift > width - 1:
            shift = (width - 1) - right

        src = arr[r0 : r1 + 1]
        if shift == 0:
            out[r0 : r1 + 1] = src
        elif shift > 0:
            out[r0 : r1 + 1, shift:] = src[:, : width - shift]
        else:
            out[r0 : r1 + 1, : width + shift] = src[:, -shift:]

        shifts.append(BlockShift((r0, r1), (left, right), raw_shift, shift))

    Image.fromarray(out).save(out_path)
    return shifts
