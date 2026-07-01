# Tractate Build Process

Generalized, procedural reference for taking a masechta from zero to a
frozen, production-quality module, written from the Yoma build. Replace
`<masechta>`/`yoma` with the new tractate id throughout. This document
describes process. For the concrete history of how Yoma specifically
reached its current state, see `docs/yoma-completion-report.md`.

Read this alongside `CLAUDE.md` (project-wide rules) and
`modules/<masechta>/MODULE.md` (per-module frozen-state declaration, once
one exists).

---

## 1. Tractate ingestion and source layout

Each module is self-contained under `modules/<masechta>/`:

```text
modules/<masechta>/
  learning_data.js            GENERATED runtime data, do not hand-edit
  source_store.js             Sefaria-verified Gemara he/en, source of truth
  MODULE.md                   Per-module frozen-state declaration
  scripts/
    build_learning_data.py    Generates learning_data.js from source_store.js + assets/
    build_literal_layer.py    Injects en_lit fields from assets/literal_en/
    fetch_literal_en.py       Fetches literal translation source
    fetch_talmuddev.py        Refreshes the talmud.dev Vilna-line cache
    daftext_align.py          Embeds Vilna line breaks into daftexts
    validate_sefaria.py       Gate: he: fields match live Sefaria
    validate_en.py            Gate: en: fields align to correct he: segment
    validate_daftext.py       Gate: daftexts match talmud.dev source
    validate_rashi.py         Gate: Rashi helper layer structural integrity
    validate_literal.py       Gate: en_lit coverage threshold
    validate_schema_completeness.py   Gate: display/learning schema present
    order_audit.py            Gate: Vilna sequence, no inversions
    completeness_audit.py     Every Sefaria segment represented
  assets/
    daftexts/<daf>.txt              Generated Vilna-line daf text, do not hand-edit
    talmuddev/<daf>.json             Vilna line source cache, do not modify
    learning/<masechta>/<daf>.learning.json   Enrichment source, the only human-editable content layer
    literal_en/<daf>.json            Raw literal-translation fetch output
    literal_en/progress.json         Atomic fetch progress tracker
```

Ingestion order for a new masechta:

1. **Source store.** Fetch each daf from the Sefaria API. Copy `he:`/`en:`
   verbatim into `modules/<masechta>/source_store.js`. Never alter these
   fields once fetched; they are the ground truth against which
   `validate_sefaria.py` checks.
2. **talmud.dev cache.** Run `fetch_talmuddev.py` to pull the Vilna-line
   reference cache used for daftext generation and order auditing.
3. **Daftexts.** Generate `assets/daftexts/<daf>.txt` from the talmud.dev
   cache. These are compressed, line-numbered Hebrew text with `וכו'`
   (etc.) elisions in some places, matching the printed Vilna page - not a
   full transcript. Treat truncations as real; do not assume more content
   is available locally than the file contains.
4. **Vilna line breaks.** Run `daftext_align.py` to embed line-break
   markers matching the physical Vilna edition.
5. **Enrichment JSON.** Create one `<daf>.learning.json` per daf under
   `assets/learning/<masechta>/`. This is the only layer intended for
   ongoing human/AI authoring. See Sections 4-8 for how to populate it to
   completion.
6. **Build.** Run `python3 scripts/build_learning_data.py` from
   `modules/<masechta>/` to generate `learning_data.js`.
7. **Manifest.** Add an entry to root `manifest.js` with the correct
   `dataScript` path (`modules/<id>/learning_data.js`, lowercase
   alphanumeric id only - both the build script and the app's runtime
   guard enforce this pattern and reject anything else).
8. Run every validation gate in Section 10, then the standard test suite.

---

## 2. Generated vs source file rules

Every file under a module falls into exactly one of three categories.
Getting this wrong is the single most common source of wasted work.

| Category | Files | Rule |
|---|---|---|
| **Verbatim source** | `source_store.js`, `assets/talmuddev/*.json` | Never edit by hand. Re-fetch from the origin (Sefaria API, talmud.dev) if wrong. |
| **Generated** | `learning_data.js`, `assets/daftexts/*.txt` | Never edit by hand. Regenerate from source + enrichment via the build scripts. |
| **Enrichment source** | `assets/learning/<masechta>/<daf>.learning.json` | The only layer meant for ongoing edits. Edit here, then regenerate the generated layer. |

