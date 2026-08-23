#!/usr/bin/env python3
"""Smoke tests for semantic campaign packet/state tooling."""
from __future__ import annotations

from semantic_certification import certificate_status, corpus_status, load_corpus
from semantic_daf_packet import build_packet
from semantic_self_heal import action_for, ordered_details


def main() -> None:
    corpus = load_corpus("yoma")
    assert len(corpus) == 492

    packet = build_packet("yoma", "42a", False)
    assert packet["daf"] == "42a"
    assert packet["reviewMode"] == "FIRST_PASS"
    assert packet["authoritativeHebrewLines"], "whole-daf packet must contain Hebrew source first"
    assert packet["sugyot"], "whole-daf packet must contain all sugya candidates"
    assert all("currentEnrichment" in item for item in packet["sugyot"])
    assert any(item["sugyaId"] == "yoma-042a-s01" for item in packet["sugyot"])

    independent = build_packet("yoma", "42a", True)
    assert independent["reviewMode"] == "INDEPENDENT_SECOND_PASS"
    assert independent["independenceRule"]
    assert all("existingReviewRecord" not in item for item in independent["sugyot"]), (
        "second-pass packet must not expose first-pass review evidence"
    )

    counts, _details = corpus_status("yoma")
    assert sum(v for k, v in counts.items() if k != "ORPHANED_RECORD") == 492

    # The live registry legitimately gains CERTIFIED records as the campaign
    # progresses daf by daf, so asserting a fixed snapshot count (or that any
    # one specific sugya is still UNCERTIFIED) here would fail on ordinary,
    # correct progress rather than on an actual regression. The durable
    # "bootstrap grandfathers nothing" property is instead checked directly
    # against certificate_status with an explicit absent record (None) for
    # every corpus sugya, independent of whatever the live registry currently
    # contains.
    for sid, (daf, doc, sugya) in corpus.items():
        state, _problems = certificate_status("yoma", daf, doc, sugya, None)
        assert state == "UNCERTIFIED", (
            f"{sid}: a sugya with no certification record must default to "
            f"UNCERTIFIED regardless of legacy review metadata, got {state}"
        )

    assert action_for("UNCERTIFIED") == "AUDIT"
    assert action_for("REPAIR_REQUIRED") == "REPAIR"
    assert action_for("CERTIFIED") == "DONE"

    ordered = ordered_details("yoma")
    assert ordered[0][1]["daf"] == "2a", "live queue must start in corpus order"

    print("OK: semantic campaign packet and queue invariants hold")


if __name__ == "__main__":
    main()
