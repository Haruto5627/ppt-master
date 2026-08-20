#!/usr/bin/env python3
"""
Word Rewrite - Office Image Extractor

Extract embedded images from Word (.docx/.docm) and PowerPoint
(.pptx/.pptm) packages into an ``images/`` folder next to each source file.
A lone Word file writes images directly into ``images/``. When that folder
has two or more Word files, each Word gets ``images/<stem>/``.
For Word, also write a captions JSON mapping document-order figures to
captions (题注 paragraph, then drawing descr/name). Does not modify the
Office file.

Usage:
    python skills/word-rewrite/extract_office_images.py <file_or_dir> [...]
    python skills/word-rewrite/extract_office_images.py report.docx
    python skills/word-rewrite/extract_office_images.py ./docs --dir-name images

Examples:
    python skills/word-rewrite/extract_office_images.py 报告.docx
    python skills/word-rewrite/extract_office_images.py ./materials -r

Dependencies:
    None (standard library only)
"""

from __future__ import annotations

import argparse
import io
import json
import re
import sys
import zipfile
from dataclasses import dataclass
from pathlib import Path
from xml.etree import ElementTree as ET

IMAGE_SUFFIXES = {
    ".png", ".jpg", ".jpeg", ".gif", ".webp", ".bmp",
    ".tif", ".tiff", ".svg", ".emf", ".wmf", ".ico",
}
MEDIA_PREFIXES = ("word/media/", "ppt/media/")
OFFICE_SUFFIXES = {".docx", ".docm", ".pptx", ".pptm"}
WORD_SUFFIXES = {".docx", ".docm"}
SKIP_SUFFIXES = {".bin", ".xml", ".rels"}

R_NS = "{http://schemas.openxmlformats.org/officeDocument/2006/relationships}"
W_NS = "{http://schemas.openxmlformats.org/wordprocessingml/2006/main}"

CAPTION_STYLES = {
    "caption", "caption1", "caption2",
    "figurecaption", "tablecaption",
    "题注", "题注1", "题注 1",
    "图表标题", "图题", "表题",
}
PLACEHOLDER_NAME_RE = re.compile(
    r"^(picture|graphic|image|图片|图形)\s*\d+$",
    re.IGNORECASE,
)
CAPTION_TEXT_RE = re.compile(
    r"^(图|表|图表|Figure|Fig\.?|Table)\s*"
    r"[\d一二三四五六七八九十百]+",
    re.IGNORECASE,
)
UNSAFE_DIR_RE = re.compile(r'[<>:"/\\|?*\x00-\x1f]')


@dataclass
class ExtractedImage:
    dest: Path
    zip_name: str


@dataclass
class DrawingRef:
    rid: str
    descr: str
    name: str


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


def local_tag(element: ET.Element) -> str:
    tag = element.tag
    if tag.startswith("{"):
        return tag.split("}", 1)[1]
    return tag


def _is_image_bytes(data: bytes) -> str | None:
    """Return a suffix (including the dot) if *data* looks like an image."""
    if data.startswith(b"\x89PNG\r\n\x1a\n"):
        return ".png"
    if data.startswith(b"\xff\xd8\xff"):
        return ".jpeg"
    if data.startswith((b"GIF87a", b"GIF89a")):
        return ".gif"
    if len(data) >= 12 and data.startswith(b"RIFF") and data[8:12] == b"WEBP":
        return ".webp"
    if data.startswith(b"BM"):
        return ".bmp"
    if data.startswith((b"II*\x00", b"MM\x00*")):
        return ".tiff"
    head = data.lstrip()[:256].lower()
    if head.startswith(b"<svg") or (head.startswith(b"<?xml") and b"<svg" in head):
        return ".svg"
    return None


def _zip_member_is_media(name: str) -> bool:
    normalized = name.replace("\\", "/").lstrip("/")
    return any(normalized.startswith(prefix) for prefix in MEDIA_PREFIXES)


def _original_filename(zip_name: str) -> str:
    return Path(zip_name.replace("\\", "/")).name


def _normalize_zip_name(name: str) -> str:
    return name.replace("\\", "/").lstrip("/")


def _safe_dir_name(stem: str) -> str:
    name = UNSAFE_DIR_RE.sub("_", stem).strip(" .")
    return name or "word"


def _word_files_in_dir(directory: Path) -> list[Path]:
    files: list[Path] = []
    for child in directory.iterdir():
        if child.is_file() and child.suffix.lower() in WORD_SUFFIXES:
            files.append(child.resolve())
    return sorted(files, key=lambda path: path.name.lower())


