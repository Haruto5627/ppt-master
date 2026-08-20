#!/usr/bin/env python3
"""
Word Rewrite - Word to HTML (stdlib OOXML)

Convert .docx/.docm to an HTML fragment using only the standard library.
Keeps table colspan/rowspan from Word gridSpan/vMerge. Does not modify
the Word file and does not need mammoth, markitdown, or Microsoft Office.

Usage:
    python3 skills/word-rewrite/docx_to_html.py report.docx
    python3 skills/word-rewrite/docx_to_html.py report.docx --check

Examples:
    python3 skills/word-rewrite/docx_to_html.py 报告.docx
    python3 skills/word-rewrite/docx_to_html.py 报告.docx -o 报告.body.html

Dependencies:
    None (standard library only)
"""

from __future__ import annotations

import argparse
import html
import io
import sys
import zipfile
from dataclasses import dataclass
from pathlib import Path
from xml.etree import ElementTree as ET

W = "{http://schemas.openxmlformats.org/wordprocessingml/2006/main}"
DOCX_SUFFIXES = {".docx", ".docm"}
HEADING_STYLES = {
    "heading1": 1, "heading 1": 1, "标题1": 1, "标题 1": 1,
    "heading2": 2, "heading 2": 2, "标题2": 2, "标题 2": 2,
    "heading3": 3, "heading 3": 3, "标题3": 3, "标题 3": 3,
    "heading4": 4, "heading 4": 4, "标题4": 4, "标题 4": 4,
    "heading5": 5, "heading 5": 5, "标题5": 5, "标题 5": 5,
    "heading6": 6, "heading 6": 6, "标题6": 6, "标题 6": 6,
}


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


def qn(tag: str) -> str:
    return f"{W}{tag}"


def w_val(element: ET.Element | None) -> str | None:
    if element is None:
        return None
    return element.get(qn("val")) or element.get("val")


def local_tag(element: ET.Element) -> str:
    tag = element.tag
    if tag.startswith("{"):
        return tag.split("}", 1)[1]
    return tag


@dataclass
class TableCell:
    colspan: int
    vmerge: str | None
    html: str


def docx_table_needs_html(source: Path) -> bool:
    """True when OOXML tables use merges."""
    xml = _document_xml(source)
    if b"<w:tbl" not in xml:
        return False
    return b"gridSpan" in xml or b"vMerge" in xml


def _document_xml(source: Path) -> bytes:
    if not zipfile.is_zipfile(source):
        raise ValueError(
            f"{source.name} is not a ZIP Office package. "
            "Legacy .doc is not supported; resave as .docx."
        )
    with zipfile.ZipFile(source) as zf:
        try:
            return zf.read("word/document.xml")
        except KeyError as exc:
            raise ValueError(f"{source.name} has no word/document.xml") from exc


def paragraph_text_nodes(paragraph: ET.Element) -> str:
    parts: list[str] = []
    for node in paragraph.iter():
        tag = local_tag(node)
        if tag == "t" and node.text:
            parts.append(html.escape(node.text))
        elif tag == "tab":
            parts.append(" ")
        elif tag in {"br", "cr"}:
            parts.append("<br />")
    return "".join(parts)


def paragraph_heading_level(paragraph: ET.Element) -> int | None:
    p_pr = paragraph.find(qn("pPr"))
    if p_pr is None:
        return None
    style = w_val(p_pr.find(qn("pStyle")))
    if not style:
        return None
    return HEADING_STYLES.get(style.strip().lower())


def paragraph_to_html(paragraph: ET.Element) -> str:
    text = paragraph_text_nodes(paragraph)
    level = paragraph_heading_level(paragraph)
    if level:
        return f"<h{level}>{text or '&nbsp;'}</h{level}>"
    if not text.strip():
        return "<p></p>"
    return f"<p>{text}</p>"


def cell_inner_html(cell: ET.Element) -> str:
    chunks: list[str] = []
    for child in list(cell):
        tag = local_tag(child)
        if tag == "p":
            inner = paragraph_text_nodes(child)
            chunks.append(inner if inner else "")
        elif tag == "tbl":
            chunks.append(table_to_html(child))
    joined = "<br />".join(part for part in chunks if part != "")
    return joined if joined else "&nbsp;"


