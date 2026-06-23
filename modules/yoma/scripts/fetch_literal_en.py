#!/usr/bin/env python3
"""
fetch_literal_en.py — fetch Sefaria WD translation and extract bold-tagged
literal portions as en_lit for each Gemara line.

The William Davidson Edition marks the literal translation text with <b> tags;
Steinsaltz commentary additions appear as plain text. This script extracts
only the bold portions to produce a direct, non-elucidated rendering.

Output: assets/literal_en/<daf>.json per daf
        assets/literal_en/progress.json (shared state - updated atomically)

Usage (run from modules/yoma/):
  python3 scripts/fetch_literal_en.py 2a
  python3 scripts/fetch_literal_en.py 2a 3a 4b
  python3 scripts/fetch_literal_en.py --range 2a 20b
  python3 scripts/fetch_literal_en.py --all
  python3 scripts/fetch_literal_en.py --all --skip-existing
"""

import argparse
import fcntl
import json
import re
import sys
import time
import urllib.request
from pathlib import Path

TRACTATE   = "Yoma"
SEFARIA    = "https://www.sefaria.org/api/texts"
OUT_DIR    = Path("assets/literal_en")
PROGRESS   = OUT_DIR / "progress.json"
DELAY      = 1.2   # seconds between requests - be polite to Sefaria
HEADERS    = {
    "User-Agent": "MySugya/11 (+https://github.com/dmo18/MySugya) research",
    "Accept":     "application/json",
}

ALL_DAF = [
    "2a","2b","3a","3b","4a","4b","5a","5b","6a","6b","7a","7b","8a","8b","9a","9b","10a","10b",
    "11a","11b","12a","12b","13a","13b","14a","14b","15a","15b","16a","16b","17a","17b","18a","18b","19a","19b","20a","20b",
    "21a","21b","22a","22b","23a","23b","24a","24b","25a","25b","26a","26b","27a","27b","28a","28b","29a","29b","30a","30b",
    "31a","31b","32a","32b","33a","33b","34a","34b","35a","35b","36a","36b","37a","37b","38a","38b","39a","39b","40a","40b",
    "41a","41b","42a","42b","43a","43b","44a","44b","45a","45b","46a","46b","47a","47b","48a","48b","49a","49b","50a","50b",
    "51a","51b","52a","52b","53a","53b","54a","54b","55a","55b","56a","56b","57a","57b","58a","58b","59a","59b","60a","60b",
    "61a","61b","62a","62b","63a","63b","64a","64b","65a","65b","66a","66b","67a","67b","68a","68b","69a","69b","70a","70b",
    "71a","71b","72a","72b","73a","73b","74a","74b","75a","75b","76a","76b","77a","77b","78a","78b","79a","79b","80a","80b",
    "81a","81b","82a","82b","83a","83b","84a","84b","85a","85b","86a","86b","87a","87b","88a",
]


def daf_index(daf_id: str) -> int:
    return ALL_DAF.index(daf_id)


def daf_range(start: str, end: str) -> list[str]:
    return ALL_DAF[daf_index(start): daf_index(end) + 1]


def strip_html(s: str) -> str:
    return re.sub(r"<[^>]+>", "", s).strip()


def extract_literal(en_html: str) -> str:
    """Extract bold-tagged segments as the literal translation portion."""
    if not en_html:
        return ""
    parts = re.findall(r"<(?:b|strong)>(.*?)</(?:b|strong)>", en_html, re.DOTALL)
    if not parts:
        # No bold markup - text may already be literal (e.g. older Sefaria refs)
        return strip_html(en_html)
    # Join bold parts, strip inner HTML tags (e.g. <i> for Aramaic terms)
    return " ".join(strip_html(p) for p in parts if strip_html(p))


def fetch_daf(daf_id: str) -> list[dict]:
    """Fetch WD translation for one daf; return list of {sefaria_ref, en_lit}."""
    ref = f"{TRACTATE}.{daf_id}"
    url = f"{SEFARIA}/{ref}?context=0"
    req = urllib.request.Request(url, headers=HEADERS)
    with urllib.request.urlopen(req, timeout=30) as resp:
        data = json.load(resp)

    raw_lines = data.get("text", [])
    versionTitle = data.get("versionTitle", "")
    sectionRef  = data.get("sectionRef", ref)

    results = []
    for i, raw in enumerate(raw_lines):
        text = raw if isinstance(raw, str) else ""
        en_lit = extract_literal(text)
        sefaria_ref = f"{TRACTATE}.{daf_id}.{i + 1}"
        results.append({
            "sefaria_ref": sefaria_ref,
            "en_lit":      en_lit,
            "source":      versionTitle,
        })

    return results


