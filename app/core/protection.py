"""Protected-content detection.

Pass 1 of the transformation strategy: scan a paragraph's plain text and mark
regions that must never be altered. Each detector is a ``(category, compiled
regex)`` pair; matches become :class:`ProtectedSpan`s. Any edit that overlaps a
protected span is rejected by :func:`app.core.applier.apply_edits`.

The detectors are intentionally conservative -- it is far safer to over-protect
(and under-edit) than to let a rule touch a citation or a number.
"""

from __future__ import annotations

import re
from typing import List

from .model import Paragraph, ProtectedCategory, ProtectedSpan

# --- Detector patterns -------------------------------------------------------
# Order matters only for the human-readable category assigned on overlap; the
# union of all spans is what actually protects content.

_URL = re.compile(r"""(?xi)
    \b(
        (?:https?://|www\.)         # scheme or www
        [^\s<>()"']+                # body
        | [\w.+-]+@[\w-]+\.[\w.-]+  # email
    )
""")

# Bracketed numeric citations: [1], [12], [3, 4], [5-7]
_CITATION_BRACKET = re.compile(r"\[\s*\d+(?:\s*[-,]\s*\d+)*\s*\]")

# Author-date citations: (Smith, 2020), (Smith et al., 2019), (Smith & Lee, 2021)
_CITATION_AUTHORDATE = re.compile(
    r"\([^()]*?\b(?:19|20)\d{2}[a-z]?\b[^()]*?\)"
)

# Dates: 2020-01-31, 31/01/2020, January 5, 2020, 5 Jan 2020
_DATE = re.compile(r"""(?xi)
    \b(
        \d{4}-\d{2}-\d{2}
      | \d{1,2}[/.]\d{1,2}[/.]\d{2,4}
      | (?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\.?\s+\d{1,2},?\s+\d{4}
      | \d{1,2}\s+(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\.?\s+\d{4}
    )\b
""")

# Numbers, percentages, currency, ranges: 3.14, 1,000, 42%, $5, 10-20, 5x
_NUMBER = re.compile(r"""(?x)
    [$£€]?\s?\d[\d,]*(?:\.\d+)?\s?%?
    (?:\s?[-–]\s?\d[\d,]*(?:\.\d+)?)?
""")

# Inline code / equations delimited by backticks or dollar signs.
_CODE = re.compile(r"`[^`]+`|\$[^$]+\$")

# Quotations: straight or curly double quotes, and curly single quotes.
_QUOTE = re.compile(r"\"[^\"]{1,400}\"|“[^”]{1,400}”|‘[^’]{1,400}’")

# Acronyms and defined terms: 2+ consecutive uppercase letters (NASA, HTTP, DNA)
_ACRONYM = re.compile(r"\b[A-Z]{2,}(?:s)?\b")

# Reference markers like "Fig. 3", "Table 2", "Eq. (4)", "Section 5"
_REFERENCE = re.compile(
    r"(?i)\b(?:fig(?:ure)?|table|eq(?:uation)?|section|chapter|appendix)\.?\s*\(?\d+[a-z]?\)?"
)

_DETECTORS: list[tuple[ProtectedCategory, re.Pattern]] = [
    (ProtectedCategory.URL, _URL),
    (ProtectedCategory.CODE, _CODE),
    (ProtectedCategory.QUOTATION, _QUOTE),
    (ProtectedCategory.CITATION, _CITATION_BRACKET),
    (ProtectedCategory.CITATION, _CITATION_AUTHORDATE),
    (ProtectedCategory.REFERENCE, _REFERENCE),
    (ProtectedCategory.DATE, _DATE),
    (ProtectedCategory.NUMBER, _NUMBER),
    (ProtectedCategory.ACRONYM, _ACRONYM),
]

_REASONS = {
    ProtectedCategory.URL: "URL/email must not be altered",
    ProtectedCategory.CODE: "code/equation must not be altered",
    ProtectedCategory.QUOTATION: "quoted material is verbatim",
    ProtectedCategory.CITATION: "citation must not be altered",
    ProtectedCategory.REFERENCE: "figure/table/section reference is fixed",
    ProtectedCategory.DATE: "date must not be altered",
    ProtectedCategory.NUMBER: "numeric value must not be altered",
    ProtectedCategory.ACRONYM: "acronym/defined term kept consistent",
}


def detect_spans(text: str) -> List[ProtectedSpan]:
    """Return protected spans found in ``text`` (may overlap)."""
    spans: List[ProtectedSpan] = []
    for category, pattern in _DETECTORS:
        for m in pattern.finditer(text):
            matched = m.group(0)
            if not matched.strip():
                continue
            # Trim leading/trailing whitespace captured by loose patterns.
            lead = len(matched) - len(matched.lstrip())
            trail = len(matched) - len(matched.rstrip())
            start = m.start() + lead
            end = m.end() - trail
            if end <= start:
                continue
            spans.append(
                ProtectedSpan(
                    start=start,
                    end=end,
                    category=category,
                    text=text[start:end],
                    reason=_REASONS.get(category, ""),
                )
            )
    return spans


def protect_paragraph(paragraph: Paragraph) -> List[ProtectedSpan]:
    """Detect and attach protected spans to ``paragraph``; also return them."""
    spans = detect_spans(paragraph.plain_text())
    paragraph.protected_spans = spans
    return spans