def parse_table_cells(table: ET.Element) -> list[list[TableCell]]:
    rows: list[list[TableCell]] = []
    for row in table.findall(qn("tr")):
        parsed: list[TableCell] = []
        for cell in row.findall(qn("tc")):
            props = cell.find(qn("tcPr"))
            colspan = 1
            vmerge = None
            if props is not None:
                span = props.find(qn("gridSpan"))
                if span is not None:
                    raw = w_val(span) or "1"
                    try:
                        colspan = max(1, int(raw))
                    except ValueError:
                        colspan = 1
                merge = props.find(qn("vMerge"))
                if merge is not None:
                    vmerge = (w_val(merge) or "continue").lower()
            parsed.append(
                TableCell(colspan=colspan, vmerge=vmerge, html=cell_inner_html(cell))
            )
        if parsed:
            rows.append(parsed)
    return rows


def table_column_count(rows: list[list[TableCell]]) -> int:
    if not rows:
        return 0
    return max(sum(cell.colspan for cell in row) for row in rows)


def place_table_grid(rows: list[list[TableCell]]) -> list[list[TableCell | None]]:
    ncols = table_column_count(rows)
    grid: list[list[TableCell | None]] = [
        [None] * ncols for _ in rows
    ]
    for row_index, row in enumerate(rows):
        column = 0
        for cell in row:
            while column < ncols and grid[row_index][column] is not None:
                column += 1
            occupant = cell
            if cell.vmerge == "continue" and row_index > 0 and column < ncols:
                occupant = grid[row_index - 1][column] or cell
            for offset in range(cell.colspan):
                target = column + offset
                if target < ncols:
                    grid[row_index][target] = occupant
            column += cell.colspan
    return grid


def table_to_html(table: ET.Element) -> str:
    rows = parse_table_cells(table)
    grid = place_table_grid(rows)
    if not grid:
        return "<table></table>"
    nrows = len(grid)
    ncols = len(grid[0])
    lines = ["<table>"]
    for row_index, row in enumerate(grid):
        lines.append("<tr>")
        column = 0
        while column < ncols:
            cell = row[column]
            if cell is None:
                column += 1
                continue
            if column > 0 and row[column - 1] is cell:
                column += 1
                continue
            if row_index > 0 and grid[row_index - 1][column] is cell:
                column += 1
                continue
            rowspan = 1
            while (
                row_index + rowspan < nrows
                and grid[row_index + rowspan][column] is cell
            ):
                rowspan += 1
            colspan = 1
            while column + colspan < ncols and row[column + colspan] is cell:
                colspan += 1
            attrs = []
            if rowspan > 1:
                attrs.append(f'rowspan="{rowspan}"')
            if colspan > 1:
                attrs.append(f'colspan="{colspan}"')
            attr = (" " + " ".join(attrs)) if attrs else ""
            lines.append(f"<td{attr}>{cell.html}</td>")
            column += colspan
        lines.append("</tr>")
    lines.append("</table>")
    return "\n".join(lines)


def iter_blocks(parent: ET.Element):
    for child in list(parent):
        tag = local_tag(child)
        if tag in {"p", "tbl"}:
            yield child
        elif tag == "sdt":
            content = child.find(qn("sdtContent"))
            if content is not None:
                yield from iter_blocks(content)
        elif tag == "body":
            yield from iter_blocks(child)


def convert_docx_to_html(source: Path) -> str:
    xml = _document_xml(source)
    root = ET.fromstring(xml)
    chunks: list[str] = []
    for block in iter_blocks(root):
        tag = local_tag(block)
        if tag == "tbl":
            chunks.append(table_to_html(block))
        elif tag == "p":
            chunks.append(paragraph_to_html(block))
    html_out = "\n".join(chunk for chunk in chunks if chunk)
    if not html_out.strip():
        raise ValueError(f"{source.name}: no paragraphs or tables found.")
    return html_out + "\n"


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Convert Word to HTML (stdlib). Keeps merged cells without mammoth."
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="Windows: if python3 is unavailable, rerun with python.",
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
            _status(f"[HTML] {source.name}: merged tables — do not use pipe tables")
            print("html")
            return 0
        _status(f"[MD] {source.name}: no merge markers — Markdown tables are enough")
        print("markdown")
        return 0

    try:
        html_out = convert_docx_to_html(source)
    except (OSError, ValueError, ET.ParseError) as exc:
        _status(f"[ERROR] {exc}")
        return 1

    dest = Path(args.output).expanduser() if args.output else source.with_suffix(".body.html")
    dest.write_text(html_out, encoding="utf-8")
    kind = "complex-tables" if needs_html else "simple"
    _status(f"[OK] {source.name} ({kind}) -> {dest}")
    print(dest)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
