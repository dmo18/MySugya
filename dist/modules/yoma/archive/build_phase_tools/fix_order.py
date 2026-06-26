#!/usr/bin/env python3
"""
fix_order.py — restore Vilna/Sefaria reading order inside every daf of source_store.js.

For each daf:
  1. Fetch the daf's Sefaria he[] segments; build a letters-only stream.
  2. Locate every line object's he: text in that stream → true position.
  3. Drop true duplicates (same passage present more times than in Sefaria).
  4. Sort line objects by true position.
  5. Re-partition the sorted blocks into the daf's existing sugyot as
     contiguous runs, maximizing agreement with original membership
     (sugyot themselves are re-ordered by their content's median position).
  6. Rewrite the daf section. Blocks are moved verbatim — no character of
     any field is altered.

Only daf whose order actually changes are rewritten.

Usage:
  python3 scripts/fix_order.py            # dry-run report
  python3 scripts/fix_order.py --apply    # write source_store.js
  python3 scripts/fix_order.py 5a --apply # specific daf (writes source_store.js)
"""

import json
import re
import sys
import time
import unicodedata
import urllib.request

DATA_JS = "source_store.js"
HEB = re.compile(r"[א-ת]")


def letters_of(text):
    return "".join(ch for ch in unicodedata.normalize("NFC", text) if HEB.match(ch))


def fetch_letters(daf_id):
    url = f"https://www.sefaria.org/api/texts/Yoma.{daf_id}?lang=he&context=0"
    req = urllib.request.Request(url, headers={"User-Agent": "YomaOrderFix/1.0"})
    with urllib.request.urlopen(req, timeout=20) as resp:
        data = json.loads(resp.read().decode("utf-8"))
    return "".join(letters_of(s) for s in data.get("he", []))


# ---------------------------------------------------------------------------
# string-aware structure scanning
# ---------------------------------------------------------------------------

def match_bracket(content, open_pos):
    """Index of the bracket matching content[open_pos] ('{'/'[')."""
    open_ch = content[open_pos]
    close_ch = {"{": "}", "[": "]"}[open_ch]
    depth = 0
    in_str = False
    i = open_pos
    while i < len(content):
        c = content[i]
        if in_str:
            if c == "\\":
                i += 2
                continue
            if c == '"':
                in_str = False
        elif c == '"':
            in_str = True
        elif c == open_ch:
            depth += 1
        elif c == close_ch:
            depth -= 1
            if depth == 0:
                return i
        i += 1
    raise ValueError("unbalanced brackets")


def top_level_objects(content, start, end):
    """Spans (s, e_inclusive) of top-level {...} objects in content[start:end]."""
    spans = []
    i = start
    in_str = False
    while i < end:
        c = content[i]
        if in_str:
            if c == "\\":
                i += 2
                continue
            if c == '"':
                in_str = False
            i += 1
            continue
        if c == '"':
            in_str = True
            i += 1
            continue
        if c == "{":
            j = match_bracket(content, i)
            spans.append((i, j))
            i = j + 1
            continue
        i += 1
    return spans


def get_str_field(src, key):
    m = re.search(r'\b' + key + r'\s*:\s*"((?:[^"\\]|\\.)*)"', src)
    if not m:
        return None
    return m.group(1).replace('\\"', '"').replace("\\\\", "\\").replace("\\n", " ")


# ---------------------------------------------------------------------------
# per-daf fixing
# ---------------------------------------------------------------------------

