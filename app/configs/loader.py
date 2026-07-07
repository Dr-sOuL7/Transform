"""Load presets and per-rule parameters from YAML, with built-in fallback.

The engine never *requires* the YAML files: if they are missing or malformed,
we fall back to the built-in presets in :mod:`app.configs.presets` and empty
rule params. This keeps the tool robust while letting power users tune it.
"""

from __future__ import annotations

from pathlib import Path
from typing import Dict, List

import yaml

from . import presets as _builtin

_HERE = Path(__file__).parent
PRESETS_YAML = _HERE / "presets.yaml"
RULES_YAML = _HERE / "rules.yaml"


def _read_yaml(path: Path) -> dict | None:
    try:
        with open(path, "r", encoding="utf-8") as fh:
            data = yaml.safe_load(fh)
        return data if isinstance(data, dict) else None
    except (OSError, yaml.YAMLError):
        return None


def load_presets(path: Path | None = None) -> Dict[str, Dict[str, bool]]:
    """Return the presets table from YAML, or the built-in one on any failure."""
    data = _read_yaml(path or PRESETS_YAML)
    if not data:
        return _builtin.PRESETS
    # Coerce values to bool and keep only dict-shaped presets.
    out: Dict[str, Dict[str, bool]] = {}
    for name, mapping in data.items():
        if isinstance(mapping, dict):
            out[name] = {str(k): bool(v) for k, v in mapping.items()}
    return out or _builtin.PRESETS


def load_rule_params(path: Path | None = None) -> Dict[str, dict]:
    """Return per-rule params from YAML, or ``{}`` on any failure."""
    data = _read_yaml(path or RULES_YAML)
    if not data:
        return {}
    return {str(k): v for k, v in data.items() if isinstance(v, dict)}


def resolve_enabled(
    preset: str,
    enable: List[str] | None = None,
    disable: List[str] | None = None,
) -> Dict[str, bool]:
    """Effective enabled map for ``preset`` (from YAML) with CLI overrides."""
    return _builtin.resolve_enabled(preset, enable, disable, presets=load_presets())
