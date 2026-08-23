#!/usr/bin/env python3
"""Generate the manifest used by holistic semantic repair/certification PRs."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from semantic_certification import load_corpus


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--module", default="yoma")
    ap.add_argument("--daf", required=True)
    ap.add_argument("--type", choices=["semantic-daf-repair", "semantic-daf-certify"], required=True)
    ap.add_argument("--review-id", required=True)
    ap.add_argument("--sugya", action="append", dest="sugya_ids")
    ap.add_argument("--all-sugyot", action="store_true")
    ap.add_argument("--out", default=".semantic-repair-manifest.json")
    args = ap.parse_args()

    corpus = load_corpus(args.module)
    daf_ids = sorted(sid for sid, (daf, _, _) in corpus.items() if daf == args.daf)
    if not daf_ids:
        raise SystemExit(f"unknown/empty daf {args.daf!r}")
    if args.all_sugyot:
        ids = daf_ids
    else:
        ids = args.sugya_ids or []
        if not ids:
            raise SystemExit("provide --sugya one or more times, or --all-sugyot")
    unknown = sorted(set(ids) - set(daf_ids))
    if unknown:
        raise SystemExit(f"sugya ids not on {args.daf}: {unknown}")

    data = {
        "schemaVersion": "1.0",
        "type": args.type,
        "module": args.module,
        "daf": args.daf,
        "sugyaIds": ids,
        "firstReviewId": args.review_id,
        "policy": {
            "sourceFirst": True,
            "independentSecondPassRequired": True,
            "rawSourceImmutable": True,
            "rashiTranslationsImmutable": True,
            "certificationRegistryRequired": True,
        },
    }
    Path(args.out).write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"Wrote {args.out}: {args.type} {args.daf}, {len(ids)} sugya(s)")


if __name__ == "__main__":
    main()
