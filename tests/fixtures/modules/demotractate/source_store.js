/* ============================================
   Demo Tractate (SYNTHETIC FIXTURE) -- verbatim source layer (GENERATED)
   Do NOT edit by hand. Regenerate with:
     python3 scripts/build_learning_data.py
   This is a Phase 3 tractate-agnostic-replication fixture. It contains no
   real Talmud content - every he:/en: value is an explicit placeholder.
   See tests/fixtures/modules/demotractate/MODULE.md.
   ============================================ */
const DATA_VERSION = "1.0";
const DATA_SCHEMA_VERSION = "1.0";
const TRACTATE_META = {
  "id": "demotractate",
  "title_en": "Demo Tractate (Synthetic Fixture)",
  "title_he": "דֻּגְמָה",
  "seder": "Fixture",
  "dafRange": {
    "first": "1a",
    "last": "2a"
  },
  "totalDaf": 3,
  "schemaVersion": "1.0",
  "fullyStructured": [
    "1a",
    "1b",
    "2a"
  ]
};
const PERAKIM = [
  {
    "n": 1,
    "name_he": "פֶּרֶק א (דֻּגְמָה)",
    "name_en": "Chapter One (Demo)",
    "topic": "[FIXTURE] The Widget Certification Board's opening rulings",
    "start": "1a",
    "end": "2a"
  }
];
const DAF_INDEX = [
  {
    "id": "1a",
    "perek": 1,
    "status": "rich",
    "topic": "[FIXTURE] Opening certification rule and the prototype question"
  },
  {
    "id": "1b",
    "perek": 1,
    "status": "rich",
    "topic": "[FIXTURE] Resolution of the prototype question and the durable takeaway"
  },
  {
    "id": "2a",
    "perek": 1,
    "status": "rich",
    "topic": "[FIXTURE] Independent recall-window scenario for defective widgets"
  }
];
const DAF_CONTENT = {
  "1a": {
    "canonicalRef": "[FIXTURE] Demo Tractate 1a",
    "daf": "1a",
    "lines": [
      {
        "id": "demo-001a-l01",
        "kind": "mishna",
        "he": "[FIXTURE-HE-PLACEHOLDER] Synthetic source line 1 for daf 1a. Not real Hebrew/Aramaic content - this field would normally hold verbatim source text.",
        "vilna_line": 1,
        "en": "[FIXTURE-EN-PLACEHOLDER] RULING: Every widget requires certification before sale. Synthetic content for the Phase 3 tractate-agnostic fixture.",
        "sefaria_ref": null,
        "commentaries": {
          "rashi": [],
          "tosafot": []
        }
      },
      {
        "id": "demo-001a-l02",
        "kind": "gemara",
        "he": "[FIXTURE-HE-PLACEHOLDER] Synthetic source line 2 for daf 1a.",
        "vilna_line": 2,
        "en": "[FIXTURE-EN-PLACEHOLDER] Bureaucrat Bet asks: does the certification duty apply to a prototype never intended for sale?",
        "sefaria_ref": null,
        "commentaries": {
          "rashi": [],
          "tosafot": []
        }
      },
      {
        "id": "demo-001a-l03",
        "kind": "gemara",
        "he": "[FIXTURE-HE-PLACEHOLDER] Synthetic source line 3 for daf 1a.",
        "vilna_line": 3,
        "en": "[FIXTURE-EN-PLACEHOLDER] Committee Gimel cites two supporting memos: the Prototype Exemption Memo and the General Certification Order.",
        "sefaria_ref": null,
        "commentaries": {
          "rashi": [],
          "tosafot": []
        }
      },
      {
        "id": "demo-001a-l04",
        "kind": "gemara",
        "he": "[FIXTURE-HE-PLACEHOLDER] Synthetic source line 4 for daf 1a.",
        "vilna_line": 4,
        "en": "[FIXTURE-EN-PLACEHOLDER] The Board distinguishes a prototype held for internal testing from a prototype held pending an eventual sale decision.",
        "sefaria_ref": null,
        "commentaries": {
          "rashi": [],
          "tosafot": []
        }
      },
      {
        "id": "demo-001a-l05",
        "kind": "gemara",
        "he": "[FIXTURE-HE-PLACEHOLDER] Synthetic source line 5 for daf 1a.",
        "vilna_line": 5,
        "en": "[FIXTURE-EN-PLACEHOLDER] The Board rejects the Prototype Exemption Memo for any prototype later routed to sale.",
        "sefaria_ref": null,
        "commentaries": {
          "rashi": [],
          "tosafot": []
        }
      }
    ]
  },
  "1b": {
    "canonicalRef": "[FIXTURE] Demo Tractate 1b",
    "daf": "1b",
    "lines": [
      {
        "id": "demo-001b-l01",
        "kind": "gemara",
        "he": "[FIXTURE-HE-PLACEHOLDER] Synthetic source line 1 for daf 1b.",
        "vilna_line": 1,
        "en": "[FIXTURE-EN-PLACEHOLDER] The Board resolves: a prototype intended for eventual sale still requires certification, even before that sale occurs.",
        "sefaria_ref": null,
        "commentaries": {
          "rashi": [],
          "tosafot": []
        }
      },
      {
        "id": "demo-001b-l02",
        "kind": "gemara",
        "he": "[FIXTURE-HE-PLACEHOLDER] Synthetic source line 2 for daf 1b.",
        "vilna_line": 2,
        "en": "[FIXTURE-EN-PLACEHOLDER] Takeaway: the certification duty attaches at the point of intended sale, not the point of actual sale - the same principle the opening ruling on 1a established for ordinary widgets.",
        "sefaria_ref": null,
        "commentaries": {
          "rashi": [],
          "tosafot": []
        }
      }
    ]
  },
  "2a": {
    "canonicalRef": "[FIXTURE] Demo Tractate 2a",
    "daf": "2a",
    "lines": [
      {
        "id": "demo-002a-l01",
        "kind": "mishna",
        "he": "[FIXTURE-HE-PLACEHOLDER] Synthetic source line 1 for daf 2a.",
        "vilna_line": 1,
        "en": "[FIXTURE-EN-PLACEHOLDER] RULING: A certified widget found defective after sale must be recalled within thirty days of discovery.",
        "sefaria_ref": null,
        "commentaries": {
          "rashi": [],
          "tosafot": []
        }
      },
      {
        "id": "demo-002a-l02",
        "kind": "gemara",
        "he": "[FIXTURE-HE-PLACEHOLDER] Synthetic source line 2 for daf 2a.",
        "vilna_line": 2,
        "en": "[FIXTURE-EN-PLACEHOLDER] The Board answers: the thirty-day clock starts on discovery by the Board, not on the defect's original occurrence.",
        "sefaria_ref": null,
        "commentaries": {
          "rashi": [],
          "tosafot": []
        }
      }
    ]
  }
};
