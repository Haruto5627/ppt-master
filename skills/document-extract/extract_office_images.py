#!/usr/bin/env python3
"""
Document Extract - Office Image Extractor

Extract embedded images from Word (.docx/.docm) and PowerPoint
(.pptx/.pptm) packages into an ``images/`` folder next to each source file.
Does not modify the Office file.

Usage:
    python3 skills/document-extract/extract_office_images.py <file_or_dir> [...]
    python3 skills/document-extract/extract_office_images.py report.docx deck.pptx
    python3 skills/document-extract/extract_office_images.py ./docs --dir-name images

Examples:
    python3 skills/document-extract/extract_office_images.py 报告.docx
    python3 skills/document-extract/extract_office_images.py ./materials -r

Dependencies:
    None (standard library only)
"""

from __future__ import annotations

import argparse
import io
import sys
import zipfile
from pathlib import Path

IMAGE_SUFFIXES = {
    ".png", ".jpg", ".jpeg", ".gif", ".webp", ".bmp",
    ".tif", ".tiff", ".svg", ".emf", ".wmf", ".ico",
}
MEDIA_PREFIXES = ("word/media/", "ppt/media/")
OFFICE_SUFFIXES = {".docx", ".docm", ".pptx", ".pptm"}
SKIP_SUFFIXES = {".bin", ".xml", ".rels"}


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


def extract_office_images(source: Path, dest_dir: Path, used: set[str]) -> list[Path]:
    """Write image parts from one Office package into *dest_dir*.

    Returns the list of written files. Creates *dest_dir* only when at least
    one image is extracted.
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

    written: list[Path] = []
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
            written.append(dest)
    return written


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Extract images from Word/PowerPoint files into a sibling images/ folder."
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "Images are written to <source-dir>/<dir-name>/ and never written "
            "back into the Office file.\n"
            "Windows: if python3 is unavailable, rerun with python."
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
    for source in sources:
        dest_dir = source.parent / dir_name
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
        _status(f"[OK] {source.name}: {len(written)} image(s) -> {dest_dir}")
        for path in written:
            print(path)

    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
