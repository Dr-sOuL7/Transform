"""Change report (design sections 5G, 13).

Turns the pipeline's results into a structured, explainable audit trail that
can be rendered as text or serialised to JSON.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field, asdict
from typing import Dict, List


@dataclass
class ChangeEntry:
    paragraph_index: int
    rule_id: str
    rule_name: str
    before: str
    after: str
    reason: str
    confidence: str


@dataclass
class FlagEntry:
    paragraph_index: int
    rule_id: str
    message: str
    excerpt: str


@dataclass
class IssueEntry:
    level: str
    paragraph_index: int
    message: str


@dataclass
class ParagraphView:
    """Original vs transformed text for one paragraph (for the diff view)."""

    index: int
    block_type: str
    original: str
    transformed: str
    changed: bool
    #: Distinct locked substrings (numbers, citations, URLs, …) to highlight.
    protected: List[str] = field(default_factory=list)


@dataclass
class Report:
    source: str = ""
    output: str = ""
    doc_type: str = "general"
    tone: str = "neutral"
    stats: Dict = field(default_factory=dict)
    changes: List[ChangeEntry] = field(default_factory=list)
    flags: List[FlagEntry] = field(default_factory=list)
    issues: List[IssueEntry] = field(default_factory=list)
    rejected: List[IssueEntry] = field(default_factory=list)
    paragraphs: List[ParagraphView] = field(default_factory=list)

    # -- serialisation ---------------------------------------------------
    def to_dict(self) -> Dict:
        return {
            "source": self.source,
            "output": self.output,
            "doc_type": self.doc_type,
            "tone": self.tone,
            "stats": self.stats,
            "summary": {
                "edits_applied": len(self.changes),
                "flags": len(self.flags),
                "validation_issues": len(self.issues),
                "rejected_paragraphs": len(self.rejected),
            },
            "changes": [asdict(c) for c in self.changes],
            "flags": [asdict(f) for f in self.flags],
            "issues": [asdict(i) for i in self.issues],
            "rejected": [asdict(r) for r in self.rejected],
            "paragraphs": [asdict(p) for p in self.paragraphs],
        }

    def to_json(self, indent: int = 2) -> str:
        return json.dumps(self.to_dict(), indent=indent, ensure_ascii=False)

    def to_text(self) -> str:
        lines: List[str] = []
        lines.append("=" * 66)
        lines.append("  TEXT TRANSFORMATION REPORT")
        lines.append("=" * 66)
        lines.append(f"Source : {self.source}")
        lines.append(f"Output : {self.output}")
        lines.append(f"Type   : {self.doc_type}    Tone: {self.tone}")
        lines.append("")
        lines.append("Document statistics")
        lines.append("-" * 66)
        for key, value in self.stats.items():
            lines.append(f"  {key:<18}: {value}")
        lines.append("")
        lines.append(
            f"Applied {len(self.changes)} edit(s); "
            f"{len(self.flags)} flag(s); "
            f"{len(self.rejected)} paragraph(s) left unedited for safety."
        )
        lines.append("")

        if self.changes:
            lines.append("Edits applied")
            lines.append("-" * 66)
            for c in self.changes:
                lines.append(f"  [para {c.paragraph_index}] {c.rule_name} ({c.confidence})")
                lines.append(f"      before: {c.before!r}")
                lines.append(f"      after : {c.after!r}")
                lines.append(f"      reason: {c.reason}")
            lines.append("")

        if self.flags:
            lines.append("Suggestions (not auto-applied)")
            lines.append("-" * 66)
            for f in self.flags:
                lines.append(f"  [para {f.paragraph_index}] {f.message}")
                if f.excerpt:
                    lines.append(f"      …{f.excerpt}…")
            lines.append("")

        if self.issues:
            lines.append("Validation")
            lines.append("-" * 66)
            for i in self.issues:
                where = "document" if i.paragraph_index < 0 else f"para {i.paragraph_index}"
                lines.append(f"  [{i.level.upper()}] ({where}) {i.message}")
            lines.append("")

        lines.append("=" * 66)
        return "\n".join(lines)