def load_progress() -> dict:
    if PROGRESS.exists():
        with open(PROGRESS) as f:
            return json.load(f)
    return {"completed": [], "failed": [], "pending": list(ALL_DAF)}


def save_progress(prog: dict) -> None:
    tmp = PROGRESS.with_suffix(".tmp")
    with open(tmp, "w") as f:
        json.dump(prog, f, indent=2, ensure_ascii=False)
        f.flush()
    tmp.replace(PROGRESS)


def mark_complete(daf_id: str) -> None:
    """Atomically update progress.json - safe for concurrent agents."""
    lock_path = PROGRESS.with_suffix(".lock")
    with open(lock_path, "w") as lock:
        fcntl.flock(lock, fcntl.LOCK_EX)
        try:
            prog = load_progress()
            if daf_id not in prog["completed"]:
                prog["completed"].append(daf_id)
            prog["pending"] = [d for d in prog.get("pending", []) if d != daf_id]
            prog["failed"]  = [d for d in prog.get("failed",  []) if d != daf_id]
            save_progress(prog)
        finally:
            fcntl.flock(lock, fcntl.LOCK_UN)


def mark_failed(daf_id: str) -> None:
    lock_path = PROGRESS.with_suffix(".lock")
    with open(lock_path, "w") as lock:
        fcntl.flock(lock, fcntl.LOCK_EX)
        try:
            prog = load_progress()
            if daf_id not in prog["failed"]:
                prog["failed"].append(daf_id)
            prog["pending"] = [d for d in prog.get("pending", []) if d != daf_id]
            save_progress(prog)
        finally:
            fcntl.flock(lock, fcntl.LOCK_UN)


def process_daf(daf_id: str, skip_existing: bool) -> bool:
    out_file = OUT_DIR / f"{daf_id}.json"
    if skip_existing and out_file.exists():
        print(f"  skip {daf_id} (exists)")
        return True

    print(f"  fetch {TRACTATE}.{daf_id} ...", end=" ", flush=True)
    try:
        lines = fetch_daf(daf_id)
        out_file.write_text(json.dumps({"daf": daf_id, "lines": lines}, indent=2, ensure_ascii=False))
        mark_complete(daf_id)
        print(f"OK ({len(lines)} lines)")
        return True
    except Exception as e:
        mark_failed(daf_id)
        print(f"FAIL: {e}")
        return False


def main():
    parser = argparse.ArgumentParser(description="Fetch literal en_lit for Yoma daf.")
    parser.add_argument("daf", nargs="*", help="Specific daf IDs (e.g. 2a 3b 4a)")
    parser.add_argument("--all", action="store_true", help="Fetch all 173 content daf")
    parser.add_argument("--range", nargs=2, metavar=("START", "END"), help="Daf range inclusive")
    parser.add_argument("--skip-existing", action="store_true", help="Skip daf that already have output files")
    parser.add_argument("--status", action="store_true", help="Print progress summary and exit")
    args = parser.parse_args()

    OUT_DIR.mkdir(parents=True, exist_ok=True)

    if args.status:
        prog = load_progress()
        total = len(ALL_DAF)
        done  = len(prog.get("completed", []))
        fail  = len(prog.get("failed", []))
        pend  = len(prog.get("pending", ALL_DAF))
        print(f"Progress: {done}/{total} complete, {fail} failed, {pend} pending")
        if prog.get("failed"):
            print("Failed:", " ".join(prog["failed"]))
        return

    if args.all:
        targets = list(ALL_DAF)
    elif args.range:
        targets = daf_range(args.range[0], args.range[1])
    elif args.daf:
        targets = args.daf
    else:
        parser.print_help()
        sys.exit(1)

    print(f"Fetching {len(targets)} daf from Sefaria ({TRACTATE})...")
    ok = fail = 0
    for i, daf_id in enumerate(targets):
        success = process_daf(daf_id, args.skip_existing)
        if success:
            ok += 1
        else:
            fail += 1
        if i < len(targets) - 1:
            time.sleep(DELAY)

    print(f"\nDone: {ok} OK, {fail} failed")


if __name__ == "__main__":
    main()
