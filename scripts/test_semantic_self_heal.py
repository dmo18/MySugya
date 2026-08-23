#!/usr/bin/env python3
"""Smoke tests for semantic campaign packet/state tooling."""
from __future__ import annotations

from semantic_certification import corpus_status, load_corpus
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

    counts, details = corpus_status("yoma")
    assert sum(v for k, v in counts.items() if k != "ORPHANED_RECORD") == 492
    assert counts.get("UNCERTIFIED") == 492, "bootstrap must grandfather zero sugyot"
    assert details["yoma-042a-s01"]["state"] == "UNCERTIFIED"
    assert action_for("UNCERTIFIED") == "AUDIT"
    assert action_for("REPAIR_REQUIRED") == "REPAIR"
    assert action_for("CERTIFIED") == "DONE"

    ordered = ordered_details("yoma")
    assert ordered[0][1]["daf"] == "2a", "live queue must start in corpus order"

    print("OK: semantic campaign packet and queue invariants hold")


if __name__ == "__main__":
    main()
