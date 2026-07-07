from app.core.model import Paragraph, Run
from app.core import protection
from app.core.applier import apply_resolved, plan_edits, simulate_text
from app.rules.filler_rules import FillerRemovalRule
from app.rules.transition_rules import TransitionSimplificationRule
from app.rules.cleanup_rules import WhitespaceRule, NegationScaffoldRule


def _para(text):
    p = Paragraph(index=0, runs=[Run(text=text)])
    p.original_text = text
    protection.protect_paragraph(p)
    return p


def _run_rule(rule, text):
    p = _para(text)
    resolved = plan_edits(p, rule.propose(p))
    return simulate_text(p.plain_text(), resolved)


def test_filler_removed_and_capitalised():
    out = _run_rule(FillerRemovalRule(), "It is important to note that the system works.")
    assert out == "The system works."


def test_in_order_to_simplified():
    out = _run_rule(FillerRemovalRule(), "We refactored in order to reduce coupling.")
    assert out == "We refactored to reduce coupling."


def test_transition_only_trims_repeats():
    text = "Moreover, it is fast. Moreover, it is safe. Moreover, it is small."
    out = _run_rule(TransitionSimplificationRule(), text)
    # First "Moreover," kept, later ones trimmed.
    assert out.count("Moreover,") == 1
    assert out.startswith("Moreover, it is fast.")


def test_whitespace_collapsed():
    out = _run_rule(WhitespaceRule(), "This  has   extra    spaces .")
    assert "  " not in out
    assert out == "This has extra spaces."


def test_negation_scaffold():
    out = _run_rule(NegationScaffoldRule(), "It is not just fast, but reliable in practice.")
    assert out == "It is reliable in practice."


def test_edit_does_not_touch_protected_number():
    # A pathological rule trying to delete a number must be rejected by protection.
    p = _para("The value is 42 exactly.")
    from app.core.model import Edit
    bad = Edit(start=13, end=15, replacement="", rule_id="x")  # "42"
    resolved = plan_edits(p, [bad])
    assert resolved == []  # overlaps a protected number


def test_apply_preserves_surrounding_run_formatting():
    # Two runs; edit only touches the first. Second run text is untouched.
    p = Paragraph(index=0, runs=[Run(text="It is important to note that x "), Run(text="stays")])
    p.original_text = p.plain_text()
    protection.protect_paragraph(p)
    rule = FillerRemovalRule()
    resolved = plan_edits(p, rule.propose(p))
    apply_resolved(p, resolved)
    assert p.runs[1].text == "stays"
    assert p.plain_text().endswith("stays")
