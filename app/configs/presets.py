"""Rule presets (design section 10).

A preset is a per-rule enabled map. Rules absent from a preset fall back to
their class ``default_enabled``. ``resolve_enabled`` layers explicit
``--enable``/``--disable`` flags on top of the chosen preset.

These presets are intentionally coded in Python for v1; Phase 2 moves them to
YAML/JSON without changing the interface.
"""

from __future__ import annotations

from typing import Dict, List

# Rule ids (kept in one place for reference / validation).
FILLER = "filler_removal"
TRANSITION = "transition_simplification"
WHITESPACE = "whitespace_normalization"
NEGATION = "negation_scaffold"
EMDASH = "em_dash_normalization"

# Rules the user can toggle in the UI (the edit-producing rules).
EDITABLE_RULES: List[str] = [WHITESPACE, FILLER, TRANSITION, NEGATION, EMDASH]

PRESETS: Dict[str, Dict[str, bool]] = {
    # Only the safest, highest-confidence edits.
    "conservative": {
        WHITESPACE: True,
        FILLER: True,
        TRANSITION: False,
        NEGATION: False,
        EMDASH: False,
    },
    # Sensible default: safe cleanups + transition trimming.
    "balanced": {
        WHITESPACE: True,
        FILLER: True,
        TRANSITION: True,
        NEGATION: False,
        EMDASH: False,
    },
    # More stylistic latitude; still meaning-preserving.
    "strong": {
        WHITESPACE: True,
        FILLER: True,
        TRANSITION: True,
        NEGATION: True,
        EMDASH: True,
    },
    # Academic/technical: structure over word-swapping; leave scaffolds alone.
    "academic": {
        WHITESPACE: True,
        FILLER: True,
        TRANSITION: True,
        NEGATION: False,
        EMDASH: False,
    },
}


def resolve_enabled(
    preset: str, enable: List[str] | None = None, disable: List[str] | None = None
) -> Dict[str, bool]:
    """Return the effective enabled map for ``preset`` with overrides applied."""
    if preset not in PRESETS:
        raise ValueError(f"unknown preset: {preset}")
    result = dict(PRESETS[preset])
    for rule_id in enable or []:
        result[rule_id] = True
    for rule_id in disable or []:
        result[rule_id] = False
    return result
