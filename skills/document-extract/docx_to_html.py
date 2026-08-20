#!/usr/bin/env python3
"""
Document Extract - Word to HTML (table-faithful)

Convert .docx to an HTML fragment with mammoth when Markdown pipe tables
would drop merged / nested cells. Does not modify the Word file.

Usage:
    python3 skills/document-extract/docx_to_html.py report.docx
    python3 skills/document-extract/docx_to_html.py report.docx --check

Examples:
    python3 skills/document-extract/docx_to_html.py 报告.docx
    python3 skills/document-extract/docx_to_html.py 报告.docx -o 报告.body.html

Dependencies:
    mammoth (comes with markitdown[docx])
"""

from __future__ import annotations

import argparse
import io
import sys
import zipfile
from pathlib import Path

DOCX_SUFFIXES = {".docx", ".docm"}


def _configure_utf8_stdio() -> None:
    for name in ("stdout", "stderr"):
        stream = getattr(sys, name)
        reconfigure = getattr(stream, "reconfigure", None)
        if callable(reconfigure):
            try:
                reconfigure(encoding="utf-8", errors="replace")
                continue
            except (OSError, ValueError, AttributeError):
                pass
        buffer = getattr(stream, "buffer", None)
        if buffer is None:
            continue
        try:
            setattr(
                sys,
                name,
                io.TextIOWrapper(buffer, encoding="utf-8", errors="replace"),
            )
        except (OSError, ValueError):
            pass


def _status(message: str) -> None:
    print(message, file=sys.stderr)


def docx_table_needs_html(source: Path) -> bool:
    """True when OOXML tables use merges or nested tables."""
    if not zipfile.is_zipfile(source):
        raise ValueError(f"{source.name} is not a ZIP Office package.")
    with zipfile.ZipFile(source) as zf:
        try:
            xml = zf.read("word/document.xml")
        except KeyError as exc:
            raise ValueError(f"{source.name} has no word/document.xml") from exc
    if b"<w:tbl" not in xml:
        return False
    return b"gridSpan" in xml or b"vMerge" in xml


def convert_docx_to_html(source: Path) -> str:
    try:
        import mammoth
    except ImportError as exc:
        raise RuntimeError(
            "mammoth is not installed. Run: python -m pip install 'markitdown[docx]'"
        ) from exc
    with source.open("rb") as handle:
        result = mammoth.convert_to_html(handle)
    for message in result.messages:
        _status(f"[mammoth] {message}")
    html = (result.value or "").strip()
    if not html:
        raise ValueError(f"{source.name}: mammoth produced empty HTML.")
    return html + "\n"


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Convert Word to HTML when Markdown tables cannot keep merges."
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("input", help="Path to a .docx / .docm file")
    parser.add_argument(
        "-o",
        "--output",
        help="HTML fragment path (default: <stem>.body.html next to the Word file)",
    )
    parser.add_argument(
        "--check",
        action="store_true",
        help="Only report whether tables need HTML; write nothing",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    _configure_utf8_stdio()
    parser = build_parser()
    args = parser.parse_args(argv)
    source = Path(args.input).expanduser().resolve()
    if not source.is_file():
        _status(f"[ERROR] Not found: {source}")
        return 1
    if source.suffix.lower() not in DOCX_SUFFIXES:
        _status("[ERROR] Only .docx / .docm are supported.")
        return 2

    try:
        needs_html = docx_table_needs_html(source)
    except (OSError, ValueError) as exc:
        _status(f"[ERROR] {exc}")
        return 1

    if args.check:
        if needs_html:
            _status(f"[HTML] {source.name}: merged or nested tables — do not use pipe tables")
            print("html")
            return 0
        _status(f"[MD] {source.name}: no merge markers — Markdown tables are enough")
        print("markdown")
        return 0

    try:
        html = convert_docx_to_html(source)
    except (OSError, ValueError, RuntimeError) as exc:
        _status(f"[ERROR] {exc}")
        return 1

    dest = Path(args.output).expanduser() if args.output else source.with_suffix(".body.html")
    dest.write_text(html, encoding="utf-8")
    kind = "complex-tables" if needs_html else "simple"
    _status(f"[OK] {source.name} ({kind}) -> {dest}")
    print(dest)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