The failure mode to avoid: hand-editing `learning_data.js` directly. It
will pass a casual visual check, diverge from the enrichment JSON that is
supposed to be the source of truth, and get silently overwritten (losing
the edit) the next time anyone runs `build_learning_data.py`. Always edit
the `.learning.json` file, then rebuild.

---

## 3. Versioning and sync rules

`VERSION` (repo root) is the single human-edited version source. Format:
`\d+\.\d+` (enforced by `scripts/sync_version.py`, which rejects anything
else).

After editing `VERSION`:

```bash
python3 scripts/sync_version.py
```

This propagates the value into `package.json` and `package-lock.json`
only. It does not touch `manifest.js` `dataVersion` or a module's
`DATA_VERSION` export - those are data-layer versions, tracked
independently, and are not required to match the platform `VERSION`.

Never hand-edit `package.json`/`package-lock.json` to change the version.
The pre-commit hook (`githooks/pre-commit`) also runs `sync_version.py`
automatically and stages `VERSION package.json package-lock.json
index.html manifest.js modules/<masechta>/learning_data.js`, so a commit
with a stale `VERSION` value gets caught, but do not rely on the hook as
your only version-bump step - run `sync_version.py` yourself before
staging so the diff you review matches what gets committed.

Bump `VERSION` for any tracked change to app code, platform tooling,
tests, or docs - including documentation-only passes like this one. A
docs-only change still gets its own version bump and its own commit.

---

## 4. Schema completeness audit

Before backfilling anything, establish the baseline:

```bash
npm run validate:schema:yoma
```

(substitute the module's npm script name; the pattern is
`validate:schema:<masechta>` -> `cd modules/<masechta> && python3
scripts/validate_schema_completeness.py`)

This checks a different layer than the other validators: whether each
sugya's enrichment JSON carries the `display`/`learning` fields that
`shared/schema_map.js` declares required and that `app.jsx` renders as the
sugya heading and the LearningPanel. It does not check source text
alignment (`he:`/`en:`/Vilna order) at all - a sugya can pass every other
gate while still failing this one if its enrichment predates the current
canonical schema.

This gate is not wired into the default `npm test` chain, because a
mid-backfill corpus is expected to fail it. Run it manually to get a
per-daf pass/fail count and the total failing-sugyot count. That count is
your backlog size for Section 5.

---

## 5. Mechanical backfill process

Once the schema gate identifies incomplete sugyot, backfill in batches
small enough to review and roll back cleanly (Yoma used batches of
roughly 20-50 sugyot, one or two daf-ranges per commit).

Per batch:

1. Pick a contiguous daf range with known-incomplete sugyot.
2. For each sugya, populate the required `display`/`learning` fields
   (`display.title`, `learning.learnerQuestion`, `learning.coreTension`,
   `learning.coreMove`, `learning.takeaway.{type,text}`,
   `learning.ahaMoment`, `learning.learningBlocker`,
   `learning.memoryAnchor`) grounded strictly in that sugya's own
   `argumentFlow` and daftext content. See the enrichment quality
   standards in `CLAUDE.md` (no fabricated argument steps, no generic
   quiz/misconception stubs, Rashi English must say what Rashi adds).
3. Use only the canonical `takeaway.type` values from the start of a new
   backfill effort: `logical_principle`, `derivation_principle`,
   `legal_principle`, `conceptual`, `open_question`. (Yoma's early batches
   predated this canonical list and required a separate normalization
   pass - Section 8 - to clean up after the fact. Starting a new tractate
   with the canonical list from day one avoids that rework.)
4. Rebuild: `cd modules/<masechta> && python3 scripts/build_learning_data.py`
5. Reinject the literal layer if applicable:
   `npm run build:literal:<masechta>`
6. Run the full validator suite (Section 10).
7. Bump `VERSION`, sync, commit, push.
8. Confirm CI is green (Section 12) before starting the next batch.

Do not start the next batch until the current batch's deploy is
confirmed green. Backfilling on top of a red deploy compounds the
debugging surface.

---

## 6. Semantic/perek review process

Once schema completeness reaches 100%, do one pass reading each perek's
sugyot in sequence to check that the corpus coheres as a learning
narrative, not just as individually-valid records. This is qualitatively
different from the schema gate (structure) and the source validators
(text alignment) - it checks meaning and continuity.

