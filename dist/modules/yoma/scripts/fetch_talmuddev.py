#!/usr/bin/env python3
"""
fetch_talmuddev.py — fetch Vilna-layout Gemara text from talmud.dev

talmud.dev /api/daf/<tractate>/<page> returns the full Gemara page in Vilna
print order with \r\n line breaks matching the printed column. This is the
authoritative source for Vilna line positions without needing PDF/OCR.

Outputs JSON to assets/talmuddev/<daf>.json with:
  lines:  list of unvowelized Hebrew strings (one per Vilna print line)
  rashi:  list of unvowelized Rashi strings (one per Vilna print line)

Usage:
  python3 scripts/fetch_talmuddev.py 2a
  python3 scripts/fetch_talmuddev.py 2a 2b 3a
  python3 scripts/fetch_talmuddev.py --all
  python3 scripts/fetch_talmuddev.py --all --skip-existing
"""

import argparse
import json
import re
import sys
import time
import urllib.request
from pathlib import Path

TRACTATE = "Yoma"
BASE_URL = "https://www.talmud.dev/api/daf"
OUT_DIR = Path("assets/talmuddev")
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36",
    "Accept": "application/json",
}


def strip_html(s: str) -> str:
    return re.sub(r"<[^>]+>", "", s)


def split_lines(raw: str) -> list[str]:
    lines = []
    for ln in raw.split("\r\n"):
        ln = strip_html(ln).strip()
        if ln:
            lines.append(ln)
    return lines


def fetch_daf(daf_id: str) -> dict:
    url = f"{BASE_URL}/{TRACTATE}/{daf_id}"
    req = urllib.request.Request(url, headers=HEADERS)
    with urllib.request.urlopen(req, timeout=30) as resp:
        d = json.load(resp)
    gemara_lines = split_lines(d.get("mainText", {}).get("hebrew", ""))
    rashi_lines = split_lines(d.get("rashi", {}).get("hebrew", ""))
    return {"daf": daf_id, "lines": gemara_lines, "rashi": rashi_lines}


def main():
    ap = argparse.ArgumentParser(description="Fetch talmud.dev Vilna-layout text")
    ap.add_argument("dafs", nargs="*", help="Daf IDs (e.g. 2a 2b 3a)")
    ap.add_argument("--all", action="store_true", help="Fetch all Yoma daf (2a–88a)")
    ap.add_argument("--skip-existing", action="store_true", help="Skip daf with existing JSON")
    args = ap.parse_args()

    if args.all:
        dafs = [f"{n}{s}" for n in range(2, 89) for s in ("a", "b") if not (n == 88 and s == "b")]
    elif args.dafs:
        dafs = args.dafs
    else:
        ap.print_help()
        sys.exit(1)

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    ok = err = 0
    for i, daf_id in enumerate(dafs):
        out_path = OUT_DIR / f"{daf_id}.json"
        if args.skip_existing and out_path.exists():
            print(f"  [{daf_id}] SKIP")
            continue
        print(f"  [{daf_id}] fetching...", end=" ", flush=True)
        try:
            data = fetch_daf(daf_id)
            out_path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
            print(f"{len(data['lines'])} gemara lines, {len(data['rashi'])} rashi lines → {out_path.name}")
            ok += 1
        except Exception as e:
            print(f"ERROR: {e}")
            err += 1
        if i + 1 < len(dafs):
            time.sleep(0.5)

    print(f"\nDone: {ok} ok, {err} failed")


if __name__ == "__main__":
    main()
