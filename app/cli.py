"""Command-line entry point.

Usage:
    python -m app.cli input.docx [-o output.docx] [--preset balanced]
                                 [--enable rule_id] [--disable rule_id]
                                 [--report report.json] [--quiet]

Presets are named enabled/disabled maps living in ``app/configs/presets.py``.
Individual ``--enable/--disable`` flags override the preset.
"""

from __future__ import annotations

import argparse
import os
import sys

from app.core.pipeline import transform_document
from app.configs.presets import PRESETS, resolve_enabled


def build_arg_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="text-transform",
        description="Offline rule-based .docx text refinement.",
    )
    p.add_argument("input", help="input .docx file")
    p.add_argument("-o", "--output", help="output .docx (default: <input>.refined.docx)")
    p.add_argument(
        "--preset", default="balanced", choices=sorted(PRESETS),
        help="rule preset (default: balanced)",
    )
    p.add_argument("--enable", action="append", default=[], metavar="RULE_ID",
                   help="force-enable a rule (repeatable)")
    p.add_argument("--disable", action="append", default=[], metavar="RULE_ID",
                   help="force-disable a rule (repeatable)")
    p.add_argument("--report", help="write JSON report to this path")
    p.add_argument("--report-txt", help="write text report to this path")
    p.add_argument("--quiet", action="store_true", help="suppress the text report on stdout")
    return p


def main(argv=None) -> int:
    args = build_arg_parser().parse_args(argv)

    if not os.path.isfile(args.input):
        print(f"error: input file not found: {args.input}", file=sys.stderr)
        return 2
    if not args.input.lower().endswith(".docx"):
        print("error: only .docx input is supported in v1", file=sys.stderr)
        return 2

    output = args.output or _default_output(args.input)
    enabled = resolve_enabled(args.preset, args.enable, args.disable)

    report = transform_document(args.input, output, enabled=enabled)

    if args.report:
        with open(args.report, "w", encoding="utf-8") as fh:
            fh.write(report.to_json())
    if args.report_txt:
        with open(args.report_txt, "w", encoding="utf-8") as fh:
            fh.write(report.to_text())

    if not args.quiet:
        print(report.to_text())
    print(f"\nWrote: {output}")
    return 0


def _default_output(in_path: str) -> str:
    base, _ = os.path.splitext(in_path)
    return f"{base}.refined.docx"


if __name__ == "__main__":
    raise SystemExit(main())