**Step 1: fast title-only scan.** Pull each perek's daf range and every
sugya title in daf order (the `DAF_INDEX` topic summaries in
`learning_data.js`, or a script over the enrichment JSON, both work).
Read titles straight through per perek looking for: jarring topic jumps,
titles that don't match the perek's stated arc, and recurring topics that
might be duplicated scaffolding rather than the Mishnah's own repeated
structure (see the false-positive note below).

**Step 2: programmatic duplicate/crosswire scan.** Run an exact-string
comparison of `learnerQuestion`, `ahaMoment`, and `memoryAnchor` across
all sugyot. Two sugyot sharing identical text in these fields, especially
when they are adjacent in the same daf file, is strong evidence one
copied the other's fields during backfill. This catches most crosswiring
cheaply:

```python
import json, glob
from collections import defaultdict
files = sorted(glob.glob('modules/<masechta>/assets/learning/<masechta>/*.learning.json'))
aha_map = defaultdict(list)
for f in files:
    for s in json.load(open(f)).get('sugyot', []):
        a = s.get('learning', {}).get('ahaMoment', '')
        if a:
            aha_map[a].append(s['id'])
for a, ids in aha_map.items():
    if len(ids) > 1:
        print(ids, a[:80])
```

Repeat for `memoryAnchor` and `learnerQuestion`.

**Step 3: heuristic keyword-overlap scan (optional, high false-positive
rate).** A lower-confidence check: compute keyword overlap between each
sugya's title/learnerQuestion and its own ahaMoment/memoryAnchor. Low
overlap can indicate crosswiring, but figurative or paraphrased AHAs
routinely score low without being wrong. Treat this as a candidate list
to manually verify, not a findings list to act on directly - in Yoma's
review, roughly 27 sugyot were flagged this way and all but the ones
already caught by Step 2 turned out to be legitimate paraphrases.

