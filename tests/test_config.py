import textwrap

from app.configs import loader
from app.configs.presets import PRESETS
from app.rules.registry import build_registry


def test_load_presets_from_yaml_default():
    presets = loader.load_presets()
    assert "balanced" in presets
    assert presets["balanced"]["filler_removal"] is True


def test_load_presets_fallback_on_missing(tmp_path):
    missing = tmp_path / "nope.yaml"
    assert loader.load_presets(missing) == PRESETS


def test_load_presets_custom_file(tmp_path):
    f = tmp_path / "p.yaml"
    f.write_text(textwrap.dedent("""
        tiny:
          whitespace_normalization: true
          filler_removal: false
    """))
    presets = loader.load_presets(f)
    assert "tiny" in presets
    assert presets["tiny"]["filler_removal"] is False


def test_rule_params_flow_into_registry(tmp_path):
    f = tmp_path / "r.yaml"
    f.write_text(textwrap.dedent("""
        long_sentence:
          word_limit: 5
    """))
    params = loader.load_rule_params(f)
    rules = build_registry(enabled=None, params=params)
    long_rule = next(r for r in rules if r.id == "long_sentence")
    assert long_rule.word_limit == 5


def test_resolve_enabled_overrides():
    enabled = loader.resolve_enabled("balanced", enable=["negation_scaffold"],
                                     disable=["filler_removal"])
    assert enabled["negation_scaffold"] is True
    assert enabled["filler_removal"] is False
