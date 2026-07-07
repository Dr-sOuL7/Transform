"""Apply plain-text span :class:`Edit`s back onto a paragraph's runs.

Rules operate on the paragraph's plain text and emit ``(start, end,
replacement)`` edits. This module:

1. :func:`plan_edits` -- drops edits overlapping protected content and resolves
   conflicts between overlapping proposals.
2. :func:`simulate_text` -- computes the resulting plain text *without* touching
   the document, so the validator can vet it first.
3. :func:`apply_resolved` -- rewrites the underlying runs in place, preserving
   the formatting of text outside each edited span.
"""

from __future__ import annotations

from typing import List

from .model import Edit, Paragraph


def plan_edits(paragraph: Paragraph, edits: List[Edit]) -> List[Edit]:
    """Return the accepted, conflict-free, protection-safe edits (sorted)."""
    safe = [e for e in edits if not paragraph.is_protected_range(e.start, e.end)]
    accepted: List[Edit] = []
    for edit in safe:
        if edit.start == edit.end and not edit.replacement:
            continue
        if any(edit.overlaps(a) for a in accepted):
            continue
        accepted.append(edit)
    accepted.sort(key=lambda e: e.start)
    return accepted


def simulate_text(text: str, resolved: List[Edit]) -> str:
    """Return ``text`` with ``resolved`` edits applied (right-to-left)."""
    for edit in sorted(resolved, key=lambda e: e.start, reverse=True):
        text = text[: edit.start] + edit.replacement + text[edit.end:]
    return text


def _run_bounds(paragraph: Paragraph) -> List[tuple[int, int]]:
    bounds = []
    cursor = 0
    for run in paragraph.runs:
        bounds.append((cursor, cursor + len(run.text)))
        cursor += len(run.text)
    return bounds


def apply_resolved(paragraph: Paragraph, resolved: List[Edit]) -> None:
    """Apply already-planned ``resolved`` edits to the paragraph's runs."""
    if not resolved:
        return
    for edit in sorted(resolved, key=lambda e: e.start, reverse=True):
        _apply_one(paragraph, edit)
    for run in paragraph.runs:
        if run.obj is not None:
            run.obj.text = run.text
    paragraph.applied_edits.extend(resolved)


def _apply_one(paragraph: Paragraph, edit: Edit) -> None:
    bounds = _run_bounds(paragraph)
    start, end = edit.start, edit.end

    first_idx = None
    for i, (rs, re) in enumerate(bounds):
        intersects = rs < end and re > start
        insertion_here = start == end and rs <= start <= re
        if not (intersects or insertion_here):
            continue
        if first_idx is None:
            first_idx = i
        rel_start = max(start - rs, 0)
        rel_end = min(end - rs, len(paragraph.runs[i].text))
        if i == first_idx:
            prefix = paragraph.runs[i].text[:rel_start]
            suffix = paragraph.runs[i].text[rel_end:]
            paragraph.runs[i].text = prefix + edit.replacement + suffix
        else:
            paragraph.runs[i].text = paragraph.runs[i].text[rel_end:]

    if first_idx is None and paragraph.runs:
        paragraph.runs[-1].text += edit.replacement