**Step 4: verify each candidate against its own argumentFlow.** For every
sugya flagged by Steps 2-3, read the full sugya JSON (`display`,
`learning`, `argumentFlow`) and, if still ambiguous, the daftext for its
line range. Confirm whether the flagged field genuinely belongs to a
different sugya (crosswire, fixable) or is a distinct-but-legitimate angle
on the same passage (near-duplicate requiring new authoring, not a simple
field swap) or reflects real Mishnaic structure (a summary list that
legitimately recurs across peraqim - not an error at all; note it as an
observation, don't fix it).

**Step 5: write the review doc.** Produce (or update) a perek-by-perek
review doc structured like `docs/yoma-perek-review.md`: for each perek,
daf range, sugya count, a flow summary, an "Issues found" subsection using
the fix/defer/document decision tree in Section 16, and an "Observations"
subsection for things worth noting that need no fix. Close with summary
tables: fixes applied, content requiring new authoring, content requiring
external source review.

---

## 7. Source-text contradiction review process

Some sugyot will contain internally contradictory fields - one field
saying X, another saying not-X. Resolving these requires more care than
ordinary crosswiring, because a bad guess corrupts the corpus with a
confident-sounding falsehood.

**Tier 1: local corpus exhaustion.** Before touching anything, check every
locally-embedded source:

1. The sugya's own daftext line range - read it directly, and check for
   truncation markers (`וכו'`, "etc.") that mean the compressed daf text
   elides the resolving content.
2. The sugya's own `argumentFlow`, `misconceptions`, `finalRuling`, and
   `quizSeeds` - sometimes one of these independently states the correct
   answer even though the primary learning fields disagree.
3. The `rashiTranslations` array for the same line range - note that
   older enrichment batches may use a different indexing scheme (some
   Yoma files index by Sefaria segment number with empty `he:` fields
   rather than by true Vilna line with full metadata; check which schema
   a given file uses before assuming a `vilnaLine` value means what it
   usually means).
4. A corpus-wide grep across every `<daf>.learning.json` for any
   terminology specific to the disputed point (a technical term, a named
   measure, a named ritual object). If no other daf in the corpus
   corroborates a proposed resolution, that resolution is not
   locally-sourced, even if it is correct - do not present it as if it
   were.

If Tier 1 resolves the contradiction, fix only the fields that were
actually wrong, cite the resolving local content in the review doc entry,
and stop.

**Tier 2: external source review.** If Tier 1 is exhausted and the
contradiction remains unresolved, this requires consulting a source
outside the local corpus. Do not rely on training-data memory of the
Gemara for this - cite a fetched, checkable source.

1. Use `WebFetch` against the Sefaria API for the exact segment
   (`https://www.sefaria.org/api/texts/<Ref>.<n>` or
   `https://www.sefaria.org/<Ref>.<n>`), requesting both Hebrew and
   English.
2. Confirm the Hebrew Sefaria returns matches the local daftext line
   byte-for-byte (or matches the un-truncated portion exactly) before
   trusting the English translation as applying to the same passage.
3. Record in the review doc: the exact source, edition, and URL used; the
   matching-Hebrew confirmation; the resolving English text verbatim or
   closely paraphrased; and which specific fields the resolution
   contradicts and why.
4. Rewrite only the fields that were actually inconsistent with the now-
   confirmed resolution. Do not do a broader wording pass on fields that
   were already correct.

If external review is not available or not authorized for the current
pass, do not guess. Document the contradiction per Section 16 and defer.

---

## 8. `takeaway.type` normalization process

`takeaway.type` has five canonical values: `logical_principle`,
`derivation_principle`, `legal_principle`, `conceptual`, `open_question`.
The app does not render this field - a non-canonical value is a data
consistency issue, not a user-visible defect, so it is safe to defer or
batch.

To normalize:

1. Scan the corpus for non-canonical values and their frequency:

```python
import json, glob
from collections import Counter
canonical = {'logical_principle','derivation_principle','legal_principle','conceptual','open_question'}
c = Counter()
for f in glob.glob('modules/<masechta>/assets/learning/<masechta>/*.learning.json'):
    for s in json.load(open(f)).get('sugyot', []):
        t = s.get('learning', {}).get('takeaway', {}).get('type')
        if t not in canonical:
            c[t] += 1
print(c)
```

2. Build an explicit mapping table (non-canonical value -> canonical
   value) and record it in the review doc before touching any file. This
   makes the normalization auditable and reversible.
3. Apply the mapping with a text-level, context-anchored regex, not a
   full JSON re-serialization (re-serializing risks unrelated formatting
   diffs and can accidentally touch other fields, like
   `reasoningPattern.category`, that happen to share the same string
   values):

```python
import re
pattern = re.compile(r'("takeaway":\s*\{\s*"type":\s*")([a-zA-Z_-]+)(")')
```

   Verify first that every `"takeaway": {` in the corpus is immediately
   followed by `"type"` (a structural sanity check) so the regex cannot
   accidentally match a different field.
4. Confirm after the pass: zero non-canonical values remain, and a diff
   of the affected files shows only `"type"` lines changed - no
   `"text"` lines, no `reasoningPattern` lines.
5. Rebuild, validate, bump version, commit as its own pass, separate from
   any content-correctness fixes.

---

## 9. Rashi audit preparation (not the audit itself)

Do not perform Rashi alignment or nekudot (vowelization) correction work
casually or as a side effect of other passes. When preparing to schedule a
dedicated Rashi audit:

1. Confirm `validate:rashi:yoma`-equivalent structural gate is green
   first (he order/count matches talmud.dev, `en:`/`enSource:` present,
   no leakage of Rashi text into Gemara lines). This is a prerequisite,
   not a substitute for the audit.
2. Create or update a backlog doc (`docs/rashi-audit-backlog.md` pattern)
   that states explicitly what a dedicated pass must check beyond the
   structural gate: content-alignment/translation-quality issues the
   structural validator cannot catch, and nekudot/vowelization
   correctness in the `he:` fields.
3. Log any Rashi-adjacent findings noticed incidentally while doing other
   work (perek review, contradiction resolution) into that backlog doc
   as read-only entries. Do not act on them. The explicit rule: finding a
   probable Rashi issue during an unrelated pass is a reason to write one
   line in the backlog, never a reason to edit Rashi content in that same
   pass.
4. Do not start the audit itself until explicitly instructed. The
   preparation step's job is to leave a clean, actionable starting point
   for that separate, later pass.

---

## 10. Validation gates and when each gate is required

| Gate | Command | Checks | Required when |
|---|---|---|---|
| Schema completeness | `npm run validate:schema:<masechta>` | display/learning fields present | Before/after any backfill or content-correctness pass touching enrichment JSON |
| Sefaria alignment | `npm run validate:yoma` (pattern: `validate:<masechta>`) | he: matches live Sefaria | Any change to enrichment JSON, or periodically to catch upstream drift |
| English alignment | `npm run validate:en:<masechta>` | en: aligned to correct he: segment | Any change to enrichment JSON's line/ref mappings |
| Daftext provenance | `npm run validate:daftext:<masechta>` | daftexts match talmud.dev | Any change touching daftext generation, or as a regression check after any enrichment edit (should always pass unchanged if you only touched enrichment JSON) |
| Rashi structural integrity | `npm run validate:rashi:<masechta>` | he order/count, en+enSource present, no leak into Gemara | Any change to enrichment JSON (confirms rashiTranslations untouched) |
| Literal coverage | `npm run validate:literal:<masechta>` | en_lit coverage >= threshold | Any change to enrichment JSON or the literal layer |
| Order audit | `npm run audit:order:<masechta>` | Vilna sequence, no inversions | Any change to enrichment JSON |
| Production build | `npm run build` | esbuild bundle succeeds | Every commit that touches app code, module data, or docs affecting validation expectations |
| Deploy HTML safety | `npm run check:deploy-html` | no dev-only loaders in dist/index.html | Every commit that runs `npm run build` |
| Smoke test | `npm test` | build + render + manifest structure + minified runtime-guard strings | Every commit |
| Browser smoke test | `npm run test:browser` | Playwright specs against a live local server | Any commit touching app.jsx, module data, or CSS; recommended for every commit that isn't purely prose-doc-only |

For a docs-only pass with no code or data changes, `npm run build` and
`npm test` are sufficient; the Yoma-specific validators and browser test
are not required (there is nothing for them to check that changed).

---

## 11. Browser/Playwright workaround rules and required cleanup

Some sandboxed environments ship a pre-installed Chromium build whose
version does not match what the pinned `@playwright/test` version
expects, producing `browserType.launch: Executable doesn't exist at
.../chromium_headless_shell-<build>/...`. This is an environment issue,
not a code regression - confirm by checking `git diff` on
`package-lock.json`'s `@playwright/test` entry (if it's unchanged, the
mismatch predates your session).

