from app.core import protection
from app.core.model import ProtectedCategory


def _cats(text):
    return {s.category for s in protection.detect_spans(text)}


def test_detects_numbers_and_dates():
    spans = protection.detect_spans("We had 1,234 items on 2020-01-31.")
    texts = [s.text for s in spans]
    assert any("1,234" in t for t in texts)
    assert ProtectedCategory.DATE in {s.category for s in spans}


def test_detects_url_and_citation():
    cats = _cats("See (Smith et al., 2019) and https://example.com now.")
    assert ProtectedCategory.URL in cats
    assert ProtectedCategory.CITATION in cats


def test_detects_bracket_citation_and_percentage():
    spans = protection.detect_spans("Accuracy hit 42% as shown [12].")
    texts = [s.text for s in spans]
    assert any("42%" in t for t in texts)
    assert any(t == "[12]" for t in texts)


def test_overlap_check():
    spans = protection.detect_spans("value 3.14 here")
    span = next(s for s in spans if "3.14" in s.text)
    assert span.overlaps(span.start, span.end)
    assert not span.overlaps(span.end, span.end + 1)
