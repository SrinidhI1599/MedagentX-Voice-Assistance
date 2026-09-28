from __future__ import annotations

import re
import unicodedata

_PAGE_NUMBER_RE = re.compile(r"^\s*(page\s+)?\d+\s*(of\s*\d+)?\s*$", re.IGNORECASE)
_MULTI_WHITESPACE_RE = re.compile(r"[ \t\u00a0]+")
_MULTI_NEWLINE_RE = re.compile(r"\n{3,}")
_HYPHEN_LINEBREAK_RE = re.compile(r"(\w)-\n(\w)")
_CONTROL_CHARS_RE = re.compile(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]")
_BULLET_RE = re.compile(r"^[\u2022\u25cf\u2023\u2043▪●◦]\s*", re.MULTILINE)

_BOILERPLATE_LINES = (
    "all rights reserved",
    "confidential",
    "for internal use only",
    "printed from",
    "downloaded from",
)

def _strip_control_chors(text: str) -> str:
    return _CONTROL_CHARS_RE.sub("", text)

def _normalize_unicode(text: str) -> str:
    return unicodedata.normalize("NFKC", text)

def _dehyphenate(text: str) -> str:
    return _HYPHEN_LINEBREAK_RE.sub(r"\1\2", text)

def _remove_boilerplate_lines(text: str) -> str:
    kept_lines = []
    for line in text.split("\n"):
        stripped = line.strip()
        if not stripped:
            kept_lines.append(line)
            continue
        if _PAGE_NUMBER_RE.match(stripped):
            continue
        lowered = stripped.lower()
        if any(marker in lowered for marker in _BOILERPLATE_LINES):
            continue
        kept_lines.append(line)
    return "\n".join(kept_lines)

def _normalize_whitespace(text: str) -> str:
    text = _MULTI_WHITESPACE_RE.sub(" ", text)
    text = _MULTI_NEWLINE_RE.sub("\n\n", text)
    text = "\n".join(line.rstrip() for line in text.split("\n"))
    return text.strip()

def _normalize_bullets(text: str) -> str:
    return _BULLET_RE.sub("- ", text)

def clean_text(raw_text: str) -> str:
    if not raw_text:
        return ""

    text = _strip_control_chors(raw_text)
    text = _normalize_unicode(text)
    text = _dehyphenate(text)
    text = _remove_boilerplate_lines(text)
    text = _normalize_bullets(text)
    text = _normalize_whitespace(text)
    return text

def clean_file(path: str, encoding: str = "utf-8") -> str:
    with open(path, "r", encoding=encoding, errors="replace") as f:
        raw = f.read()
    return clean_text(raw)