Workaround, applied only for the duration of a single test run:

```bash
ls /opt/pw-browsers/          # confirm a working chromium build is present
```

Temporarily edit `playwright.config.js`'s chromium project to add:

```js
{ name: 'chromium', use: { ...devices['Desktop Chrome'], launchOptions: { executablePath: '/opt/pw-browsers/chromium' } } },
```

Run `npm run test:browser`, then **immediately revert** the edit back to:

```js
{ name: 'chromium', use: { ...devices['Desktop Chrome'] } },
```

Confirm with `git diff playwright.config.js` that it is empty before
proceeding to commit anything. Never commit the `executablePath`
workaround - CI's own environment has the matching browser build and does
not need it; committing the override risks masking a real CI browser
mismatch instead of using the workaround only where actually needed.

---

## 12. CI/deploy troubleshooting, especially Pages deploy collisions

Two workflows run on every push to `main`: `.github/workflows/
deploy-pages.yml` (build, verify, test, deploy to GitHub Pages) and
`.github/workflows/deploy-cloudways.yml` (build, force-push `dist/` output
to a `cloudways` branch). Both are independent; a failure in one does not
block the other.

`deploy-pages.yml` uses `concurrency: group: pages, cancel-in-progress:
true` at the workflow level, and its deploy job additionally cancels any
stale in-flight/queued/pending Pages deployments before deploying. This
means pushing a second commit while a Pages deploy from a prior commit is
still running is safe - the newer push takes priority and stale
deployments are marked inactive rather than left racing.

To check status (no `gh` CLI available; use the GitHub MCP server tools):

```
mcp__github__actions_list, method=list_workflow_runs, owner=<owner>, repo=<repo>, workflow_runs_filter={"branch":"main"}
```

This call can return output large enough to exceed the tool's inline
token limit; when it does, the result is saved to a file and must be read
with a shell tool (Python `json.load` + slicing) rather than the Read
tool's line-based chunking, since GitHub API JSON is typically one long
line. Filter to the first handful of entries and check `head_sha`,
`status`, and `conclusion` for the commit you just pushed.

Typical timing observed: Cloudways deploy completes in well under a
minute; GitHub Pages deploy (build + verify + smoke + browser test +
actual Pages deploy) takes roughly 4-5 minutes. Do not conclude a Pages
deploy failed just because it is still `in_progress` a minute after push -
wait for the full window before treating a non-`completed` status as a
problem.

