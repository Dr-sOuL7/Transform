# Offline Rule-Based Text Transformation

A local, offline system that reads a `.docx`, applies conservative, explainable
rule-based style/clarity edits, preserves protected content and formatting, and
writes a new `.docx` plus a change report.

It is a document editing tool, not a detector-evasion tool. The design bias is
**under-edit over over-edit**: it only makes changes it can make deterministically
and safely, and it *flags* (rather than blindly rewrites) anything that would
risk changing meaning.

## Status

**Phase 1 + 2 — engine, CLI, local web UI, YAML config.** Fully offline, no cloud, no model downloads.

- ✅ DOCX parser + writer (edits run text **in place**, so styles, tables,
  images, headers/footers, and numbering are preserved automatically)
- ✅ Internal document model with plain-text ↔ run mapping
- ✅ Protected-content detection (numbers, dates, citations, URLs, quotes, code,
  acronyms, figure/table references)
- ✅ Deterministic rule engine with conflict resolution
- ✅ Pre-apply + whole-document validation (unsafe edits are rejected, not shipped)
- ✅ Explainable change report (text + JSON)
- ✅ CLI with presets
- ✅ Local web UI (FastAPI + browser): drag-drop upload, preset + per-rule
  toggles, side-by-side word-level diff with **protected-content highlighting**,
  live stats, edit log, warnings, `.docx` export, **JSON report download**,
  **saved rule profiles** (browser-local), and start-over reset
- ✅ **YAML rule profiles** (`configs/presets.yaml`, `configs/rules.yaml`) with
  built-in fallback — tune presets and rule parameters without editing code
- ✅ **Richer rule set**: wordy-phrase simplification, redundant-modifier
  (tautology) removal, repeated-word cleanup, plus mini-summary / restatement
  flags

Not yet built (later phases): spaCy-based linguistics, batch processing,
packaging into an executable.

## Install

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Use — web UI

```bash
python -m app.web        # then open http://127.0.0.1:8000
```

Runs entirely on localhost; nothing leaves your machine. Drop a `.docx`, pick a
preset (and toggle individual rules), press **Transform**, review the
side-by-side diff and edit log, and export the refined `.docx`.

## Use — CLI

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

Rule ids: `whitespace_normalization`, `repeated_word`, `filler_removal`,
`transition_simplification`, `stock_phrase_simplification`, `redundant_modifier`,
`negation_scaffold`, `em_dash_normalization`.

## Configuration (YAML)

Presets and per-rule parameters live in editable YAML files; if they're missing
or invalid the engine falls back to built-in defaults.

- `app/configs/presets.yaml` — named presets mapping each rule id to on/off.
- `app/configs/rules.yaml` — per-rule tunables, e.g. extra filler phrases,
  extra wordy-phrase replacements, `long_sentence.word_limit`,
  `transition_simplification.repeat_threshold`.

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
    redundancy_rules.py  # wordy phrases / redundant modifiers / repeated words
    structure_rules.py   # flag-only observations (openers, long sentences, triads,
                         #   mini-summaries, restatements)
  reporting/report.py    # change report (text + JSON)
  configs/
    presets.py           # built-in preset defaults (fallback)
    loader.py            # YAML loader (presets + rule params)
    presets.yaml         # editable presets
    rules.yaml           # editable per-rule params
  web/
    server.py            # FastAPI app (offline, localhost)
    static/              # index.html, style.css, app.js (side-by-side diff UI)
tests/                   # pytest suite
```

## Tests

```bash
python -m pytest -q
```

## Roadmap

- **Phase 3:** offline NLP (sentence segmentation, POS, NER) for smarter, still
  meaning-preserving variation.
- **Phase 4:** packaging into a distributable executable (e.g. PyInstaller),
  batch processing, profile manager, history.
