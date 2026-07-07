"""Base class for transformation rules.

A rule inspects a single paragraph and proposes zero or more :class:`Edit`s on
its plain text. Rules never mutate the paragraph directly -- the engine
validates proposals against protected spans, resolves conflicts, and applies
them. This keeps every rule small, independent, and testable.

Rules may also emit *flags*: observations that are reported to the user but not
auto-applied (e.g. "these two sentences open with the same word"). Flagging,
rather than blindly rewriting, is how the engine honours the rulebook's
"prefer under-editing over over-editing" principle for changes that can't be
made deterministically without risking meaning drift.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import List

from app.core.model import Edit, Paragraph


@dataclass
class Flag:
    """A non-destructive observation surfaced in the report."""

    rule_id: str
    paragraph_index: int
    message: str
    excerpt: str = ""


class Rule:
    """Interface every transformation rule implements."""

    id: str = "base"
    name: str = "Base Rule"
    category: str = "general"
    #: Lower numbers run first and win conflict resolution.
    priority: int = 100
    #: Confidence attached to edits this rule emits.
    confidence: str = "high"
    #: Whether the rule is on by default (overridable via config).
    default_enabled: bool = True

    def __init__(self, enabled: bool | None = None, params: dict | None = None):
        self.enabled = self.default_enabled if enabled is None else enabled
        self.params = params or {}
        self.configure(self.params)

    def configure(self, params: dict) -> None:
        """Apply per-rule parameters from config (YAML). Default: no-op.

        Subclasses override this to read tunables (thresholds, extra phrase
        lists, confidence overrides) so behaviour can change without code edits.
        """
        if "confidence" in params:
            self.confidence = params["confidence"]

    def propose(self, paragraph: Paragraph) -> List[Edit]:
        """Return edits this rule would make to ``paragraph`` (may be empty)."""
        return []

    def flags(self, paragraph: Paragraph) -> List[Flag]:
        """Return non-destructive observations for ``paragraph``."""
        return []

    # -- helpers for subclasses ------------------------------------------
    def make_edit(
        self,
        start: int,
        end: int,
        replacement: str,
        original: str,
        reason: str,
    ) -> Edit:
        return Edit(
            start=start,
            end=end,
            replacement=replacement,
            rule_id=self.id,
            category=self.category,
            reason=reason,
            confidence=self.confidence,
            original=original,
        )
