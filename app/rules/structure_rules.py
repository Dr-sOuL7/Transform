"""Structure observations surfaced as flags rather than auto-edits.

Rewriting these safely needs judgement a deterministic engine can't supply
without risking meaning drift, so v1 *reports* them and lets the user act. This
directly honours the rulebook's "prefer under-editing over over-editing" rule.
"""

from __future__ import annotations

import re
from typing import List

from app.core.model import Paragraph
from .base_rule import Rule, Flag

_SENT_SPLIT = re.compile(r"(?<=[.!?])\s+")
_WORD = re.compile(r"[A-Za-z']+")


def split_sentences(text: str) -> List[str]:
    return [s for s in _SENT_SPLIT.split(text.strip()) if s]


class RepeatedOpenerFlag(Rule):
    id = "repeated_opener"
    name = "Repeated sentence opener"
    category = "sentence structure"

    def flags(self, paragraph: Paragraph) -> List[Flag]:
        if not paragraph.is_editable():
            return []
        sentences = split_sentences(paragraph.plain_text())
        out: List[Flag] = []
        prev_opener = None
        for sent in sentences:
            words = _WORD.findall(sent)
            if not words:
                continue
            opener = words[0].lower()
            if opener == prev_opener and len(opener) > 2:
                out.append(Flag(
                    self.id, paragraph.index,
                    f"consecutive sentences both open with '{words[0]}'",
                    excerpt=sent[:60],
                ))
            prev_opener = opener
        return out


class LongSentenceFlag(Rule):
    id = "long_sentence"
    name = "Overly long sentence"
    category = "sentence structure"
    word_limit = 40

    def configure(self, params: dict) -> None:
        super().configure(params)
        self.word_limit = int(params.get("word_limit", self.word_limit))

    def flags(self, paragraph: Paragraph) -> List[Flag]:
        if not paragraph.is_editable():
            return []
        out: List[Flag] = []
        for sent in split_sentences(paragraph.plain_text()):
            n = len(_WORD.findall(sent))
            if n > self.word_limit:
                out.append(Flag(
                    self.id, paragraph.index,
                    f"sentence runs {n} words; consider splitting",
                    excerpt=sent[:60],
                ))
        return out


class TriadFlag(Rule):
    id = "triad_overuse"
    name = "List-of-three (triad)"
    category = "sentence structure"

    _TRIAD = re.compile(r"\b[\w'-]+,\s+[\w'-]+,?\s+and\s+[\w'-]+")

    def flags(self, paragraph: Paragraph) -> List[Flag]:
        if not paragraph.is_editable():
            return []
        out: List[Flag] = []
        for m in self._TRIAD.finditer(paragraph.plain_text()):
            out.append(Flag(
                self.id, paragraph.index,
                "list-of-three detected; vary if it feels formulaic",
                excerpt=m.group(0)[:60],
            ))
        return out


class MiniSummaryFlag(Rule):
    """Flag a trailing recap sentence (rulebook F32) rather than delete it."""

    id = "mini_summary"
    name = "End-of-paragraph mini-summary"
    category = "redundancy reduction"

    _OPENERS = re.compile(
        r"^(in summary|in conclusion|to summarize|to summarise|to sum up|"
        r"overall|in short|in brief)\b",
        re.IGNORECASE,
    )

    def flags(self, paragraph: Paragraph) -> List[Flag]:
        if not paragraph.is_editable():
            return []
        sentences = split_sentences(paragraph.plain_text())
        if len(sentences) < 2:
            return []
        last = sentences[-1]
        if self._OPENERS.match(last.strip()):
            return [Flag(
                self.id, paragraph.index,
                "trailing mini-summary; drop it unless the format expects a recap",
                excerpt=last[:60],
            )]
        return []


class RestatementFlag(Rule):
    """Flag adjacent sentences that heavily overlap (possible restatement)."""

    id = "restatement"
    name = "Adjacent restatement"
    category = "redundancy reduction"
    overlap_threshold = 0.7

    def configure(self, params: dict) -> None:
        super().configure(params)
        self.overlap_threshold = float(params.get("overlap_threshold", self.overlap_threshold))

    def flags(self, paragraph: Paragraph) -> List[Flag]:
        if not paragraph.is_editable():
            return []
        sentences = split_sentences(paragraph.plain_text())
        out: List[Flag] = []
        prev_words: set | None = None
        for sent in sentences:
            words = {w.lower() for w in _WORD.findall(sent) if len(w) > 3}
            if prev_words and words:
                overlap = len(words & prev_words) / max(1, len(words | prev_words))
                if overlap >= self.overlap_threshold:
                    out.append(Flag(
                        self.id, paragraph.index,
                        "sentence closely restates the previous one; keep only the unique parts",
                        excerpt=sent[:60],
                    ))
            prev_words = words
        return out