def assign_word_subdirs(word_files: list[Path]) -> dict[Path, str]:
    """Stable per-stem folder names when a directory has multiple Word files."""
    mapping: dict[Path, str] = {}
    used: set[str] = set()
    for source in word_files:
        base = _safe_dir_name(source.stem)
        name = base
        if name.lower() in used:
            name = _safe_dir_name(f"{source.stem}_{source.suffix.lstrip('.')}")
        n = 2
        candidate = name
        while candidate.lower() in used:
            candidate = f"{name}_{n}"
            n += 1
        used.add(candidate.lower())
        mapping[source.resolve()] = candidate
    return mapping


def image_dest_dir(source: Path, images_root: Path, word_subdirs: dict[Path, str]) -> Path:
    """Use images/<stem>/ when the Word's directory contains more than one Word file."""
    if source.suffix.lower() not in WORD_SUFFIXES:
        return images_root
    if len(word_subdirs) <= 1:
        return images_root
    name = word_subdirs.get(source.resolve())
    if not name:
        name = _safe_dir_name(source.stem)
    return images_root / name


def captions_json_path(source: Path, dest_dir: Path, images_root: Path) -> Path:
    if dest_dir.resolve() == images_root.resolve():
        return dest_dir / f"{source.stem}.captions.json"
    return dest_dir / "captions.json"


def _unique_filename(
    dest_dir: Path,
    filename: str,
    used: set[str],
    source_stem: str,
) -> str:
    """Pick a non-colliding name in *dest_dir*, prefixing with the source stem if needed."""
    candidates = [filename, f"{source_stem}_{filename}"]
    n = 2
    while True:
        for name in candidates:
            key = name.lower()
            if key not in used and not (dest_dir / name).exists():
                used.add(key)
                return name
        stem = Path(filename).stem
        suffix = Path(filename).suffix
        candidates = [f"{source_stem}_{stem}_{n}{suffix}"]
        n += 1


def collect_office_files(inputs: list[Path], *, recursive: bool) -> list[Path]:
    files: list[Path] = []
    seen: set[Path] = set()
    for raw in inputs:
        path = raw.expanduser().resolve()
        if path.is_file():
            if path not in seen:
                files.append(path)
                seen.add(path)
            continue
        if not path.is_dir():
            raise FileNotFoundError(str(raw))
        pattern = "**/*" if recursive else "*"
        for child in sorted(path.glob(pattern)):
            if child.is_file() and child.suffix.lower() in OFFICE_SUFFIXES:
                resolved = child.resolve()
                if resolved not in seen:
                    files.append(resolved)
                    seen.add(resolved)
    return files


def extract_office_images(source: Path, dest_dir: Path, used: set[str]) -> list[ExtractedImage]:
    """Write image parts from one Office package into *dest_dir*.

    Returns written files plus their ZIP member paths. Creates *dest_dir*
    only when at least one image is extracted.
    """
    suffix = source.suffix.lower()
    if suffix not in OFFICE_SUFFIXES:
        raise ValueError(
            f"Unsupported type {suffix or '(none)'}: {source.name}. "
            "Use .docx / .docm / .pptx / .pptm."
        )
    if not zipfile.is_zipfile(source):
        raise ValueError(
            f"{source.name} is not a ZIP Office package. "
            "Legacy .doc / .ppt are not supported; resave as .docx / .pptx first."
        )

    written: list[ExtractedImage] = []
    with zipfile.ZipFile(source) as zf:
        members = [
            info for info in zf.infolist()
            if not info.is_dir() and _zip_member_is_media(info.filename)
        ]
        for info in members:
            original = _original_filename(info.filename)
            if not original or original.startswith("."):
                continue
            ext = Path(original).suffix.lower()
            if ext in SKIP_SUFFIXES:
                continue
            data = zf.read(info)
            sniffed = _is_image_bytes(data)
            if ext not in IMAGE_SUFFIXES and sniffed is None:
                continue
            if ext not in IMAGE_SUFFIXES and sniffed:
                original = f"{Path(original).stem}{sniffed}"
            dest_dir.mkdir(parents=True, exist_ok=True)
            filename = _unique_filename(dest_dir, original, used, source.stem)
            dest = dest_dir / filename
            dest.write_bytes(data)
            written.append(
                ExtractedImage(dest=dest, zip_name=_normalize_zip_name(info.filename))
            )
    return written


def _resolve_rel_target(part_dir: str, target: str) -> str:
    raw = target.replace("\\", "/").strip()
    if not raw or raw.startswith("/"):
        return raw.lstrip("/")
    parts: list[str] = []
    for piece in f"{part_dir}/{raw}".replace("\\", "/").split("/"):
        if piece == "..":
            if parts:
                parts.pop()
        elif piece and piece != ".":
            parts.append(piece)
    return "/".join(parts)


