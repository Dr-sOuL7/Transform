"""Shared helpers for regex-based rules.

Contract: a rule matches the *entire* removable chunk, including any trailing
whitespace it wants gone (e.g. ``r"It is important to note that\\s+"``).
:func:`clean_deletion` then decides how to remove it so the surrounding text
still reads correctly -- chiefly, capitalising the next word when the deleted
chunk began a sentence.
"""

from __future__ import annotations

import re

_SENTENCE_END = re.compile(r"[.!?][\"'”’)]?\s*$")


def at_sentence_start(text: str, pos: int) -> bool:
    """Return ``True`` if position ``pos`` begins a sentence in ``text``."""
    if pos == 0:
        return True
    return bool(_SENTENCE_END.search(text[:pos]))


def clean_deletion(text: str, start: int, end: int) -> tuple[int, int, str]:
    """Delete ``[start, end)`` cleanly; returns ``(start, end, replacement)``.

    If the chunk starts a sentence and a word follows, that word's first letter
    is capitalised (the span extends by one to rewrite it).
    """
    if at_sentence_start(text, start) and end < len(text) and text[end].isalpha():
        return start, end + 1, text[end].upper()
    return start, end, ""
