"""Internal document model.

The model wraps live ``python-docx`` objects. We never rebuild the document
from scratch; instead we hold references to the underlying paragraphs/runs and
edit their text in place. Everything we do not touch (styles, tables, images,
headers/footers, numbering) is preserved automatically by python-docx.

Rules express changes as :class:`Edit` operations on a paragraph's *plain
text* -- a ``(start, end, replacement)`` span. A separate applier maps those
spans back onto the runs, preserving surrounding formatting. Protected content
is represented as :class:`ProtectedSpan`; any edit overlapping a protected span
is rejected before it is ever applied.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import List, Optional


class BlockType(str, Enum):
    """Coarse classification of a paragraph's role in the document."""

    HEADING = "heading"
    BODY = "body"
    LIST = "list"
    QUOTE = "quote"
    CAPTION = "caption"
    TITLE = "title"


class ProtectedCategory(str, Enum):
    """Categories of content that must never be altered."""

    CITATION = "citation"
    QUOTATION = "quotation"
    NUMBER = "number"
    DATE = "date"
    EQUATION = "equation"
    CODE = "code"
    NAMED_ENTITY = "named_entity"
    REFERENCE = "reference"
    URL = "url"
    ACRONYM = "acronym"


@dataclass
class ProtectedSpan:
    """A locked region of a paragraph's plain text.

    Offsets are half-open ``[start, end)`` positions into the paragraph's
    plain text as returned by :meth:`Paragraph.plain_text`.
    """

    start: int
    end: int
    category: ProtectedCategory
    text: str
    reason: str = ""

    def overlaps(self, start: int, end: int) -> bool:
        """Return ``True`` if ``[start, end)`` intersects this span."""
        return start < self.end and end > self.start


@dataclass
class Edit:
    """A proposed span replacement on a paragraph's plain text.

    ``start``/``end`` are half-open offsets into the plain text at the moment
    the rule inspected it. Edits are collected, conflict-resolved, and then
    applied right-to-left so earlier offsets stay valid.
    """

    start: int
    end: int
    replacement: str
    rule_id: str
    category: str = ""
    reason: str = ""
    confidence: str = "high"  # high | medium | low
    original: str = ""

    def overlaps(self, other: "Edit") -> bool:
        return self.start < other.end and other.start < self.end


@dataclass
class Run:
    """A formatted text run inside a paragraph.

    ``obj`` is the live python-docx run object; ``text`` mirrors its current
    text and is written back to ``obj`` by the applier.
    """

    text: str
    obj: object = None  # docx.text.run.Run (live reference)
    bold: Optional[bool] = None
    italic: Optional[bool] = None


@dataclass
class Paragraph:
    """A single paragraph and everything a rule needs to reason about it."""

    index: int
    runs: List[Run] = field(default_factory=list)
    style_name: str = ""
    block_type: BlockType = BlockType.BODY
    obj: object = None  # docx.text.paragraph.Paragraph (live reference)
    list_level: Optional[int] = None

    original_text: str = ""
    protected_spans: List[ProtectedSpan] = field(default_factory=list)
    applied_edits: List[Edit] = field(default_factory=list)

    def plain_text(self) -> str:
        """Concatenate run text into the paragraph's plain text."""
        return "".join(r.text for r in self.runs)

    def is_editable(self) -> bool:
        """Headings, titles, and captions are structurally protected."""
        return self.block_type in (BlockType.BODY, BlockType.LIST, BlockType.QUOTE)

    def is_protected_range(self, start: int, end: int) -> bool:
        """Return ``True`` if any protected span overlaps ``[start, end)``."""
        return any(span.overlaps(start, end) for span in self.protected_spans)


@dataclass
class Document:
    """Top-level model: an ordered list of paragraphs plus source metadata."""

    paragraphs: List[Paragraph] = field(default_factory=list)
    source_path: str = ""
    docx: object = None  # docx.document.Document (live reference)

    # Populated by the structural analyzer.
    doc_type: str = "general"
    tone: str = "neutral"
    stats: dict = field(default_factory=dict)

    def body_paragraphs(self) -> List[Paragraph]:
        return [p for p in self.paragraphs if p.block_type == BlockType.BODY]