def locate_blocks(blocks, stream):
    """Assign .pos to each block; mark duplicates beyond Sefaria's count.
    Returns (located_blocks, dropped_reports)."""
    by_text = {}
    for b in blocks:
        if b["letters"]:
            by_text.setdefault(b["letters"], []).append(b)

    dropped = []
    for text, group in by_text.items():
        occs = []
        p = stream.find(text)
        while p != -1:
            occs.append(p)
            p = stream.find(text, p + 1)
        if not occs:
            for b in group:
                b["pos"] = None        # unlocatable → rider
            continue
        if len(group) > len(occs):
            # true duplicates: keep the first len(occs) blocks in file order
            for b in group[len(occs):]:
                b["dup"] = True
                dropped.append(b)
            group = group[: len(occs)]
        if len(group) == 1 and len(occs) > 1:
            # repeated passage in Sefaria, single block: pick occurrence
            # closest to the median position of its sugya's unique siblings
            sib = [x["pos"] for x in blocks
                   if x.get("pos") is not None and x["sug"] == group[0]["sug"]]
            anchor = sorted(sib)[len(sib) // 2] if sib else occs[0]
            group[0]["pos"] = min(occs, key=lambda o: abs(o - anchor))
        else:
            for b, o in zip(group, occs):
                b["pos"] = o
    return dropped


def fix_daf(content, daf, sec_start, sec_end, report):
    sug_m = re.search(r'\bsugyot\s*:\s*\[', content[sec_start:sec_end])
    if not sug_m:
        return None
    arr_open = sec_start + sug_m.end() - 1
    arr_close = match_bracket(content, arr_open)

    sugya_spans = top_level_objects(content, arr_open + 1, arr_close)
    if not sugya_spans:
        return None

    sugyas = []
    all_blocks = []
    for k, (ss, se) in enumerate(sugya_spans):
        ssrc = content[ss:se + 1]
        lm = re.search(r'\blines\s*:\s*\[', ssrc)
        if not lm:
            sugyas.append({"src": ssrc, "lopen": None})
            continue
        lopen = lm.end() - 1
        lclose = match_bracket(ssrc, lopen)
        blocks = []
        for bs, be in top_level_objects(ssrc, lopen + 1, lclose):
            bsrc = ssrc[bs:be + 1]
            he = get_str_field(bsrc, "he") or ""
            blocks.append({
                "src": bsrc, "letters": letters_of(he),
                "sug": k, "pos": None, "dup": False,
            })
        sugyas.append({"src": ssrc, "lopen": lopen, "lclose": lclose,
                       "blocks": blocks})
        all_blocks.extend(blocks)

    if not all_blocks:
        return None

    try:
        stream = fetch_letters(daf)
    except Exception as e:
        report.append((daf, f"SKIP — Sefaria fetch failed: {e}"))
        return None
    time.sleep(0.3)

    dropped = locate_blocks(all_blocks, stream)
    for b in dropped:
        report.append((daf, f"DROP duplicate passage: “{b['letters'][:40]}…”"))

    kept = [b for b in all_blocks if not b["dup"]]

    # riders (unlocatable / empty) travel with the previous located block
    hosts = []
    for b in kept:
        if b["pos"] is None:
            if hosts:
                hosts[-1]["riders"].append(b)
                report.append((daf, f"RIDER (not in Sefaria stream, kept with "
                                    f"neighbor): “{(b['letters'] or '·')[:40]}”"))
            else:
                b["pos"] = -1
                b["riders"] = []
                hosts.append(b)
        else:
            b["riders"] = []
            hosts.append(b)

    old_order = [b["pos"] for b in hosts]
    sorted_hosts = sorted(hosts, key=lambda b: b["pos"])
    order_changed = [b["pos"] for b in sorted_hosts] != old_order

    if not order_changed and not dropped:
        return None

    # sugya output order: by median of member positions
    K = len(sugya_spans)
    members = {k: [] for k in range(K)}
    for b in hosts:
        members[b["sug"]].append(b["pos"])
    def med(k):
        v = sorted(members[k])
        return v[len(v) // 2] if v else 10 ** 12
    sug_order = sorted(range(K), key=lambda k: (med(k), k))

    # DP: partition sorted_hosts into K contiguous non-empty runs
    N = len(sorted_hosts)
    if N < K:
        report.append((daf, f"ERROR: {N} blocks < {K} sugyot — manual fix needed"))
        return None
    NEG = float("-inf")
    dp = [[NEG] * (K + 1) for _ in range(N + 1)]
    par = [[0] * (K + 1) for _ in range(N + 1)]
    dp[0][0] = 0
    for j in range(1, K + 1):
        sk = sug_order[j - 1]
        for i in range(j, N - (K - j) + 1):
            best, bp = NEG, 0
            gain = 0
            # run = blocks p..i-1 for p from i-1 down to j-1
            for p in range(i - 1, j - 2, -1):
                gain += 1 if sorted_hosts[p]["sug"] == sk else 0
                if dp[p][j - 1] != NEG and dp[p][j - 1] + gain > best:
                    best, bp = dp[p][j - 1] + gain, p
            dp[i][j], par[i][j] = best, bp
    # reconstruct boundaries
    bounds = []
    i = N
    for j in range(K, 0, -1):
        p = par[i][j]
        bounds.append((p, i))
        i = p
    bounds.reverse()

    moved = sum(1 for j, (p, q) in enumerate(bounds)
                for b in sorted_hosts[p:q] if b["sug"] != sug_order[j])
    report.append((daf, f"REORDERED — {N} blocks, {len(dropped)} dup(s) dropped, "
                        f"{moved} block(s) changed sugya, "
                        f"sugya order {[s + 1 for s in sug_order]}"))

    # rebuild sugya sources
    new_sug_srcs = []
    for j, k in enumerate(sug_order):
        sg = sugyas[k]
        p, q = bounds[j]
        run = []
        for b in sorted_hosts[p:q]:
            run.append(b["src"])
            run.extend(r["src"] for r in b["riders"])
        inner = ",\n            ".join(run)
        ssrc = sg["src"]
        new_ssrc = (ssrc[:sg["lopen"] + 1] + "\n            " + inner +
                    "\n        " + ssrc[sg["lclose"]:])
        new_sug_srcs.append(new_ssrc)

    new_arr_inner = "\n      " + ",\n      ".join(new_sug_srcs) + "\n    "
    return (arr_open + 1, arr_close, new_arr_inner)


def main():
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    apply_mode = "--apply" in sys.argv
    target = set(args) if args else None

    with open(DATA_JS, encoding="utf-8") as f:
        content = f.read()

    daf_re = re.compile(r'^(\s*)"(\d+[ab])":\s*\{', re.MULTILINE)
    sections = []
    for m in daf_re.finditer(content):
        open_pos = content.index("{", m.end() - 1)
        close = match_bracket(content, open_pos)
        sections.append((m.group(2), open_pos, close))

    report = []
    patches = []
    for daf, s, e in sections:
        if target and daf not in target:
            continue
        r = fix_daf(content, daf, s, e, report)
        if r:
            patches.append(r)

    for daf, msg in report:
        print(f"[{daf}] {msg}")

    print(f"\n{len(patches)} daf need rewriting.")
    if not apply_mode:
        print("(dry-run — use --apply to write)")
        return
    patches.sort(key=lambda x: x[0], reverse=True)
    for s, e, repl in patches:
        content = content[:s] + repl + content[e:]
    with open(DATA_JS, "w", encoding="utf-8") as f:
        f.write(content)
    print("source_store.js written.")


if __name__ == "__main__":
    main()
