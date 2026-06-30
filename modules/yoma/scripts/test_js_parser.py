#!/usr/bin/env python3
"""
test_js_parser.py - Unit tests for _js_parser.py.

No network access, no dependency on learning_data.js. Run directly:
  python3 scripts/test_js_parser.py
"""

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from _js_parser import (
    extract_balanced_array,
    extract_balanced_block,
    extract_number_field,
    extract_string_field,
    find_string_field_span,
    iter_line_object_spans,
    parse_daf_blocks,
    parse_line_fields,
    parse_line_items_from_lines_array,
    split_top_level_array_items,
)
from build_literal_layer import inject


SIMPLE_LINE = (
    '{ id: "yoma-002a-l01", kind: "mishna", he: "first line text",\n'
    '    vilna_line: 1, en: "first line english",\n'
    '    sefaria_ref: "Yoma.2a.1", commentaries: { rashi: [], tosafot: [] } }'
)

ESCAPED_QUOTES_LINE = (
    '{ id: "yoma-002a-l02", kind: "gemara", he: "text with \\"quoted\\" word",\n'
    '    vilna_line: 2, en: "English with \\"quotes\\"",\n'
    '    sefaria_ref: "Yoma.2a.2", commentaries: { rashi: [], tosafot: [] } }'
)

BRACKETS_IN_STRINGS_LINE = (
    '{ id: "yoma-002a-l03", kind: "gemara", he: "text {with} [brackets] inside",\n'
    '    vilna_line: 3, en: "also {has} [brackets] here",\n'
    '    sefaria_ref: "Yoma.2a.3", commentaries: { rashi: [], tosafot: [] } }'
)

WITH_EN_LIT_LINE = (
    '{ id: "yoma-002a-l04", kind: "gemara", he: "Hebrew text",\n'
    '    vilna_line: 4, en: "English text", en_lit: "Literal rendering",\n'
    '    sefaria_ref: "Yoma.2a.4", commentaries: { rashi: [], tosafot: [] } }'
)

NESTED_COMMENTARIES_LINE = (
    '{ id: "yoma-002a-l05", kind: "gemara", he: "Hebrew",\n'
    '    vilna_line: 5, en: "English",\n'
    '    sefaria_ref: "Yoma.2a.5", commentaries: '
    '{ rashi: [{ id: "rashi-1", he: "Rashi text", en: "Rashi en" }], tosafot: [] } }'
)

LINE_WITH_BRACKETS_AND_RASHI = (
    '{ id: "yoma-002a-l10", kind: "gemara", he: "Hebrew {with} [brackets]",\n'
    '    vilna_line: 10, en: "English {with} [brackets] too",\n'
    '    sefaria_ref: "Yoma.2a.10", commentaries: '
    '{ rashi: [{ id: "rashi-2", he: "Rashi {brace} [bracket]", en: "Rashi en {x}" }], tosafot: [] } }'
)


def make_lines_block(*line_items: str) -> str:
    """Wrap one or more line-object texts in a lines: [...] array string."""
    return 'lines: [\n  ' + ',\n  '.join(line_items) + '\n]'


LINES_ARRAY_BLOCK = (
    'lines: [\n'
    '  { id: "yoma-002a-l01", kind: "mishna", he: "First",\n'
    '      vilna_line: 1, en: "First en",\n'
    '      sefaria_ref: "Yoma.2a.1", commentaries: { rashi: [], tosafot: [] } },\n'
    '  { id: "yoma-002a-l02", kind: "gemara", he: "Second",\n'
    '      vilna_line: 2, en: "Second en",\n'
    '      sefaria_ref: "Yoma.2a.2", commentaries: { rashi: [], tosafot: [] } }\n'
    ']'
)

