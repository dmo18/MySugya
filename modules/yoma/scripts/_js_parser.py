#!/usr/bin/env python3
"""
_js_parser.py - Shared parser helpers for Yoma JS-like data files.

Parses the specific format emitted by build_learning_data.py's emit_line():

  { id: "...", kind: "...", he: "...",
      vilna_line: N, en: "...",
      sefaria_ref: "...", commentaries: { rashi: [], tosafot: [] } }

These helpers are string-accurate: they track bracket depth and skip quoted
strings, so literal { } [ ] characters inside string values never confuse
the parser. This replaces ad-hoc DOTALL one-level-nesting patterns.

Functions are scoped to this repo's emitted format. They do not attempt to
parse arbitrary JavaScript.
"""

from __future__ import annotations

import re
from typing import Iterator


# ---------------------------------------------------------------------------
# Low-level string-scanner helpers
# ---------------------------------------------------------------------------

def _advance_past_string(s: str, i: int) -> int:
    """Return the index of the char after the closing quote that starts at s[i].

    s[i] must be the opening double-quote. Handles backslash-escapes by
    skipping two characters for any backslash sequence (sufficient for the
    actual escape sequences used in this codebase: \\", \\\\, \\n).
    Raises ValueError if the string is unterminated before end-of-input.
    """
    if s[i] != '"':
        raise ValueError(f"Expected '\"' at index {i}, got {s[i]!r}")
    i += 1
    while i < len(s):
        ch = s[i]
        if ch == '\\':
            i += 2  # skip escaped character (works for \", \\, \n, \r, \t)
            continue
        if ch == '"':
            return i + 1  # past the closing quote
        i += 1
    raise ValueError(f"Unterminated string in content starting near index {i}")


def extract_balanced_block(
    content: str,
    start: int,
    open_char: str = '{',
    close_char: str = '}',
) -> str:
    """Return content from start up to and including the matching close_char.

    start must point at open_char. Skips over double-quoted strings so that
    bracket characters inside string values do not affect depth counting.
    Only the specified open_char/close_char pair is depth-tracked; other
    bracket pairs are treated as ordinary content.

    Raises ValueError if start does not point at open_char, or if no
    matching close_char is found.
    """
    if content[start] != open_char:
        raise ValueError(
            f"Expected {open_char!r} at index {start}, got {content[start]!r}"
        )
    depth = 0
    i = start
    while i < len(content):
        ch = content[i]
        if ch == '"':
            i = _advance_past_string(content, i)
            continue
        if ch == open_char:
            depth += 1
        elif ch == close_char:
            depth -= 1
            if depth == 0:
                return content[start : i + 1]
        i += 1
    raise ValueError(
        f"No matching {close_char!r} found starting at index {start}"
    )


# ---------------------------------------------------------------------------
# Field extractors
# ---------------------------------------------------------------------------

def extract_string_field(text: str, field_name: str) -> str:
    """Extract the value of a JS string field: field_name: "value".

    Returns the raw JS string content with only escaped-quote sequences
    (\") decoded back to literal quotes. The backslash-n sequence (\\n) is
    left as the two-character escape and is NOT converted to a real newline,
    matching the convention used in the existing validators.

    Raises ValueError if the field is not found or the string is unterminated.
    """
    pattern = re.compile(r'\b' + re.escape(field_name) + r'\s*:\s*"')
    m = pattern.search(text)
    if not m:
        raise ValueError(f"Field {field_name!r} not found in text")
    quote_start = m.end() - 1  # position of the opening "
    i = quote_start + 1
    while i < len(text):
        ch = text[i]
        if ch == '\\':
            i += 2
            continue
        if ch == '"':
            raw = text[quote_start + 1 : i]
            return raw.replace('\\"', '"')
        i += 1
    raise ValueError(f"Unterminated string for field {field_name!r}")


def extract_number_field(text: str, field_name: str) -> int | None:
    """Extract the integer value of a JS numeric field: field_name: N.

    Returns None if the field is not found.
    """
    m = re.search(r'\b' + re.escape(field_name) + r'\s*:\s*(\d+)', text)
    return int(m.group(1)) if m else None


