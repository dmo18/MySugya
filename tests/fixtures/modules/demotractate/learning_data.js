/* ============================================
   Demo Tractate (SYNTHETIC FIXTURE) -- canonical learning data (GENERATED)
   Do NOT edit by hand. Regenerate with:
     python3 scripts/build_learning_data.py
   Source line layer: assets/fixture_source/<daf>.source.json
   Learning layer:    assets/learning/demotractate/<daf>.learning.json

   THIS IS A SYNTHETIC PHASE 3 REPLICATION-PROOF FIXTURE, NOT REAL CONTENT.
   Every he:/en: field below is an explicit bracketed placeholder. Never
   wired into manifest.js, never built by scripts/build.mjs's default
   invocation, never deployed to GitHub Pages. See MODULE.md.
   ============================================ */
const DATA_VERSION = "1.0";
const DATA_SCHEMA_VERSION = "1.0";
const LEARNING_DATA_VERSION = DATA_VERSION;
const TRACTATE_META = {
  "id": "demotractate",
  "title": "Demo Tractate (Synthetic Fixture)",
  "title_he": "דֻּגְמָה",
  "seder": "Fixture",
  "schemaVersion": "1.0",
  "dataVersion": "1.0",
  "sourceEdition": "Phase 3 synthetic fixture - no real source edition",
  "dafRange": {
    "first": "1a",
    "last": "2a"
  },
  "totalDaf": 3,
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
    "summary": "[FIXTURE] Synthetic daf 1a of the demo tractate: the fictional Widget Certification Board rules that every widget requires certification before sale, then debates whether an unsold prototype is exempt.",
    "sugyot": [
      {
        "id": "demo-001a-s01",
        "canonicalRef": "[FIXTURE] Demo Tractate 1a",
        "daf": "1a",
        "sugyaNumber": 1,
        "lineRange": {
          "startLineId": "demo-001a-l01",
          "endLineId": "demo-001a-l03",
          "startVilnaLine": 1,
          "endVilnaLine": 3
        },
        "display": {
          "title": "[FIXTURE] Opening ruling and the prototype question",
          "oneLine": "[FIXTURE] Every widget needs certification before sale; Bureaucrat Bet asks about unsold prototypes.",
          "shortSummary": "[FIXTURE] The Board's opening ruling requires certification before sale. Bureaucrat Bet raises the prototype question, and Committee Gimel brings two supporting memos.",
          "whats": "[FIXTURE] Synthetic explanatory text for the fixture's first sugya, standing in for the kind of editorial analysis a real sugya would carry.",
          "hint": "[FIXTURE] What distinguishes a prototype from an ordinary widget?"
        },
        "learning": {
          "learnerQuestion": "[FIXTURE] Does an unsold prototype need certification?",
          "coreTension": "[FIXTURE] The certification rule is framed around sale, but a prototype may never be sold.",
          "coreMove": "[FIXTURE] Committee Gimel supplies two memos anticipating exactly this question.",
          "resolution": "",
          "takeaway": {
            "type": "logical_principle",
            "text": "[FIXTURE] A rule framed around one triggering event needs an explicit answer for cases where that event may never occur."
          },
          "ahaMoment": "[FIXTURE] The rule's own drafters already anticipated the prototype gap.",
          "learningBlocker": "[FIXTURE] Assuming 'before sale' rules only ever apply to items that are eventually sold.",
          "memoryAnchor": "[FIXTURE] Prototype now, sale maybe - certify anyway if intent is there."
        },
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
          }
        ],
        "argumentFlow": [
          {
            "id": "step-01",
            "type": "case",
            "label": "[FIXTURE] Opening rule",
            "speaker": "Board",
            "text": "[FIXTURE] Every widget requires certification before sale.",
            "sourceRefs": [
              {
                "sourceType": "mishnah",
                "lineId": "demo-001a-l01",
                "vilnaLine": 1
              }
            ]
          },
          {
            "id": "step-02",
            "type": "question",
            "label": "[FIXTURE] The prototype question",
            "speaker": "Bureaucrat Bet",
            "text": "[FIXTURE] Does the certification duty apply to a prototype never intended for sale? This step intentionally omits sourceRefs - a purely rhetorical question with no single-line anchor, legal per the optional sourceRefs field."
          },
          {
            "id": "step-03",
            "type": "proof",
            "label": "[FIXTURE] Two supporting memos",
            "speaker": "Committee Gimel",
            "text": "[FIXTURE] Two memos are cited in support: the Prototype Exemption Memo and the General Certification Order - a genuine multi-ref step citing two distinct lines.",
            "sourceRefs": [
              {
                "sourceType": "gemara",
                "lineId": "demo-001a-l02",
                "vilnaLine": 2,
                "note": "Prototype Exemption Memo"
              },
              {
                "sourceType": "gemara",
                "lineId": "demo-001a-l03",
                "vilnaLine": 3,
                "note": "General Certification Order"
              }
            ]
          }
        ],
        "topicTags": [
          "fixture-demo",
          "widget-certification",
          "prototype-exemption"
        ],
        "misconceptions": [
          {
            "misconception": "[FIXTURE] A prototype is automatically exempt from certification.",
            "correction": "[FIXTURE] Exemption depends on whether the prototype is ever routed toward sale, resolved on daf 1b.",
            "correctedByStepId": "step-03"
          }
        ],
        "visualizableElements": [
          {
            "item": "[FIXTURE] The Widget Certification Board in session",
            "role": "anchor",
            "priority": 1
          }
        ],
        "quizSeeds": [
          {
            "question": "[FIXTURE] What must happen before a widget is sold?",
            "answer": "[FIXTURE] It must be certified by the Board.",
            "sourceRefs": [
              {
                "sourceType": "mishnah",
                "lineId": "demo-001a-l01",
                "vilnaLine": 1
              }
            ]
          }
        ],
        "difficulty": "intro",
        "review": {
          "learning": "ai_generated",
          "argumentFlow": "ai_generated",
          "sourceRefs": "ai_generated"
        }
      },
      {
        "id": "demo-001a-s02",
        "canonicalRef": "[FIXTURE] Demo Tractate 1a",
        "daf": "1a",
        "sugyaNumber": 2,
        "lineRange": {
          "startLineId": "demo-001a-l04",
          "endLineId": "demo-001a-l05",
          "startVilnaLine": 4,
          "endVilnaLine": 5
        },
        "display": {
          "title": "[FIXTURE] Distinguishing internal-test from sale-bound prototypes",
          "oneLine": "[FIXTURE] The Board distinguishes prototypes by their eventual destination.",
          "shortSummary": "[FIXTURE] The Board draws a distinction between a prototype held purely for internal testing and one held pending a possible sale, then rejects the exemption for the latter.",
          "whats": "[FIXTURE] Synthetic explanatory text for the fixture's second sugya on daf 1a.",
          "hint": "[FIXTURE] Does intent at the time of manufacture matter, or only eventual outcome?"
        },
        "learning": {
          "learnerQuestion": "[FIXTURE] Which prototypes actually qualify for the exemption?",
          "coreTension": "[FIXTURE] Not every prototype is alike - some are purely internal, others are sale candidates.",
          "coreMove": "[FIXTURE] The Board draws a bright-line distinction based on eventual routing, not manufacturing intent.",
          "resolution": "[FIXTURE] Only a prototype that never leaves internal testing is exempt.",
          "takeaway": {
            "type": "legal_principle",
            "text": "[FIXTURE] An exemption keyed to intent must be narrowed to the cases where that intent is actually realized."
          },
          "ahaMoment": "[FIXTURE] The exemption was never about the word 'prototype' - it was about whether the item ever reaches a customer.",
          "learningBlocker": "[FIXTURE] Treating 'prototype' as a fixed status rather than a routing that can change.",
          "memoryAnchor": "[FIXTURE] Internal-only prototype: exempt. Sale-bound prototype: certify."
        },
        "lines": [
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
        ],
        "argumentFlow": [
          {
            "id": "step-01",
            "type": "distinction",
            "label": "[FIXTURE] Internal-test vs sale-bound",
            "speaker": "Board",
            "text": "[FIXTURE] A prototype held for internal testing is distinguished from one held pending a sale decision.",
            "sourceRefs": [
              {
                "sourceType": "gemara",
                "lineId": "demo-001a-l04",
                "vilnaLine": 4
              }
            ]
          },
          {
            "id": "step-02",
            "type": "rejection",
            "label": "[FIXTURE] Exemption rejected for sale-bound prototypes",
            "speaker": "Board",
            "text": "[FIXTURE] The Prototype Exemption Memo is rejected for any prototype later routed to sale.",
            "sourceRefs": [
              {
                "sourceType": "gemara",
                "lineId": "demo-001a-l05",
                "vilnaLine": 5
              }
            ]
          }
        ],
        "topicTags": [
          "fixture-demo",
          "widget-certification",
          "prototype-exemption"
        ],
        "difficulty": "intro",
        "review": {
          "learning": "ai_generated",
          "argumentFlow": "ai_generated",
          "sourceRefs": "ai_generated"
        }
      }
    ],
    "glossary": [
      {
        "he": "[FIXTURE-HE]",
        "translit": "widget",
        "en": "[FIXTURE] a generic certifiable item invented for this fixture"
      }
    ],
    "rashiLines": [
      {
        "id": "rashi-demo-1a-001",
        "sourceType": "rashi",
        "daf": "1a",
        "vilnaLine": 1,
        "he": "[FIXTURE-RASHI-HE-PLACEHOLDER] Synthetic Rashi-layer commentary on daf 1a line 1.",
        "en": "[FIXTURE-RASHI-EN-PLACEHOLDER] Explains that 'every widget' includes items not yet manufactured, i.e. covers future production too.",
        "enSource": "ai_helper_translation",
        "source": "fixture-local",
        "confidence": "helper",
        "linkedGemaraLineIds": [
          "demo-001a-l01"
        ]
      },
      {
        "id": "rashi-demo-1a-003",
        "sourceType": "rashi",
        "daf": "1a",
        "vilnaLine": 3,
        "he": "[FIXTURE-RASHI-HE-PLACEHOLDER] Synthetic Rashi-layer commentary on daf 1a line 3.",
        "en": "[FIXTURE-RASHI-EN-PLACEHOLDER] Clarifies that the General Certification Order predates the Prototype Exemption Memo by charter number, establishing its precedence.",
        "enSource": "ai_helper_translation",
        "source": "fixture-local",
        "confidence": "helper",
        "linkedGemaraLineIds": [
          "demo-001a-l03"
        ]
      }
    ],
    "review": {
      "status": "verified"
    }
  },
  "1b": {
    "canonicalRef": "[FIXTURE] Demo Tractate 1b",
    "daf": "1b",
    "summary": "[FIXTURE] Synthetic daf 1b of the demo tractate: the Board resolves the prototype question from 1a and states the durable takeaway, tying it back to the opening ruling.",
    "sugyot": [
      {
        "id": "demo-001b-s01",
        "canonicalRef": "[FIXTURE] Demo Tractate 1b",
        "daf": "1b",
        "sugyaNumber": 1,
        "lineRange": {
          "startLineId": "demo-001b-l01",
          "endLineId": "demo-001b-l02",
          "startVilnaLine": 1,
          "endVilnaLine": 2
        },
        "display": {
          "title": "[FIXTURE] Resolution and takeaway",
          "oneLine": "[FIXTURE] A sale-bound prototype still requires certification; the duty attaches at intended sale.",
          "shortSummary": "[FIXTURE] The Board resolves that certification duty attaches at the point of intended sale, not actual sale, closing the loop back to the daf 1a opening ruling.",
          "whats": "[FIXTURE] Synthetic explanatory text for the fixture's sugya on daf 1b.",
          "hint": "[FIXTURE] When exactly does the certification duty attach?"
        },
        "learning": {
          "learnerQuestion": "[FIXTURE] Is the certification duty tied to actual sale or intended sale?",
          "coreTension": "[FIXTURE] A literal reading of 'before sale' could delay the duty until a sale is actually imminent.",
          "coreMove": "[FIXTURE] The Board locates the duty at the earlier point: intended sale.",
          "resolution": "[FIXTURE] The certification duty attaches once sale is intended, not once sale is imminent or complete.",
          "takeaway": {
            "type": "legal_principle",
            "text": "[FIXTURE] A duty framed around an eventual event attaches at the point of intent toward that event, not the event itself."
          },
          "ahaMoment": "[FIXTURE] 'Before sale' was never about timing relative to a transaction - it was about timing relative to intent.",
          "learningBlocker": "[FIXTURE] Assuming 'before sale' means immediately preceding a completed transaction.",
          "memoryAnchor": "[FIXTURE] Intend to sell it? Certify it now, not at the register."
        },
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
        ],
        "argumentFlow": [
          {
            "id": "step-01",
            "type": "resolution",
            "label": "[FIXTURE] The duty attaches at intended sale",
            "speaker": "Board",
            "text": "[FIXTURE] A prototype intended for eventual sale still requires certification, even before that sale occurs.",
            "sourceRefs": [
              {
                "sourceType": "gemara",
                "lineId": "demo-001b-l01",
                "vilnaLine": 1
              }
            ]
          },
          {
            "id": "step-02",
            "type": "takeaway",
            "label": "[FIXTURE] Durable principle, tied back to daf 1a",
            "speaker": "Board",
            "text": "[FIXTURE] The certification duty attaches at the point of intended sale - the same principle the opening ruling on 1a established for ordinary widgets. A qualified cross-daf reference back to the 1a opening rule.",
            "sourceRefs": [
              {
                "refType": "crossDaf",
                "targetDaf": "1a",
                "targetLineId": "demo-001a-l01",
                "targetVilnaLine": 1,
                "sourceType": "mishnah",
                "note": "Ties the daf 1b takeaway back to the daf 1a opening ruling"
              }
            ]
          }
        ],
        "topicTags": [
          "fixture-demo",
          "widget-certification",
          "prototype-exemption"
        ],
        "relatedSugyot": [
          "demo-001a-s01",
          "demo-001a-s02"
        ],
        "difficulty": "intro",
        "review": {
          "learning": "ai_generated",
          "argumentFlow": "ai_generated",
          "sourceRefs": "ai_generated"
        }
      }
    ],
    "review": {
      "status": "verified"
    }
  },
  "2a": {
    "canonicalRef": "[FIXTURE] Demo Tractate 2a",
    "daf": "2a",
    "summary": "[FIXTURE] Synthetic daf 2a of the demo tractate: a second, independent scenario about recalling a defective certified widget, exercising a fresh case/answer pair.",
    "sugyot": [
      {
        "id": "demo-002a-s01",
        "canonicalRef": "[FIXTURE] Demo Tractate 2a",
        "daf": "2a",
        "sugyaNumber": 1,
        "lineRange": {
          "startLineId": "demo-002a-l01",
          "endLineId": "demo-002a-l02",
          "startVilnaLine": 1,
          "endVilnaLine": 2
        },
        "display": {
          "title": "[FIXTURE] Recall window for defective widgets",
          "oneLine": "[FIXTURE] A defective certified widget must be recalled within thirty days of discovery.",
          "shortSummary": "[FIXTURE] The Board rules that a certified widget found defective must be recalled within thirty days, and clarifies that the clock starts on discovery, not on the defect's original occurrence.",
          "whats": "[FIXTURE] Synthetic explanatory text for the fixture's independent second-scenario sugya on daf 2a.",
          "hint": "[FIXTURE] Does the thirty-day clock start when the defect occurs or when it is discovered?"
        },
        "learning": {
          "learnerQuestion": "[FIXTURE] When does the thirty-day recall clock start?",
          "coreTension": "[FIXTURE] A defect may exist long before anyone notices it - starting the clock at occurrence could make timely recall impossible.",
          "coreMove": "[FIXTURE] The Board anchors the clock to discovery, a knowable and provable event, rather than occurrence.",
          "resolution": "[FIXTURE] The thirty-day clock starts on the Board's discovery of the defect.",
          "takeaway": {
            "type": "legal_principle",
            "text": "[FIXTURE] A compliance clock tied to a hidden event should instead be anchored to the first knowable, provable event."
          },
          "ahaMoment": "[FIXTURE] Anchoring the clock to discovery rather than occurrence is what makes the thirty-day rule actually enforceable.",
          "learningBlocker": "[FIXTURE] Assuming every deadline runs from when the underlying problem first arose.",
          "memoryAnchor": "[FIXTURE] Thirty days from when you find it, not from when it started."
        },
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
        ],
        "argumentFlow": [
          {
            "id": "step-01",
            "type": "case",
            "label": "[FIXTURE] Recall rule",
            "speaker": "Board",
            "text": "[FIXTURE] A certified widget found defective after sale must be recalled within thirty days of discovery.",
            "sourceRefs": [
              {
                "sourceType": "mishnah",
                "lineId": "demo-002a-l01",
                "vilnaLine": 1
              }
            ]
          },
          {
            "id": "step-02",
            "type": "answer",
            "label": "[FIXTURE] Clock starts on discovery",
            "speaker": "Board",
            "text": "[FIXTURE] The thirty-day clock starts on discovery by the Board, not on the defect's original occurrence.",
            "sourceRefs": [
              {
                "sourceType": "gemara",
                "lineId": "demo-002a-l02",
                "vilnaLine": 2
              }
            ]
          }
        ],
        "topicTags": [
          "fixture-demo",
          "widget-certification",
          "recall-procedure"
        ],
        "difficulty": "intro",
        "review": {
          "learning": "ai_generated",
          "argumentFlow": "ai_generated",
          "sourceRefs": "ai_generated"
        }
      }
    ],
    "review": {
      "status": "verified"
    }
  }
};

if (typeof module !== "undefined" && module.exports) {
  module.exports = { DATA_VERSION, DATA_SCHEMA_VERSION, LEARNING_DATA_VERSION,
    TRACTATE_META, PERAKIM, DAF_INDEX, DAF_CONTENT };
}
