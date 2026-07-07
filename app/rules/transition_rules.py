"""Transition simplification (rulebook E25).

Repetitive additive connectives ("Moreover,", "Furthermore,", "Additionally,")
are removed when they open a sentence and merely stack ideas. This is a
medium-confidence change: it alters surface flow but not meaning. It is only
applied when the *same* additive connective is over-used in the document, so a
single well-placed "Moreover," is left alone.
"""

from __future__ import annotations

import re
from typing import List

from app.core.model import Edit, Paragraph
from .base_rule import Rule
from ._util import clean_deletion

# Additive connectives that are safe to drop when redundant.
_ADDITIVE = ["Moreover", "Furthermore", "Additionally", "In addition", "Also"]

_PATTERN = re.compile(
    r"(?:(?<=^)|(?<=[.!?]\s))\s*(" + "|".join(_ADDITIVE) + r")\s*,\s+",
    re.IGNORECASE,
)


class TransitionSimplificationRule(Rule):
    id = "transition_simplification"
    name = "Repetitive transition simplification"
    category = "flow and transitions"
    priority = 20
    confidence = "medium"

    #: Only trim a given connective once its count in the paragraph exceeds this.
    repeat_threshold = 1

    def configure(self, params: dict) -> None:
        super().configure(params)
        self.repeat_threshold = int(params.get("repeat_threshold", self.repeat_threshold))

    def propose(self, paragraph: Paragraph) -> List[Edit]:
        if not paragraph.is_editable():
            return []
        text = paragraph.plain_text()

        matches = list(_PATTERN.finditer(text))
        if not matches:
            return []

        # Count occurrences per connective; only act on over-used ones.
        counts: dict[str, int] = {}
        for m in matches:
            key = m.group(1).lower()
            counts[key] = counts.get(key, 0) + 1

        edits: List[Edit] = []
        seen: dict[str, int] = {}
        for m in matches:
            key = m.group(1).lower()
            if counts[key] <= self.repeat_threshold:
                continue
            # Keep the first occurrence, trim later repeats.
            seen[key] = seen.get(key, 0) + 1
            if seen[key] == 1:
                continue
            # Delete the connective + its comma + following space.
            conn_start = m.start(1)
            del_end = m.end()  # includes ", "
            s, e, repl = clean_deletion(text, conn_start, del_end)
            edits.append(
                self.make_edit(
                    s, e, repl,
                    original=text[conn_start:del_end],
                    reason="removed repeated additive transition",
                )
            )
        return edits
