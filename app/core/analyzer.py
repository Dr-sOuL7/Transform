"""Structural analyzer (rulebook + design section 5B).

Labels the document before any rewriting: coarse type, tone, and a handful of
statistics that inform which rules should run and that the report surfaces. It
does not modify the document.
"""

from __future__ import annotations

import re
from typing import Dict

from .model import BlockType, Document
from . import protection

_SENT_SPLIT = re.compile(r"(?<=[.!?])\s+")
_WORD = re.compile(r"[A-Za-z']+")

_FILLER_HINT = re.compile(
    r"it is important to note|it should be noted|needless to say|"
    r"at the end of the day|for all intents",
    re.IGNORECASE,
)
_TRANSITION_HINT = re.compile(
    r"\b(moreover|furthermore|additionally|in addition)\b", re.IGNORECASE
)
_CONVERSATIONAL = re.compile(r"\b(you|your|we|our|I'm|don't|can't|it's)\b", re.IGNORECASE)


def analyze(document: Document) -> Dict:
    """Compute stats + type/tone, store them on ``document``, return the stats."""
    body_text = "\n".join(
        p.plain_text() for p in document.paragraphs if p.block_type != BlockType.HEADING
    )
    sentences = [s for s in _SENT_SPLIT.split(body_text) if s.strip()]
    sent_lengths = [len(_WORD.findall(s)) for s in sentences] or [0]
    word_count = sum(sent_lengths)

    citation_count = sum(
        1
        for p in document.paragraphs
        for span in protection.detect_spans(p.plain_text())
        if span.category.value in ("citation", "reference")
    )

    stats = {
        "paragraphs": len(document.paragraphs),
        "headings": sum(1 for p in document.paragraphs if p.block_type == BlockType.HEADING),
        "sentences": len(sentences),
        "words": word_count,
        "avg_sentence_len": round(sum(sent_lengths) / len(sent_lengths), 1),
        "max_sentence_len": max(sent_lengths),
        "filler_hits": len(_FILLER_HINT.findall(body_text)),
        "transition_hits": len(_TRANSITION_HINT.findall(body_text)),
        "citations": citation_count,
    }

    document.doc_type = _infer_type(body_text, citation_count)
    document.tone = _infer_tone(body_text)
    document.stats = stats
    return stats


def _infer_type(text: str, citation_count: int) -> str:
    if citation_count >= 2:
        return "academic"
    conversational = len(_CONVERSATIONAL.findall(text))
    if conversational > max(1, len(text.split()) // 40):
        return "conversational"
    if re.search(r"```|def |function |import |SELECT |;\s*$", text):
        return "technical"
    return "general"


def _infer_tone(text: str) -> str:
    contractions = len(re.findall(r"\b\w+'(?:s|t|re|ve|ll|d|m)\b", text))
    first_person = len(re.findall(r"\bI\b|\bwe\b", text, re.IGNORECASE))
    if contractions > 3 or first_person > 5:
        return "conversational"
    return "formal"