TWO_DAF_BLOCK = (
    'const DAF_CONTENT = {\n'
    '  // YOMA 2a\n'
    '  "2a": {\n'
    '    canonicalRef: "Yoma 2a",\n'
    '    sugyot: [\n'
    '      { id: "yoma-002a-s01", lines: [\n'
    f'        {SIMPLE_LINE}\n'
    '      ] }\n'
    '    ]\n'
    '  },\n'
    '  // YOMA 2b\n'
    '  "2b": {\n'
    '    canonicalRef: "Yoma 2b",\n'
    '    sugyot: [\n'
    '      { id: "yoma-002b-s01", lines: [\n'
    f'        {WITH_EN_LIT_LINE}\n'
    '      ] }\n'
    '    ]\n'
    '  }\n'
    '};'
)


class TestAdvanceAndBalance(unittest.TestCase):
    def test_extract_balanced_block_simple(self):
        text = '{ a: 1 } trailing'
        block = extract_balanced_block(text, 0)
        self.assertEqual(block, '{ a: 1 }')

    def test_extract_balanced_block_nested(self):
        text = '{ a: { b: 1 }, c: 2 } trailing'
        block = extract_balanced_block(text, 0)
        self.assertEqual(block, '{ a: { b: 1 }, c: 2 }')

    def test_extract_balanced_block_ignores_other_pair(self):
        text = '{ a: [1, 2], b: { c: 3 } } trailing'
        block = extract_balanced_block(text, 0)
        self.assertEqual(block, '{ a: [1, 2], b: { c: 3 } }')

    def test_extract_balanced_block_brace_in_string(self):
        text = '{ he: "text with } a brace" } trailing'
        block = extract_balanced_block(text, 0)
        self.assertEqual(block, '{ he: "text with } a brace" }')

    def test_extract_balanced_block_unterminated_raises(self):
        text = '{ a: 1 '
        with self.assertRaises(ValueError):
            extract_balanced_block(text, 0)

    def test_extract_balanced_block_wrong_start_raises(self):
        text = 'a: 1 }'
        with self.assertRaises(ValueError):
            extract_balanced_block(text, 0)

    def test_extract_balanced_array(self):
        content = 'foo: 1, lines: [1, 2, 3], bar: 2'
        arr = extract_balanced_array(content, 'lines')
        self.assertEqual(arr, '[1, 2, 3]')

    def test_extract_balanced_array_missing_returns_none(self):
        content = 'foo: 1, bar: 2'
        self.assertIsNone(extract_balanced_array(content, 'lines'))


class TestStringAndNumberFields(unittest.TestCase):
    def test_extract_string_field_basic(self):
        self.assertEqual(extract_string_field(SIMPLE_LINE, 'he'), 'first line text')
        self.assertEqual(extract_string_field(SIMPLE_LINE, 'en'), 'first line english')
        self.assertEqual(extract_string_field(SIMPLE_LINE, 'sefaria_ref'), 'Yoma.2a.1')

    def test_extract_string_field_escaped_quotes(self):
        he = extract_string_field(ESCAPED_QUOTES_LINE, 'he')
        self.assertEqual(he, 'text with "quoted" word')
        en = extract_string_field(ESCAPED_QUOTES_LINE, 'en')
        self.assertEqual(en, 'English with "quotes"')

    def test_extract_string_field_literal_brackets_in_string(self):
        he = extract_string_field(BRACKETS_IN_STRINGS_LINE, 'he')
        self.assertEqual(he, 'text {with} [brackets] inside')
        en = extract_string_field(BRACKETS_IN_STRINGS_LINE, 'en')
        self.assertEqual(en, 'also {has} [brackets] here')

    def test_extract_string_field_missing_raises(self):
        with self.assertRaises(ValueError):
            extract_string_field(SIMPLE_LINE, 'en_lit')

    def test_extract_number_field_basic(self):
        self.assertEqual(extract_number_field(SIMPLE_LINE, 'vilna_line'), 1)

    def test_extract_number_field_missing_returns_none(self):
        self.assertIsNone(extract_number_field(SIMPLE_LINE, 'no_such_field'))