def _load_part_rels(zf: zipfile.ZipFile, part_name: str) -> dict[str, str]:
    normalized = _normalize_zip_name(part_name)
    parent = str(Path(normalized).parent).replace("\\", "/")
    if parent == ".":
        parent = ""
    base = Path(normalized).name
    rels_name = f"{parent}/_rels/{base}.rels" if parent else f"_rels/{base}.rels"
    try:
        xml = zf.read(rels_name)
    except KeyError:
        return {}
    try:
        root = ET.fromstring(xml)
    except ET.ParseError:
        return {}
    mapping: dict[str, str] = {}
    for rel in root:
        if local_tag(rel) != "Relationship":
            continue
        rid = rel.get("Id") or ""
        target = rel.get("Target") or ""
        mode = (rel.get("TargetMode") or "").lower()
        if not rid or not target or mode == "external":
            continue
        mapping[rid] = _resolve_rel_target(parent, target)
    return mapping


def _w_val(element: ET.Element | None) -> str | None:
    if element is None:
        return None
    return element.get(f"{W_NS}val") or element.get("val")


def _paragraph_style(paragraph: ET.Element) -> str:
    for node in paragraph:
        if local_tag(node) != "pPr":
            continue
        for child in node:
            if local_tag(child) == "pStyle":
                return (_w_val(child) or "").strip()
    return ""


def _paragraph_text(paragraph: ET.Element) -> str:
    parts: list[str] = []
    for node in paragraph.iter():
        tag = local_tag(node)
        if tag == "t" and node.text:
            parts.append(node.text)
        elif tag == "tab":
            parts.append(" ")
        elif tag in {"br", "cr"}:
            parts.append(" ")
    return re.sub(r"\s+", " ", "".join(parts)).strip()


def _is_caption_style(style: str) -> bool:
    return style.strip().lower() in CAPTION_STYLES


def _looks_like_caption(text: str) -> bool:
    if not text or len(text) > 80:
        return False
    return bool(CAPTION_TEXT_RE.match(text))


def _is_placeholder_name(name: str) -> bool:
    return bool(name) and bool(PLACEHOLDER_NAME_RE.match(name.strip()))


def _attr(element: ET.Element, *names: str) -> str:
    for name in names:
        value = element.get(name)
        if value:
            return value.strip()
    return ""


def _drawings_in_paragraph(paragraph: ET.Element) -> list[DrawingRef]:
    found: list[DrawingRef] = []
    seen_rids: set[str] = set()

    def add(rid: str, descr: str, name: str) -> None:
        if not rid or rid in seen_rids:
            return
        seen_rids.add(rid)
        found.append(DrawingRef(rid=rid, descr=descr, name=name))

    for node in paragraph.iter():
        if local_tag(node) not in {"drawing", "pict", "object"}:
            continue
        descr = ""
        name = ""
        for child in node.iter():
            if local_tag(child) == "docPr":
                descr = _attr(child, "descr", "description")
                name = _attr(child, "name", "title")
                break
        for child in node.iter():
            tag = local_tag(child)
            if tag == "blip":
                add(_attr(child, f"{R_NS}embed", "embed"), descr, name)
            elif tag == "imagedata":
                add(
                    _attr(child, f"{R_NS}id", "id"),
                    descr,
                    name or _attr(child, "o:title", "title"),
                )
    return found


def _fallback_caption(drawing: DrawingRef) -> tuple[str, str]:
    if drawing.descr:
        return drawing.descr, "docPr"
    if drawing.name and not _is_placeholder_name(drawing.name):
        return drawing.name, "name"
    return "", "empty"


def collect_word_figure_captions(
    source: Path,
    extracted_by_zip: dict[str, ExtractedImage],
) -> list[dict[str, object]]:
    """Return document-order figure records for a Word package."""
    with zipfile.ZipFile(source) as zf:
        try:
            xml = zf.read("word/document.xml")
        except KeyError as exc:
            raise ValueError(f"{source.name} has no word/document.xml") from exc
        rels = _load_part_rels(zf, "word/document.xml")
        root = ET.fromstring(xml)

    figures: list[dict[str, object]] = []
    used_zip: set[str] = set()
    pending_caption: str | None = None
    path_root = source.parent.resolve()

    def figure_record(
        zip_name: str,
        item: ExtractedImage,
        caption: str,
        caption_source: str,
    ) -> dict[str, object]:
        rel = item.dest.resolve().relative_to(path_root).as_posix()
        return {
            "order": len(figures) + 1,
            "file": item.dest.name,
            "path": rel,
            "media": zip_name,
            "caption": caption,
            "caption_source": caption_source,
        }

    for node in root.iter():
        if local_tag(node) != "p":
            continue
        drawings = _drawings_in_paragraph(node)
        text = _paragraph_text(node)
        style = _paragraph_style(node)
        is_caption = _is_caption_style(style) or _looks_like_caption(text)
        if drawings:
            para_caption = text if is_caption and text else None
            first = True
            for drawing in drawings:
                nonlocal_pending = pending_caption if first else None
                zip_name = rels.get(drawing.rid, "")
                item = extracted_by_zip.get(zip_name)
                if item is None:
                    continue
                caption = ""
                caption_source = "empty"
                if nonlocal_pending:
                    caption = nonlocal_pending
                    caption_source = "paragraph"
                fallback, fallback_source = _fallback_caption(drawing)
                if para_caption:
                    caption = para_caption
                    caption_source = "paragraph"
                elif not caption:
                    caption = fallback
                    caption_source = fallback_source
                used_zip.add(zip_name)
                figures.append(figure_record(zip_name, item, caption, caption_source))
                first = False
            pending_caption = None
            continue
        if text and is_caption:
            if figures and figures[-1]["caption_source"] != "paragraph":
                figures[-1]["caption"] = text
                figures[-1]["caption_source"] = "paragraph"
            else:
                pending_caption = text

    for zip_name, item in extracted_by_zip.items():
        if zip_name in used_zip:
            continue
        figures.append(figure_record(zip_name, item, "", "unreferenced"))
    return figures


