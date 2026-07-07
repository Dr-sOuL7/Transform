"""Built-in rule presets (design section 10).

These are the *fallback* defaults. If ``presets.yaml`` is present next to this
file, the loader (:mod:`app.configs.loader`) uses that instead, so presets can
be tuned without editing code. A preset is a per-rule enabled map; rules absent
from a preset fall back to their class ``default_enabled``.
"""

from __future__ import annotations

from typing import Dict, List

# Rule ids (kept in one place for reference / validation).
FILLER = "filler_removal"
TRANSITION = "transition_simplification"
WHITESPACE = "whitespace_normalization"
NEGATION = "negation_scaffold"
EMDASH = "em_dash_normalization"
STOCK = "stock_phrase_simplification"
MODIFIER = "redundant_modifier"
REPEATED = "repeated_word"

# Rules the user can toggle in the UI (the edit-producing rules).
EDITABLE_RULES: List[str] = [
    WHITESPACE, REPEATED, FILLER, TRANSITION, STOCK, MODIFIER, NEGATION, EMDASH,
]

PRESETS: Dict[str, Dict[str, bool]] = {
    # Only the safest, highest-confidence edits.
    "conservative": {
        WHITESPACE: True, REPEATED: True, FILLER: True,
        TRANSITION: False, STOCK: False, MODIFIER: False,
        NEGATION: False, EMDASH: False,
    },
    # Sensible default: safe cleanups + transitions + concision.
    "balanced": {
        WHITESPACE: True, REPEATED: True, FILLER: True,
        TRANSITION: True, STOCK: True, MODIFIER: True,
        NEGATION: False, EMDASH: False,
    },
    # More stylistic latitude; still meaning-preserving.
    "strong": {
        WHITESPACE: True, REPEATED: True, FILLER: True,
        TRANSITION: True, STOCK: True, MODIFIER: True,
        NEGATION: True, EMDASH: True,
    },
    # Academic/technical: concision + structure, no scaffold rewrites.
    "academic": {
        WHITESPACE: True, REPEATED: True, FILLER: True,
        TRANSITION: True, STOCK: True, MODIFIER: True,
        NEGATION: False, EMDASH: False,
    },
}


def resolve_enabled(
    preset: str,
    enable: List[str] | None = None,
    disable: List[str] | None = None,
    presets: Dict[str, Dict[str, bool]] | None = None,
) -> Dict[str, bool]:
    """Return the effective enabled map for ``preset`` with overrides applied."""
    table = presets if presets is not None else PRESETS
    if preset not in table:
        raise ValueError(f"unknown preset: {preset}")
    result = dict(table[preset])
    for rule_id in enable or []:
        result[rule_id] = True
    for rule_id in disable or []:
        result[rule_id] = False
    return result
