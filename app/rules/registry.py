"""Rule registry: the ordered set of rules the engine runs.

Rules are sorted by ``priority`` (lower first) so higher-priority edits win
conflict resolution. ``build_registry`` accepts an optional per-rule enabled
map and a per-rule params map (both typically sourced from YAML config), so the
UI or CLI can toggle *and* tune rules without touching code.
"""

from __future__ import annotations

from typing import Dict, List

from .base_rule import Rule
from .filler_rules import FillerRemovalRule
from .transition_rules import TransitionSimplificationRule
from .cleanup_rules import WhitespaceRule, NegationScaffoldRule, EmDashRule
from .redundancy_rules import (
    StockPhraseRule,
    RedundantModifierRule,
    RepeatedWordRule,
)
from .structure_rules import (
    RepeatedOpenerFlag,
    LongSentenceFlag,
    TriadFlag,
    MiniSummaryFlag,
    RestatementFlag,
)

#: All known rule classes.
ALL_RULES: List[type[Rule]] = [
    WhitespaceRule,
    RepeatedWordRule,
    FillerRemovalRule,
    TransitionSimplificationRule,
    StockPhraseRule,
    RedundantModifierRule,
    NegationScaffoldRule,
    EmDashRule,
    # flag-only observations
    RepeatedOpenerFlag,
    LongSentenceFlag,
    TriadFlag,
    MiniSummaryFlag,
    RestatementFlag,
]


def rule_catalog() -> List[dict]:
    """Metadata for every known rule (for UIs to render toggles/legends)."""
    return [
        {
            "id": cls.id,
            "name": cls.name,
            "category": cls.category,
            "confidence": getattr(cls, "confidence", "high"),
            "default_enabled": cls.default_enabled,
        }
        for cls in ALL_RULES
    ]


def build_registry(
    enabled: Dict[str, bool] | None = None,
    params: Dict[str, dict] | None = None,
) -> List[Rule]:
    """Instantiate rules, apply enabled + params overrides, sort by priority."""
    enabled = enabled or {}
    params = params or {}
    rules = [
        cls(enabled=enabled.get(cls.id), params=params.get(cls.id))
        for cls in ALL_RULES
    ]
    active = [r for r in rules if r.enabled]
    active.sort(key=lambda r: r.priority)
    return active