class TestSplitTopLevelArrayItems(unittest.TestCase):
    def test_split_simple(self):
        items = split_top_level_array_items('[1, 2, 3]')
        self.assertEqual(items, ['1', '2', '3'])

    def test_split_nested_objects(self):
        array_text = '[' + SIMPLE_LINE + ', ' + WITH_EN_LIT_LINE + ']'
        items = split_top_level_array_items(array_text)
        self.assertEqual(len(items), 2)
        self.assertTrue(items[0].startswith('{ id: "yoma-002a-l01"'))
        self.assertTrue(items[1].startswith('{ id: "yoma-002a-l04"'))

    def test_split_ignores_commas_in_strings(self):
        array_text = '[{ he: "a, b, c" }, { he: "d, e" }]'
        items = split_top_level_array_items(array_text)
        self.assertEqual(len(items), 2)

    def test_split_ignores_commas_in_nested_arrays(self):
        array_text = '[{ arr: [1, 2, 3] }, { x: 1 }]'
        items = split_top_level_array_items(array_text)
        self.assertEqual(len(items), 2)

    def test_split_empty_array(self):
        self.assertEqual(split_top_level_array_items('[]'), [])

    def test_split_requires_brackets(self):
        with self.assertRaises(ValueError):
            split_top_level_array_items('1, 2, 3')


class TestParseLineFields(unittest.TestCase):
    def test_parse_basic_line(self):
        fields = parse_line_fields(SIMPLE_LINE)
        self.assertEqual(fields['id'], 'yoma-002a-l01')
        self.assertEqual(fields['kind'], 'mishna')
        self.assertEqual(fields['he'], 'first line text')
        self.assertEqual(fields['en'], 'first line english')
        self.assertEqual(fields['vilna_line'], 1)
        self.assertEqual(fields['sefaria_ref'], 'Yoma.2a.1')
        self.assertIsNone(fields['en_lit'])

    def test_parse_line_with_en_lit(self):
        fields = parse_line_fields(WITH_EN_LIT_LINE)
        self.assertEqual(fields['en_lit'], 'Literal rendering')

    def test_parse_line_with_nested_commentaries(self):
        fields = parse_line_fields(NESTED_COMMENTARIES_LINE)
        self.assertEqual(fields['id'], 'yoma-002a-l05')
        self.assertEqual(fields['he'], 'Hebrew')
        self.assertEqual(fields['sefaria_ref'], 'Yoma.2a.5')

    def test_parse_line_missing_required_field_raises(self):
        malformed = '{ id: "x", kind: "gemara", he: "text" }'  # missing en, sefaria_ref
        with self.assertRaises(ValueError):
            parse_line_fields(malformed)


class TestParseLineItemsFromLinesArray(unittest.TestCase):
    def test_parse_multiple_line_objects(self):
        items = parse_line_items_from_lines_array(LINES_ARRAY_BLOCK)
        self.assertEqual(len(items), 2)
        self.assertEqual(items[0]['id'], 'yoma-002a-l01')
        self.assertEqual(items[0]['he'], 'First')
        self.assertEqual(items[1]['id'], 'yoma-002a-l02')
        self.assertEqual(items[1]['he'], 'Second')

    def test_no_lines_array_returns_empty(self):
        self.assertEqual(parse_line_items_from_lines_array('no lines here'), [])

    def test_multiple_lines_arrays_in_one_content(self):
        content = LINES_ARRAY_BLOCK + '\n' + LINES_ARRAY_BLOCK
        items = parse_line_items_from_lines_array(content)
        self.assertEqual(len(items), 4)