No `gh` CLI and no direct GitHub API access are available in this
environment outside the MCP server tools - do not attempt to shell out to
`gh` or raw `curl` against the GitHub API for repo operations.

---

## 13. Stale container/local reset recovery

The local working tree in a remote/sandboxed session can silently reset
to an earlier state between turns (observed multiple times during the
Yoma review: local `HEAD` reverted to a commit many pushes behind, with
`VERSION` and all uncommitted edits reverted to match). This is a
container/session artifact, not a git problem, and it is not detectable
except by checking.

**Do not trust local git state at the start of any turn that involves
committing or continuing prior work.** Always reconcile first:

```bash
git fetch origin main --prune
git checkout main
git reset --hard origin/main
cat VERSION
git status --short
git log --oneline -5
```

Compare the resulting `HEAD` and `VERSION` against what you expect from
the most recent commit you made or were told about. If they match,
proceed. If `HEAD` is behind the expected commit, the container reset -
any uncommitted work from before the reset is gone and must be redone
from scratch. If you have a clear written record of exactly what that
work was (a chat-log description, or better, the review doc entries
themselves), redoing it is mechanical and fast; without one, it requires
re-deriving the fix.

**Practical mitigations:**

- Commit and push in small, frequent increments rather than batching a
  large amount of uncommitted work across many tool calls. The smaller
  the uncommitted window, the less is at risk from a reset.
- Keep the review/tracking doc (Sections 6-7) updated with enough detail
  (exact field names, exact replacement text, exact source citations)
  that a lost uncommitted change can be reconstructed from the doc alone
  without re-deriving the analysis.
- After any suspected reset, re-verify the full chain: `git log`,
  `VERSION`, and `git status --short`, before assuming any file's content
  matches what you last edited.

---

## 14. Commit/push approval protocol

Never commit or push without an explicit go-ahead for that specific
change, even if a prior turn approved a similar change. Each pass:

1. Make the edits, run required validators/build/test, and report a full
   summary: diff stat, exact fields/files changed, validation results,
   current `VERSION`.
2. Wait. Do not commit in the same turn as the report unless explicitly
   told to proceed.
3. When approved, confirm the staged file list matches exactly what was
   specified (no more, no fewer files) before running `git commit`.
4. After pushing, confirm the commit SHA, `VERSION`, and CI/deploy status
   (Section 12), and report all four explicitly.
5. Stay within the approved scope. If a pass surfaces additional issues
   beyond what was authorized (like the residual `resolution`/
   `learningBlocker` inconsistency found after an initial 9b/s02 fix in
   the Yoma review), report the finding and ask before expanding scope,
   rather than fixing it inline.

A repo-level `stop-hook-git-check.sh` may fire on uncommitted changes at
the end of a turn. That hook is a reminder, not an authorization - it
does not substitute for the user's explicit "proceed" on a specific pass.

---

## 15. Exact files that should and should not be edited

Generalizing `CLAUDE.md`'s "Do not do these things" for any module:

**Never edit directly (regenerate or re-fetch instead):**

- `modules/<masechta>/learning_data.js` - generated; rebuild via
  `build_learning_data.py`.
- `modules/<masechta>/assets/daftexts/*.txt` - generated; regenerate via
  the daftext pipeline.
- `modules/<masechta>/source_store.js` - verbatim Sefaria source; re-fetch
  if wrong, never hand-correct.
- `modules/<masechta>/assets/talmuddev/*.json` - verbatim talmud.dev
  cache; re-fetch if wrong.

**Editable only within the enrichment/documentation layer:**

- `modules/<masechta>/assets/learning/<masechta>/<daf>.learning.json` -
  the enrichment source. This is the one place ongoing content edits
  belong. Never touch the `rashiTranslations` array inside these files
  outside a dedicated, explicitly-authorized Rashi pass, even when other
  fields in the same file are in scope.
- `docs/*.md`, `CLAUDE.md`, module `MODULE.md` files - documentation, edit
  freely within the scope of the current task.

**Never bypass:**

- The pre-commit hook (`--no-verify` is forbidden).
- The `dataScript` allowlist pattern in `manifest.js`/`app.jsx` (build-
  time and runtime guards both enforce `modules/<id>/learning_data.js`
  with a lowercase alphanumeric id; do not restructure module paths to
  work around this).

