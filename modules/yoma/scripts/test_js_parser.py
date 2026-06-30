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
    parse_daf_blocks,
    parse_line_fields,
    parse_line_items_from_lines_array,
    split_top_level_array_items,
)


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


if __name__ == '__main__':
    unittest.main(verbosity=2)