class TestParseDafBlocks(unittest.TestCase):
    def test_parse_two_daf_blocks(self):
        blocks = list(parse_daf_blocks(TWO_DAF_BLOCK))
        self.assertEqual(len(blocks), 2)
        daf_ids = [b[0] for b in blocks]
        self.assertEqual(daf_ids, ['2a', '2b'])

    def test_daf_block_contains_its_lines(self):
        blocks = dict(parse_daf_blocks(TWO_DAF_BLOCK))
        items_2a = parse_line_items_from_lines_array(blocks['2a'])
        self.assertEqual(len(items_2a), 1)
        self.assertEqual(items_2a[0]['id'], 'yoma-002a-l01')

        items_2b = parse_line_items_from_lines_array(blocks['2b'])
        self.assertEqual(len(items_2b), 1)
        self.assertEqual(items_2b[0]['id'], 'yoma-002a-l04')

    def test_no_daf_blocks_yields_nothing(self):
        self.assertEqual(list(parse_daf_blocks('no daf here')), [])


class TestFindStringFieldSpan(unittest.TestCase):
    def test_finds_simple_field(self):
        span = find_string_field_span(SIMPLE_LINE, 'sefaria_ref')
        start, end = span
        self.assertEqual(SIMPLE_LINE[start:end], 'sefaria_ref: "Yoma.2a.1"')

    def test_finds_en_not_en_lit(self):
        span = find_string_field_span(WITH_EN_LIT_LINE, 'en')
        start, end = span
        self.assertEqual(WITH_EN_LIT_LINE[start:end], 'en: "English text"')

    def test_missing_field_returns_none(self):
        self.assertIsNone(find_string_field_span(SIMPLE_LINE, 'en_lit'))

    def test_span_respects_escaped_quotes(self):
        span = find_string_field_span(ESCAPED_QUOTES_LINE, 'he')
        start, end = span
        self.assertEqual(
            ESCAPED_QUOTES_LINE[start:end],
            'he: "text with \\"quoted\\" word"',
        )

    def test_span_respects_brackets_in_string(self):
        span = find_string_field_span(BRACKETS_IN_STRINGS_LINE, 'he')
        start, end = span
        self.assertEqual(
            BRACKETS_IN_STRINGS_LINE[start:end],
            'he: "text {with} [brackets] inside"',
        )


class TestIterLineObjectSpans(unittest.TestCase):
    def test_spans_cover_each_top_level_object(self):
        spans = list(iter_line_object_spans(LINES_ARRAY_BLOCK))
        self.assertEqual(len(spans), 2)
        first = LINES_ARRAY_BLOCK[spans[0][0] : spans[0][1]]
        second = LINES_ARRAY_BLOCK[spans[1][0] : spans[1][1]]
        self.assertTrue(first.startswith('{ id: "yoma-002a-l01"'))
        self.assertTrue(first.endswith('}'))
        self.assertTrue(second.startswith('{ id: "yoma-002a-l02"'))
        self.assertTrue(second.endswith('}'))

    def test_span_not_split_by_nested_commentaries(self):
        block = make_lines_block(NESTED_COMMENTARIES_LINE)
        spans = list(iter_line_object_spans(block))
        self.assertEqual(len(spans), 1)
        text = block[spans[0][0] : spans[0][1]]
        self.assertEqual(text, NESTED_COMMENTARIES_LINE)

    def test_span_not_affected_by_brackets_in_strings(self):
        block = make_lines_block(LINE_WITH_BRACKETS_AND_RASHI)
        spans = list(iter_line_object_spans(block))
        self.assertEqual(len(spans), 1)
        text = block[spans[0][0] : spans[0][1]]
        self.assertEqual(text, LINE_WITH_BRACKETS_AND_RASHI)

    def test_no_lines_array_yields_no_spans(self):
        self.assertEqual(list(iter_line_object_spans('no lines here')), [])


class TestLiteralCoverageCounting(unittest.TestCase):
    """Mirrors the coverage aggregation logic used by validate_literal.py."""

    def test_coverage_counts_with_nested_and_bracketed_lines(self):
        block = make_lines_block(
            WITH_EN_LIT_LINE,
            NESTED_COMMENTARIES_LINE,
            LINE_WITH_BRACKETS_AND_RASHI,
        )
        items = parse_line_items_from_lines_array(block)
        total = len(items)
        has_lit = sum(1 for item in items if item['en_lit'] is not None)
        empty_lit = sum(1 for item in items if item['en_lit'] == '')
        filled = has_lit - empty_lit

        self.assertEqual(total, 3)
        self.assertEqual(has_lit, 1)
        self.assertEqual(empty_lit, 0)
        self.assertEqual(filled, 1)


