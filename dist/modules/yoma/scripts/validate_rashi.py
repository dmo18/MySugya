#!/usr/bin/env python3
"""
validate_rashi.py - lighter validation for the Rashi helper layer in
learning_data.js. Rashi is a learning helper, NOT a source-critical layer, so
this is deliberately separate from (and looser than) the strict Gemara gates
(validate_sefaria.py / validate_en.py / order_audit.py).

Checks per enriched daf that carries rashiLines:
  1. Rashi Hebrew count + order match the talmud.dev source (assets/talmuddev/<daf>.json rashi[]).
  2. Every Rashi line has an en field whenever it has he (helper translation present).
  3. Every Rashi line is stamped with enSource.
  4. No Rashi Hebrew text has leaked into the Gemara source layer (lines:[] he/en).

Exit non-zero on any error.
"""
import re, json, sys
from pathlib import Path

ROOT = Path(__file__).parent.parent
DATA_JS = ROOT / "learning_data.js"
TALMUDDEV_DIR = ROOT / "assets" / "talmuddev"

STR = r'"((?:[^"\\]|\\.)*)"'  # JSON-escaped string body


def unescape(s):
    return json.loads('"' + s + '"')


def daf_blocks(text):
    """Yield (daf_id, block_text) for each // YOMA <daf> chunk in DAF_CONTENT."""
    starts = [(m.group(1), m.start()) for m in re.finditer(r'// YOMA (\S+)', text)]
    for i, (daf, s) in enumerate(starts):
        e = starts[i + 1][1] if i + 1 < len(starts) else len(text)
        yield daf, text[s:e]


def extract_rashi(block):
    """Return list of {vilnaLine, he, en, enSource} from a daf block's rashiLines:[]."""
    m = re.search(r'rashiLines:\s*\[', block)
    if not m:
        return []
    # bracket-track to the matching close of the rashiLines array,
    # skipping over quoted string literals so ] inside strings don't count
    i = m.end() - 1
    depth = 0
    j = i
    while j < len(block):
        c = block[j]
        if c == '"':
            # skip over the quoted string (handles \" escapes)
            j += 1
            while j < len(block):
                if block[j] == '\\':
                    j += 2
                    continue
                if block[j] == '"':
                    break
                j += 1
        elif c == '[':
            depth += 1
        elif c == ']':
            depth -= 1
            if depth == 0:
                arr = block[i:j + 1]
                break
        j += 1
    else:
        return []

    out = []
    # split into per-object segments on the id marker
    parts = re.split(r'(?=id:\s*"rashi-)', arr)
    for p in parts:
        if 'sourceType:' not in p:
            continue
        vl = re.search(r'vilnaLine:\s*(\d+)', p)
        he = re.search(r'\bhe:\s*' + STR, p)
        en = re.search(r'\ben:\s*' + STR, p)
        es = re.search(r'enSource:\s*' + STR, p)
        out.append({
            "vilnaLine": int(vl.group(1)) if vl else None,
            "he": unescape(he.group(1)) if he else None,
            "en": unescape(en.group(1)) if en else "",
            "enSource": unescape(es.group(1)) if es else None,
        })
    return out


def gemara_text(block):
    """Concatenate all he: and en: fields inside lines:[] blocks of a daf block."""
    chunks = []
    in_lines = False
    depth = 0
    for line in block.split("\n"):
        if not in_lines and re.search(r'\blines\s*:\s*\[', line):
            in_lines = True
            depth = line.count("[") - line.count("]")
            continue
        if in_lines:
            depth += line.count("[") - line.count("]")
            for m in re.finditer(r'\bhe:\s*' + STR, line):
                chunks.append(unescape(m.group(1)))
            for m in re.finditer(r'\ben:\s*' + STR, line):
                chunks.append(unescape(m.group(1)))
            if depth <= 0:
                in_lines = False
    return "\n".join(chunks)


def main():
    text = DATA_JS.read_text()
    errors = []
    checked = 0

    for daf, block in daf_blocks(text):
        rashi = extract_rashi(block)
        if not rashi:
            continue
        checked += 1

        td_path = TALMUDDEV_DIR / f"{daf}.json"
        if not td_path.exists():
            errors.append(f"{daf}: rashiLines present but {td_path.name} missing")
            continue
        src = [l for l in json.loads(td_path.read_text()).get("rashi", []) if l and l.strip()]

        # 1. count + order match talmud.dev
        if len(rashi) != len(src):
            errors.append(f"{daf}: rashiLines count {len(rashi)} != talmud.dev rashi[] count {len(src)}")
        else:
            for idx, (r, s) in enumerate(zip(rashi, src), 1):
                if r["he"] != s:
                    errors.append(f"{daf} rashi L{idx}: he does not match talmud.dev source")
                    break
                if r["vilnaLine"] != idx:
                    errors.append(f"{daf} rashi L{idx}: vilnaLine {r['vilnaLine']} out of order (expected {idx})")
                    break

        # 2 + 3. en present when he present; enSource stamped
        for r in rashi:
            tag = f"{daf} rashi L{r['vilnaLine']}"
            if r["he"] and not r["en"].strip():
                errors.append(f"{tag}: he present but en missing (helper translation required)")
            if not r["enSource"]:
                errors.append(f"{tag}: missing enSource stamp")

        # 4. no Rashi he leaked into the Gemara source layer
        gem = gemara_text(block)
        for r in rashi:
            he = (r["he"] or "").strip()
            if len(he) >= 12 and he in gem:
                errors.append(f"{daf} rashi L{r['vilnaLine']}: Rashi he text found inside Gemara lines:[] source layer")

    if errors:
        print("Rashi validation FAILED:\n")
        for e in errors:
            print(f"  ERROR  {e}")
        print(f"\n{len(errors)} error(s) across {checked} daf with rashiLines.")
        sys.exit(1)

    print(f"OK: Rashi helper layer valid across {checked} daf "
          f"(he matches talmud.dev order/count, en+enSource present, no leak into Gemara).")


if __name__ == "__main__":
    main()
