from app.core.model import Paragraph, Run
from app.core import protection
from app.core.applier import plan_edits, simulate_text
from app.rules.redundancy_rules import (
    StockPhraseRule,
    RedundantModifierRule,
    RepeatedWordRule,
)


def _run(rule, text):
    p = Paragraph(index=0, runs=[Run(text=text)])
    p.original_text = text
    protection.protect_paragraph(p)
    return simulate_text(p.plain_text(), plan_edits(p, rule.propose(p)))


def test_stock_phrase_simplifies():
    assert _run(StockPhraseRule(), "We stopped due to the fact that it rained.") \
        == "We stopped because it rained."


def test_stock_phrase_preserves_capitalisation():
    assert _run(StockPhraseRule(), "Due to the fact that it rained, we stopped.") \
        == "Because it rained, we stopped."


def test_stock_phrase_extra_from_config():
    rule = StockPhraseRule(params={"extra": {"a whole lot of": "many"}})
    assert _run(rule, "We saw a whole lot of birds.") == "We saw many birds."


def test_redundant_modifier():
    assert _run(RedundantModifierRule(), "The end result was a free gift.") \
        == "The result was a gift."


def test_repeated_word_removed():
    assert _run(RepeatedWordRule(), "This is the the final version.") \
        == "This is the final version."


def test_repeated_word_leaves_grammatical_doubles():
    # "had had" is legitimate past perfect; must not be touched.
    text = "She had had enough by then."
    assert _run(RepeatedWordRule(), text) == text


def test_stock_phrase_does_not_touch_protected_number():
    # "the majority of 100" -> the number stays; phrase still simplifies.
    out = _run(StockPhraseRule(), "The majority of 100 users agreed.")
    assert "100" in out
    assert out.startswith("Most")