class TestLiteralLayerInjection(unittest.TestCase):
    """Tests for build_literal_layer.inject(), the writer side of the literal
    translation pipeline. Exercises the parser-backed line object boundary
    detection that replaced the one-level DOTALL pattern."""

    def test_insert_new_en_lit(self):
        source = make_lines_block(SIMPLE_LINE)
        cache = {'Yoma.2a.1': 'Literal text'}
        new_source, injected, skipped = inject(source, cache)
        self.assertEqual(injected, 1)
        self.assertEqual(skipped, 0)
        items = parse_line_items_from_lines_array(new_source)
        self.assertEqual(items[0]['en_lit'], 'Literal text')
        self.assertEqual(items[0]['he'], 'first line text')

    def test_update_existing_en_lit(self):
        source = make_lines_block(WITH_EN_LIT_LINE)
        cache = {'Yoma.2a.4': 'New literal text'}
        new_source, injected, skipped = inject(source, cache)
        self.assertEqual(injected, 1)
        self.assertEqual(skipped, 0)
        items = parse_line_items_from_lines_array(new_source)
        self.assertEqual(items[0]['en_lit'], 'New literal text')

    def test_skip_when_ref_not_in_cache(self):
        source = make_lines_block(SIMPLE_LINE)
        new_source, injected, skipped = inject(source, {})
        self.assertEqual(injected, 0)
        self.assertEqual(skipped, 1)
        self.assertEqual(new_source, source)

    def test_injection_with_nested_commentaries_and_brackets(self):
        source = make_lines_block(LINE_WITH_BRACKETS_AND_RASHI)
        cache = {'Yoma.2a.10': 'Literal {with} [brackets]'}
        new_source, injected, skipped = inject(source, cache)
        self.assertEqual(injected, 1)
        self.assertEqual(skipped, 0)
        items = parse_line_items_from_lines_array(new_source)
        self.assertEqual(len(items), 1)
        self.assertEqual(items[0]['he'], 'Hebrew {with} [brackets]')
        self.assertEqual(items[0]['en_lit'], 'Literal {with} [brackets]')

    def test_injection_escapes_quotes_in_literal_text(self):
        source = make_lines_block(SIMPLE_LINE)
        cache = {'Yoma.2a.1': 'Text with "quotes" inside'}
        new_source, injected, skipped = inject(source, cache)
        self.assertEqual(injected, 1)
        items = parse_line_items_from_lines_array(new_source)
        self.assertEqual(items[0]['en_lit'], 'Text with "quotes" inside')

    def test_multiple_lines_only_modifies_matched(self):
        source = make_lines_block(SIMPLE_LINE, WITH_EN_LIT_LINE)
        cache = {'Yoma.2a.1': 'New lit for first'}
        new_source, injected, skipped = inject(source, cache)
        self.assertEqual(injected, 1)
        self.assertEqual(skipped, 1)  # second line's ref is not in cache
        items = parse_line_items_from_lines_array(new_source)
        self.assertEqual(len(items), 2)
        self.assertEqual(items[0]['en_lit'], 'New lit for first')
        self.assertEqual(items[1]['en_lit'], 'Literal rendering')  # unchanged

    def test_line_without_sefaria_ref_is_left_untouched(self):
        malformed = '{ id: "x", kind: "gemara", he: "text", en: "text en" }'
        source = make_lines_block(malformed)
        new_source, injected, skipped = inject(source, {'Yoma.2a.1': 'x'})
        self.assertEqual(injected, 0)
        self.assertEqual(skipped, 0)
        self.assertEqual(new_source, source)


if __name__ == '__main__':
    unittest.main(verbosity=2)
