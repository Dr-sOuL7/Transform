# Offline Rule-Based Text Transformation

A local, offline system that reads a `.docx`, applies conservative, explainable
rule-based style/clarity edits, preserves protected content and formatting, and
writes a new `.docx` plus a change report.

It is a document editing tool, not a detector-evasion tool. The design bias is
**under-edit over over-edit**: it only makes changes it can make deterministically
and safely, and it *flags* (rather than blindly rewrites) anything that would
risk changing meaning.

## Status

**Phase 1 (MVP) — engine + CLI.** Fully offline, no cloud, no model downloads.

- ✅ DOCX parser + writer (edits run text **in place**, so styles, tables,
  images, headers/footers, and numbering are preserved automatically)
- ✅ Internal document model with plain-text ↔ run mapping
- ✅ Protected-content detection (numbers, dates, citations, URLs, quotes, code,
  acronyms, figure/table references)
- ✅ Deterministic rule engine with conflict resolution
- ✅ Pre-apply + whole-document validation (unsafe edits are rejected, not shipped)
- ✅ Explainable change report (text + JSON)
- ✅ CLI with presets

Not yet built (later phases): GUI, YAML rule files, spaCy-based linguistics,
batch processing, packaging into an executable.

## Install

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Use

```bash
python -m app.cli input.docx -o output.docx --preset balanced --report report.json
```

Options:

| Flag | Meaning |
|------|---------|
| `--preset` | `conservative`, `balanced` (default), `strong`, `academic` |
| `--enable RULE_ID` / `--disable RULE_ID` | override individual rules (repeatable) |
| `--report PATH` | write JSON report |
| `--report-txt PATH` | write text report |
| `--quiet` | don't print the report to stdout |

Rule ids: `whitespace_normalization`, `filler_removal`,
`transition_simplification`, `negation_scaffold`, `em_dash_normalization`.

## Pipeline

```
parse → analyze → protect → propose → plan → validate → apply → export → report
```

Rules express changes as `(start, end, replacement)` span edits on a paragraph's
plain text. Any edit overlapping a protected span is rejected before it is
applied; the resulting text is validated (protected content, numbers, non-empty,
length) before anything is committed.

## Project layout

```
app/
  cli.py                 # command-line entry point
  core/
    model.py             # Document / Paragraph / Run / Edit / ProtectedSpan
    parser.py            # .docx -> model
    protection.py        # protected-content detection
    applier.py           # plan / simulate / apply span edits onto runs
    analyzer.py          # doc type / tone / statistics
    validator.py         # pre-apply + whole-document checks
    exporter.py          # model -> .docx
    pipeline.py          # orchestration
  rules/
    base_rule.py         # Rule / Flag interface
    registry.py          # ordered active rule set
    filler_rules.py      # throat-clearing removal
    transition_rules.py  # repeated-transition trimming
    cleanup_rules.py     # whitespace / negation scaffold / em dash
    structure_rules.py   # flag-only observations (openers, long sentences, triads)
  reporting/report.py    # change report (text + JSON)
  configs/presets.py     # rule presets
tests/                   # pytest suite
```

## Tests

```bash
python -m pytest -q
```

## Roadmap

- **Phase 2:** YAML/JSON rule profiles, richer reports, stronger protection.
- **Phase 3:** offline NLP (sentence segmentation, POS, NER) for smarter, still
  meaning-preserving variation.
- **Phase 4:** GUI (a local web UI is recommended so it is verifiable
  cross-platform) and packaging into a distributable executable.
