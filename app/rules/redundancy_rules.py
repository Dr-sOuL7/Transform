"""Conciseness and redundancy rules (rulebook D24, F29).

All three are deterministic and meaning-preserving:

* :class:`StockPhraseRule` swaps wordy fixed phrases for concise equivalents
  ("due to the fact that" -> "because").
* :class:`RedundantModifierRule` removes tautological modifiers
  ("very unique" -> "unique", "end result" -> "result").
* :class:`RepeatedWordRule` fixes accidental function-word doubling
  ("the the" -> "the"), restricted to words where doubling is virtually
  always a typo (so grammatical "had had" / "that that" are left alone).

Edits that overlap protected content are dropped by the engine, so numbers,
citations, and quotes are never touched.
"""

from __future__ import annotations

import re
from typing import Dict, List

from app.core.model import Edit, Paragraph
from .base_rule import Rule
from ._util import cap_like

# --- wordy phrase -> concise equivalent --------------------------------------
_STOCK: Dict[str, str] = {
    "due to the fact that": "because",
    "owing to the fact that": "because",
    "in view of the fact that": "because",
    "in spite of the fact that": "although",
    "despite the fact that": "although",
    "in the event that": "if",
    "in the case that": "if",
    "for the purpose of": "for",
    "with regard to": "regarding",
    "with respect to": "regarding",
    "in relation to": "about",
    "a large number of": "many",
    "a great deal of": "much",
    "the majority of": "most",
    "a majority of": "most",
    "at this point in time": "now",
    "at the present time": "now",
    "in the near future": "soon",
    "on a regular basis": "regularly",
    "in a timely manner": "promptly",
    "has the ability to": "can",
    "have the ability to": "can",
    "is able to": "can",
    "are able to": "can",
    "as to whether": "whether",
    "in the process of": "",
    "a sufficient number of": "enough",
    "in order for": "for",
}

# --- redundant / tautological modifier -> head noun --------------------------
_MODIFIER: Dict[str, str] = {
    "very unique": "unique",
    "absolutely essential": "essential",
    "completely eliminate": "eliminate",
    "end result": "result",
    "final outcome": "outcome",
    "past history": "history",
    "advance planning": "planning",
    "close proximity": "proximity",
    "each and every": "every",
    "basic fundamentals": "fundamentals",
    "future plans": "plans",
    "unexpected surprise": "surprise",
    "free gift": "gift",
    "added bonus": "bonus",
    "new innovation": "innovation",
    "revert back": "revert",
    "join together": "join",
    "brief summary": "summary",
}

_SAFE_DOUBLE = {
    "the", "a", "an", "and", "of", "to", "in", "on", "for", "with", "at",
    "by", "but", "or", "as", "is", "are", "was", "were", "be", "it", "we",
    "you", "they", "he", "she",
}
_DOUBLE = re.compile(r"\b(\w+)(\s+)(\1)\b", re.IGNORECASE)


def _compile_map(mapping: Dict[str, str]) -> List[tuple[re.Pattern, str]]:
    return [
        (re.compile(r"\b" + re.escape(phrase) + r"\b", re.IGNORECASE), repl)
        for phrase, repl in mapping.items()
    ]


class _PhraseMapRule(Rule):
    """Shared machinery: replace matches of a phrase->replacement map."""

    _compiled: List[tuple[re.Pattern, str]] = []
    _reason = "simplified wordy phrase"

    def configure(self, params: dict) -> None:
        super().configure(params)
        extra = params.get("extra") or {}
        base = dict(self._base_map())
        base.update(extra)
        self._compiled = _compile_map(base)

    def _base_map(self) -> Dict[str, str]:
        return {}

    def propose(self, paragraph: Paragraph) -> List[Edit]:
        if not paragraph.is_editable():
            return []
        text = paragraph.plain_text()
        edits: List[Edit] = []
        for pattern, repl in self._compiled:
            for m in pattern.finditer(text):
                original = m.group(0)
                replacement = cap_like(original, repl)
                start, end = m.start(), m.end()
                # If we're deleting the phrase entirely, also swallow one space.
                if replacement == "" and end < len(text) and text[end] == " ":
                    end += 1
                edits.append(self.make_edit(
                    start, end, replacement, original=original, reason=self._reason,
                ))
        return edits


class StockPhraseRule(_PhraseMapRule):
    id = "stock_phrase_simplification"
    name = "Wordy-phrase simplification"
    category = "redundancy reduction"
    priority = 25
    confidence = "medium"
    _reason = "replaced wordy phrase with concise equivalent"

    def _base_map(self) -> Dict[str, str]:
        return _STOCK


class RedundantModifierRule(_PhraseMapRule):
    id = "redundant_modifier"
    name = "Redundant modifier removal"
    category = "redundancy reduction"
    priority = 26
    confidence = "medium"
    _reason = "removed redundant/tautological modifier"

    def _base_map(self) -> Dict[str, str]:
        return _MODIFIER


class RepeatedWordRule(Rule):
    id = "repeated_word"
    name = "Repeated-word cleanup"
    category = "redundancy reduction"
    priority = 8
    confidence = "high"

    def propose(self, paragraph: Paragraph) -> List[Edit]:
        text = paragraph.plain_text()
        edits: List[Edit] = []
        for m in _DOUBLE.finditer(text):
            if m.group(1).lower() not in _SAFE_DOUBLE:
                continue
            # Keep the first occurrence; delete the whitespace + duplicate.
            edits.append(self.make_edit(
                m.start(2), m.end(3), "",
                original=m.group(0),
                reason="removed accidental repeated word",
            ))
        return edits