**Scope discipline:** a pass authorized to fix one sugya's fields should
touch only that sugya's named fields, not its neighbors, not its
`argumentFlow`, not fields not named in the authorization, even if they
look related. When a fix requires touching a field outside the current
authorization to be internally consistent, report the residual
inconsistency and ask, rather than silently expanding scope (see Section
14, point 5).

---

## 16. How to document unresolved source issues without guessing

When a contradiction, ambiguity, or missing-content issue cannot be
resolved within the current pass's authorized scope or available sources,
document it rather than guess. Never write a "fix" that asserts a
specific resolution not traceable to either local corpus content (cited
by file and line) or an external citation (cited by source, edition, and
URL, per Section 7 Tier 2).

**Decision tree: fix, defer, or document.**

```
Is the issue a clean crosswire (a field's content verbatim matches
a *different*, identifiable sugya's field, and that sugya's own
content is otherwise correct)?
  YES -> FIX. Replace only the wrong field(s) with content grounded in
         the current sugya's own argumentFlow/daftext. Low risk.
  NO  -> continue

Is the issue an internal contradiction where the sugya's own local
content (daftext, argumentFlow, misconceptions, finalRuling) already
states an answer, or where a corpus-wide search finds corroborating
content elsewhere in the local corpus?
  YES -> FIX. Cite the resolving local content explicitly in the
         fix's commit and doc entry.
  NO  -> continue

Is authoritative external source review available and authorized for
this pass (Section 7 Tier 2)?
  YES -> Fetch it, confirm the Hebrew matches the local passage,
         then FIX with the sourced resolution, citing source/edition/URL.
  NO  -> DEFER. Write a doc entry (see format below) and stop. Do not
         guess, and do not treat outside training-data memory as a
         citable source.

Is the issue a near-duplicate (two sugyot genuinely differ in topic
per their own argumentFlow, but share templated scaffolding fields)
rather than a clean crosswire?
  -> DOCUMENT as "requires new authored content." This needs judgment
     about what new content to write, which is a separate authorization
     decision from a mechanical field-swap fix.
```

**Deferred/documented entry format** (see
`docs/yoma-perek-review.md` for worked examples):

```text
**[STATUS] - <sugya-id> (<one-line description>):**
<What the contradiction/issue is, quoting the actual conflicting field
values.>
<What was checked and where: exact files, exact line ranges, exact
search terms tried, exact results.>
<Why it remains unresolved: what would be needed to resolve it - a
specific external source, a specific broader Mishnah/Gemara passage,
human judgment about which authored angle to take.>
<Explicit statement that no fix was applied, or exactly what fix was
applied and to which fields only.>
```

When a deferred issue is later resolved, do not just delete the old
entry - replace it with a "RESOLVED" entry that preserves the original
investigation (or a pointer to it in git history) plus the new source
basis, so the audit trail of what was checked and when remains legible.

---

## Pre-commit checklist

- [ ] Enrichment JSON changes grounded only in that sugya's own
      argumentFlow/daftext (or an explicitly cited external source)
- [ ] Only the specifically authorized fields changed - diff the file and
      check
- [ ] `rashiTranslations` untouched (grep the diff for it; expect zero
      hits unless this is an authorized Rashi pass)
- [ ] `modules/<masechta>/learning_data.js` regenerated, never hand-edited
- [ ] Literal layer reinjected if the enrichment JSON changed
      (`build_literal_layer.py`)
- [ ] `VERSION` bumped and `sync_version.py` run
- [ ] All required validation gates green (Section 10)
- [ ] `npm run build` and `npm test` pass
- [ ] `npm run test:browser` passes if app code, module data, or CSS
      changed
- [ ] `playwright.config.js` diff is empty (Section 11)
- [ ] No em dashes or en dashes in any project-authored text
- [ ] Staged file list matches exactly what was authorized, no more, no
      fewer

## Post-push checklist

- [ ] Commit SHA reported
- [ ] `VERSION` reported and matches what was bumped to
- [ ] GitHub Pages deploy status confirmed (Section 12) - wait the full
      ~5 minute window before treating `in_progress` as a problem
- [ ] Cloudways deploy status confirmed
- [ ] Changed-file list reported and matches exactly what was staged
- [ ] Any explicit "do not start X yet" boundary from the current
      authorization restated as still in force