def extract_balanced_array(content: str, field_name: str) -> str | None:
    """Find 'field_name: [' in content and return the balanced [...] block.

    Returns None if the field is not found. Raises ValueError if the array
    is unbalanced.
    """
    pattern = re.compile(r'\b' + re.escape(field_name) + r'\s*:\s*\[')
    m = pattern.search(content)
    if not m:
        return None
    bracket_start = m.end() - 1  # position of '['
    return extract_balanced_block(content, bracket_start, '[', ']')


# ---------------------------------------------------------------------------
# Array splitting
# ---------------------------------------------------------------------------

def split_top_level_array_items(array_text: str) -> list[str]:
    """Split a balanced [...] string into its top-level comma-separated items.

    array_text must include the outer brackets. Depth is tracked for both
    { } and [ ] pairs, and double-quoted strings are skipped, so commas
    inside nested structures or string values are not treated as separators.

    Returns a list of stripped item strings; empty items are excluded.
    """
    if not array_text or array_text[0] != '[' or array_text[-1] != ']':
        raise ValueError(
            "array_text must be a balanced [...] string starting with '[' and ending with ']'"
        )
    inner = array_text[1:-1]
    items: list[str] = []
    depth = 0
    current_start = 0
    i = 0
    while i < len(inner):
        ch = inner[i]
        if ch == '"':
            i = _advance_past_string(inner, i)
            continue
        if ch in ('{', '['):
            depth += 1
        elif ch in ('}', ']'):
            depth -= 1
        elif ch == ',' and depth == 0:
            item = inner[current_start:i].strip()
            if item:
                items.append(item)
            current_start = i + 1
        i += 1
    last = inner[current_start:].strip()
    if last:
        items.append(last)
    return items


# ---------------------------------------------------------------------------
# Line-object parser
# ---------------------------------------------------------------------------

def parse_line_fields(item_text: str) -> dict:
    """Parse a single line object text into a Python dict.

    Required fields: id, kind, he, en, sefaria_ref.
    Optional fields: vilna_line (int or None), en_lit (str or None).

    Raises ValueError if any required string field is missing or unterminated.
    Returns a dict with keys: id, kind, he, en, vilna_line, en_lit, sefaria_ref.
    """
    result: dict = {}
    for field in ('id', 'kind', 'he', 'en', 'sefaria_ref'):
        result[field] = extract_string_field(item_text, field)
    result['vilna_line'] = extract_number_field(item_text, 'vilna_line')
    try:
        result['en_lit'] = extract_string_field(item_text, 'en_lit')
    except ValueError:
        result['en_lit'] = None
    return result


# ---------------------------------------------------------------------------
# Multi-item and multi-daf parsers
# ---------------------------------------------------------------------------

def parse_line_items_from_lines_array(content: str) -> list[dict]:
    """Extract all line item dicts from every lines: [...] array in content.

    Finds all occurrences of 'lines: [' in content, extracts each balanced
    array, splits into items, and parses each item with parse_line_fields.
    Items that do not parse as line objects are silently skipped.

    Returns a flat list of dicts in document order.
    """
    results: list[dict] = []
    pattern = re.compile(r'\blines\s*:\s*\[')
    for m in pattern.finditer(content):
        bracket_start = m.end() - 1
        try:
            array_text = extract_balanced_block(content, bracket_start, '[', ']')
        except ValueError:
            continue
        for item in split_top_level_array_items(array_text):
            if not item:
                continue
            try:
                results.append(parse_line_fields(item))
            except ValueError:
                pass
    return results


def parse_daf_blocks(content: str) -> Iterator[tuple[str, str]]:
    """Yield (daf_id, block_text) for each daf entry in content.

    Matches entries of the form '"2a": {' and extracts the balanced {block}.
    Daf entries with unbalanced braces are skipped.
    """
    daf_re = re.compile(r'"(\d+[ab])"\s*:\s*\{')
    for m in daf_re.finditer(content):
        daf_id = m.group(1)
        brace_start = m.end() - 1  # position of '{'
        try:
            block = extract_balanced_block(content, brace_start, '{', '}')
            yield daf_id, block
        except ValueError:
            continue
