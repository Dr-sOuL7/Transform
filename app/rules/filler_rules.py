"""Filler / throat-clearing removal (rulebook F29)."""

from __future__ import annotations

import re
from typing import List

from app.core.model import Edit, Paragraph
from .base_rule import Rule
from ._util import clean_deletion

# Phrases that add framing but no meaning. Each pattern includes its trailing
# whitespace so deletion leaves clean spacing. Ordered longest-first is not
# required because conflict resolution handles overlaps.
_FILLER_PHRASES = [
    r"It is important to note that\s+",
    r"It is worth noting that\s+",
    r"It is worth mentioning that\s+",
    r"It should be noted that\s+",
    r"It must be noted that\s+",
    r"It is interesting to note that\s+",
    r"It goes without saying that\s+",
    r"Needless to say,\s+",
    r"As a matter of fact,\s+",
    r"For all intents and purposes,\s+",
    r"Please note that\s+",
    r"It is important to (?:realize|realise|understand|remember) that\s+",
    r"When all is said and done,\s+",
    r"At the end of the day,\s+",
    r"In order to\b",  # -> "to" (handled specially below)
]

_INORDER = re.compile(r"\bin order to\b", re.IGNORECASE)
_COMPILED = [re.compile(p, re.IGNORECASE) for p in _FILLER_PHRASES if "In order to" not in p]


class FillerRemovalRule(Rule):
    id = "filler_removal"
    name = "Filler / throat-clearing removal"
    category = "redundancy reduction"
    priority = 10
    confidence = "high"

    def propose(self, paragraph: Paragraph) -> List[Edit]:
        if not paragraph.is_editable():
            return []
        text = paragraph.plain_text()
        edits: List[Edit] = []

        for pattern in _COMPILED:
            for m in pattern.finditer(text):
                s, e, repl = clean_deletion(text, m.start(), m.end())
                edits.append(
                    self.make_edit(
                        s, e, repl,
                        original=text[m.start():m.end()],
                        reason="removed empty framing phrase",
                    )
                )

        # "In order to" -> "to": trim the redundant "In order " prefix.
        for m in _INORDER.finditer(text):
            # Keep "to"; delete "In order " (start .. start+9).
            phrase_end = m.start() + len("In order ")
            s, e, repl = clean_deletion(text, m.start(), phrase_end)
            edits.append(
                self.make_edit(
                    s, e, repl,
                    original=text[m.start():m.end()],
                    reason="'in order to' simplified to 'to'",
                )
            )

        return edits
