"""Surface cleanup rules: whitespace, negation scaffolds, em dashes.

These are deterministic and conservative. The higher-risk ones
(negation-scaffold and em-dash normalisation) are off by default because they
can subtly shift emphasis; the config/preset turns them on.
"""

from __future__ import annotations

import re
from typing import List

from app.core.model import Edit, Paragraph
from .base_rule import Rule


class WhitespaceRule(Rule):
    """Collapse double spaces and remove spaces before punctuation."""

    id = "whitespace_normalization"
    name = "Whitespace normalisation"
    category = "formatting and structure"
    priority = 5
    confidence = "high"

    _MULTISPACE = re.compile(r"  +")
    _SPACE_BEFORE_PUNCT = re.compile(r"\s+([,.;:!?])")

    def propose(self, paragraph: Paragraph) -> List[Edit]:
        text = paragraph.plain_text()
        edits: List[Edit] = []
        for m in self._MULTISPACE.finditer(text):
            edits.append(self.make_edit(
                m.start(), m.end(), " ",
                original=m.group(0), reason="collapsed repeated spaces",
            ))
        for m in self._SPACE_BEFORE_PUNCT.finditer(text):
            edits.append(self.make_edit(
                m.start(), m.end(), m.group(1),
                original=m.group(0), reason="removed space before punctuation",
            ))
        return edits


class NegationScaffoldRule(Rule):
    """Simplify "not just X, but Y" / "not only X but also Y" -> "Y" (rulebook B12)."""

    id = "negation_scaffold"
    name = "Negation-affirmation scaffold removal"
    category = "sentence structure"
    priority = 40
    confidence = "medium"
    default_enabled = False

    # Capture the affirmation Y after the scaffold, up to sentence end.
    # Y is bounded to a single clause (stops at comma/clause end) so the edit
    # stays local instead of swallowing the rest of the sentence.
    _PATTERN = re.compile(
        r"\bnot (?:just|only) [^,.;:]+?,?\s+but(?:\s+also)?\s+(?P<y>[^,.;:!?]+)",
        re.IGNORECASE,
    )

    def propose(self, paragraph: Paragraph) -> List[Edit]:
        if not paragraph.is_editable():
            return []
        text = paragraph.plain_text()
        edits: List[Edit] = []
        for m in self._PATTERN.finditer(text):
            if paragraph.is_protected_range(m.start(), m.end()):
                continue
            y = m.group("y")
            repl = y
            # Capitalise if the scaffold opened the sentence.
            if m.start() == 0 or text[:m.start()].rstrip().endswith((".", "!", "?")):
                repl = y[:1].upper() + y[1:]
            edits.append(self.make_edit(
                m.start(), m.end(), repl,
                original=m.group(0),
                reason="kept affirmation, dropped redundant negation",
            ))
        return edits


class EmDashRule(Rule):
    """Normalise punchy em-dash conclusions to a comma (rulebook B11).

    Only targets an em dash followed by a short (<=4 word) trailing clause that
    ends the sentence -- the "mechanical conclusion" pattern. Em dashes used for
    longer asides are left untouched.
    """

    id = "em_dash_normalization"
    name = "Em-dash conclusion normalisation"
    category = "sentence structure"
    priority = 45
    confidence = "low"
    default_enabled = False

    _PATTERN = re.compile(r"\s*[—–]\s*(?P<tail>(?:\w+\s+){0,3}\w+[.!?])")

    def propose(self, paragraph: Paragraph) -> List[Edit]:
        if not paragraph.is_editable():
            return []
        text = paragraph.plain_text()
        edits: List[Edit] = []
        for m in self._PATTERN.finditer(text):
            if paragraph.is_protected_range(m.start(), m.end()):
                continue
            edits.append(self.make_edit(
                m.start(), m.end(), ", " + m.group("tail"),
                original=m.group(0),
                reason="replaced punchy em dash with comma",
            ))
        return edits
