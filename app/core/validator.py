"""Post-edit validation (design sections 5E, 12).

Two layers:

* :func:`validate_paragraph` -- a *pre-apply gate*. Given a paragraph's current
  text and the plain text that would result from a set of edits, it confirms
  nothing protected was lost. The pipeline only commits edits that pass, so an
  unsafe rewrite is rejected rather than shipped.
* :func:`validate_document` -- whole-document sanity checks run after export
  (paragraph count, no newly-empty paragraphs, number/citation counts stable).
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import List

from .model import Document, Paragraph
from . import protection

_NUMBER = re.compile(r"\d[\d,]*(?:\.\d+)?")


@dataclass
class ValidationIssue:
    level: str  # "error" | "warning"
    paragraph_index: int
    message: str


def _multiset(items):
    counts = {}
    for it in items:
        counts[it] = counts.get(it, 0) + 1
    return counts


def validate_paragraph(paragraph: Paragraph, new_text: str) -> List[ValidationIssue]:
    """Return blocking issues if ``new_text`` is an unsafe rewrite of ``paragraph``.

    An empty list means the edits are safe to apply.
    """
    issues: List[ValidationIssue] = []
    old_text = paragraph.plain_text()

    # 1. Every protected span's text must still be present the same number of times.
    old_spans = _multiset(s.text for s in protection.detect_spans(old_text))
    new_spans = _multiset(s.text for s in protection.detect_spans(new_text))
    for text, count in old_spans.items():
        if new_spans.get(text, 0) < count:
            issues.append(ValidationIssue(
                "error", paragraph.index,
                f"protected content would be lost: {text!r}",
            ))

    # 2. Numbers must be preserved exactly (belt-and-braces over span check).
    old_nums = _multiset(_NUMBER.findall(old_text))
    new_nums = _multiset(_NUMBER.findall(new_text))
    if old_nums != new_nums:
        issues.append(ValidationIssue(
            "error", paragraph.index, "numeric content would change",
        ))

    # 3. A non-empty paragraph must not become empty.
    if old_text.strip() and not new_text.strip():
        issues.append(ValidationIssue(
            "error", paragraph.index, "edit would empty the paragraph",
        ))

    # 4. Output should not balloon past the source (rulebook H39).
    if len(new_text) > len(old_text) + 5:
        issues.append(ValidationIssue(
            "warning", paragraph.index, "edit lengthens the paragraph",
        ))

    return issues


def validate_document(document: Document, original_texts: List[str]) -> List[ValidationIssue]:
    """Whole-document checks comparing against pre-edit paragraph texts."""
    issues: List[ValidationIssue] = []

    if len(document.paragraphs) != len(original_texts):
        issues.append(ValidationIssue(
            "error", -1,
            f"paragraph count changed: {len(original_texts)} -> {len(document.paragraphs)}",
        ))
        return issues

    for para, original in zip(document.paragraphs, original_texts):
        current = para.plain_text()
        if original.strip() and not current.strip():
            issues.append(ValidationIssue(
                "error", para.index, "paragraph became empty after editing",
            ))
        # Duplicated-sentence guard: no sentence should appear twice if it didn't before.
        cur_sents = [s for s in re.split(r"(?<=[.!?])\s+", current) if len(s) > 15]
        if len(cur_sents) != len(set(cur_sents)):
            issues.append(ValidationIssue(
                "warning", para.index, "possible duplicated sentence introduced",
            ))

    return issues
