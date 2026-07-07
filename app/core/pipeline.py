"""Transformation pipeline (design section 4).

Wires the components together in the conservative, layered order the design
calls for:

    parse -> analyze -> protect -> propose -> plan -> validate -> apply -> export

Every paragraph is protected first, rules propose edits against the original
offsets, conflicts are resolved, the *result* is validated before anything is
committed, and only safe edits are applied. Unsafe rewrites are rejected, not
shipped.
"""

from __future__ import annotations

from typing import Dict, List, Optional

from . import protection
from .analyzer import analyze
from .applier import apply_resolved, plan_edits, simulate_text
from .exporter import export_docx
from .model import Document
from .parser import parse_docx
from .validator import validate_document, validate_paragraph
from app.rules.registry import build_registry
from app.configs.loader import load_rule_params
from app.reporting.report import ChangeEntry, FlagEntry, IssueEntry, ParagraphView, Report


_CTX = 22  # chars of context shown on each side of an edit in the report


def _context(text: str, edit) -> tuple[str, str]:
    """Render an edit as readable ``before``/``after`` strings with context.

    The changed region is wrapped in ``[[ ]]`` and surrounded by up to
    :data:`_CTX` characters of the original text, so a reader can see exactly
    what changed and where -- including capitalisation fixes.
    """
    lo = max(0, edit.start - _CTX)
    hi = min(len(text), edit.end + _CTX)
    lead = "…" if lo > 0 else ""
    trail = "…" if hi < len(text) else ""
    left, right = text[lo:edit.start], text[edit.end:hi]
    before = f"{lead}{left}[[{text[edit.start:edit.end]}]]{right}{trail}"
    after = f"{lead}{left}[[{edit.replacement}]]{right}{trail}"
    return before, after


def transform_document(
    in_path: str,
    out_path: str,
    enabled: Optional[Dict[str, bool]] = None,
    params: Optional[Dict[str, dict]] = None,
) -> Report:
    """Run the full pipeline and return a :class:`Report`."""
    document = parse_docx(in_path)
    original_texts = [p.plain_text() for p in document.paragraphs]
    stats = analyze(document)
    if params is None:
        params = load_rule_params()
    rules = build_registry(enabled, params)
    rule_names = {r.id: r.name for r in rules}

    report = Report(
        source=in_path,
        output=out_path,
        doc_type=document.doc_type,
        tone=document.tone,
        stats=stats,
    )

    for paragraph in document.paragraphs:
        protection.protect_paragraph(paragraph)

        proposed = []
        for rule in rules:
            proposed.extend(rule.propose(paragraph))
            for flag in rule.flags(paragraph):
                report.flags.append(FlagEntry(
                    paragraph_index=flag.paragraph_index,
                    rule_id=flag.rule_id,
                    message=flag.message,
                    excerpt=flag.excerpt,
                ))

        resolved = plan_edits(paragraph, proposed)
        if not resolved:
            continue

        pre_text = paragraph.plain_text()
        new_text = simulate_text(pre_text, resolved)
        issues = validate_paragraph(paragraph, new_text)
        errors = [i for i in issues if i.level == "error"]
        if errors:
            # Conservative: reject the whole paragraph's edits rather than risk
            # applying an unsafe subset.
            for i in errors:
                report.rejected.append(IssueEntry(i.level, i.paragraph_index, i.message))
            continue

        apply_resolved(paragraph, resolved)
        for edit in resolved:
            before, after = _context(pre_text, edit)
            report.changes.append(ChangeEntry(
                paragraph_index=paragraph.index,
                rule_id=edit.rule_id,
                rule_name=rule_names.get(edit.rule_id, edit.rule_id),
                before=before,
                after=after,
                reason=edit.reason,
                confidence=edit.confidence,
            ))

    export_docx(document, out_path)

    for paragraph, original in zip(document.paragraphs, original_texts):
        current = paragraph.plain_text()
        report.paragraphs.append(ParagraphView(
            index=paragraph.index,
            block_type=paragraph.block_type.value,
            original=original,
            transformed=current,
            changed=(original != current),
        ))

    for issue in validate_document(document, original_texts):
        report.issues.append(IssueEntry(issue.level, issue.paragraph_index, issue.message))

    return report