def write_word_captions_json(
    source: Path,
    dest_dir: Path,
    images_root: Path,
    extracted: list[ExtractedImage],
) -> Path | None:
    """Write captions JSON next to extracted Word images."""
    if source.suffix.lower() not in WORD_SUFFIXES or not extracted:
        return None
    extracted_by_zip = {item.zip_name: item for item in extracted}
    figures = collect_word_figure_captions(source, extracted_by_zip)
    payload = {
        "source": source.name,
        "directory": dest_dir.resolve().relative_to(source.parent.resolve()).as_posix(),
        "figures": figures,
    }
    dest = captions_json_path(source, dest_dir, images_root)
    dest.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    return dest


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Extract images from Word/PowerPoint files into a sibling images/ folder. "
            "Multiple Word files in one directory each get images/<stem>/. "
            "Word also writes a captions JSON for figure captions."
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "Images are written next to each source file and never written "
            "back into the Office file.\n"
            "One Word file: <dir>/images/. Two or more Word files in the same "
            "folder: <dir>/images/<stem>/.\n"
            "Invoke with python, not python3."
        ),
    )
    parser.add_argument(
        "inputs",
        nargs="+",
        help="Word/PowerPoint file(s), or a directory of them",
    )
    parser.add_argument(
        "--dir-name",
        default="images",
        help="Folder name next to each source file (default: images)",
    )
    parser.add_argument(
        "-r",
        "--recursive",
        action="store_true",
        help="When an input is a directory, scan it recursively",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    _configure_utf8_stdio()
    parser = build_parser()
    args = parser.parse_args(argv)
    dir_name = str(args.dir_name).strip() or "images"
    if "/" in dir_name or "\\" in dir_name:
        _status("--dir-name must be a single folder name, not a path.")
        return 2

    try:
        sources = collect_office_files(
            [Path(item) for item in args.inputs],
            recursive=args.recursive,
        )
    except FileNotFoundError as exc:
        _status(f"[ERROR] Not found: {exc}")
        return 1

    if not sources:
        _status("[ERROR] No .docx / .docm / .pptx / .pptm files in the given inputs.")
        return 1

    failed = 0
    used_by_dir: dict[Path, set[str]] = {}
    word_subdirs_by_parent: dict[Path, dict[Path, str]] = {}
    for source in sources:
        images_root = source.parent / dir_name
        parent_key = source.parent.resolve()
        if parent_key not in word_subdirs_by_parent:
            word_subdirs_by_parent[parent_key] = assign_word_subdirs(
                _word_files_in_dir(source.parent)
            )
        dest_dir = image_dest_dir(
            source, images_root, word_subdirs_by_parent[parent_key]
        )
        used = used_by_dir.setdefault(dest_dir.resolve(), set())
        if dest_dir.exists():
            for existing in dest_dir.iterdir():
                if existing.is_file():
                    used.add(existing.name.lower())
        try:
            written = extract_office_images(source, dest_dir, used)
        except (OSError, ValueError, zipfile.BadZipFile) as exc:
            _status(f"[ERROR] {source}: {exc}")
            failed += 1
            continue
        if not written:
            _status(f"[SKIP] {source.name}: no embedded images")
            continue
        captions_path = None
        try:
            captions_path = write_word_captions_json(
                source, dest_dir, images_root, written
            )
        except (OSError, ValueError, ET.ParseError, zipfile.BadZipFile) as exc:
            _status(f"[WARN] {source.name}: images extracted, captions skipped ({exc})")
        extra = f"; captions -> {captions_path.name}" if captions_path else ""
        _status(f"[OK] {source.name}: {len(written)} image(s) -> {dest_dir}{extra}")
        for item in written:
            print(item.dest)

    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
