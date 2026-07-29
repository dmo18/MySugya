# Legacy Rashi renderer: retirement policy

Status: **the legacy renderer is retained. It is not scheduled for deletion,
and nothing in this policy authorizes deleting it.**

Since the VERSION 15.338 cutover (`ef58878`), the linked
`linkedGemaraLineIds` renderer is the production default. The legacy
vilnaLine-coincidence renderer remains fully intact in `app.jsx` and is
reachable only through the explicit override `?rashiAssoc=legacy`. This
document defines what would have to be true before anyone proposes removing
it, so the decision is never made implicitly or by a worker.

## What is being retained

- The legacy branch in `app.jsx` (`legacyRashi` / `!useLinked` paths).
- The `?rashiAssoc=legacy` selector arm in `rashiRendererFromUrl`
  (`shared/rashi_association.js`).
- The browser test that proves legacy still renders
  (`tests/browser/rashi-association.spec.js`, "Rashi renderer selection"
  describe block).

None of these may be removed, weakened, or made conditional by routine work.

## Observation period

A minimum of **90 days of linked-default production service on GitHub
Pages**, starting from the VERSION 15.338 deployment. The clock restarts if
any linked-rendering defect is found and repaired during the window.

## Evidence required before retirement may be proposed

All of the following, gathered at a single commit:

1. Renderer readiness **8/8** with a fresh, machine-verified sharded browser
   artifact at that exact commit (`ci=true`, 173/173 daf, zero failed).
2. Exhaustive association audit clean: **0 broken, 0 cross-daf**.
3. Boundary authorization registry valid, ratchet unchanged at 20/20.
4. Semantic audit showing **0 actionable** daf (no SHIFTED, no
   FABRICATION-SUSPECT, no recommended task type).
5. Rashi translation-quality coverage complete: every daf classified
   audited-clean, audited-advisory, or repaired-and-verified.
6. **Zero rollback invocations that were needed.** Any use of
   `?rashiAssoc=legacy` to work around a linked-rendering defect during the
   observation window resets the period and blocks retirement.
7. No open item in `docs/reports/open-items.md` classified
   OPEN-ACTIONABLE against the renderer or association layer.

## Rollback conditions (while the legacy path exists)

Roll back to legacy immediately, without waiting for approval, if production
linked rendering shows any of:

- a Rashi comment rendering beneath a line it does not declare;
- a declared association failing to render at all;
- an authorized boundary entry rendering anywhere;
- Hebrew paired with another entry's English;
- console errors or asset failures traceable to the renderer.

Rollback procedure, in increasing order of blast radius:

1. **Per-user, no deploy:** append `?rashiAssoc=legacy` to the URL.
2. **Site-wide, minimum revert:** change the single default in
   `rashiRendererFromUrl` back to `legacy`, bump VERSION, ship through the
   normal PR/CI/deploy path. This is a one-line change by design.
3. Preserve all evidence (artifact ids, workflow runs, failing daf and line
   ids) in `docs/reports/open-items.md` before or alongside the revert.

## Approval required to delete

Deleting the legacy path requires **explicit operator approval**, recorded in
writing, after the evidence above is presented. It is a deliberate product
decision, not a cleanup task.

A worker, agent, or automated process must **never**:

- delete the legacy branch or the `legacy` selector arm;
- remove or weaken the renderer-selection tests;
- treat "the legacy path is unused" as sufficient justification;
- bundle legacy removal into an unrelated PR.

If deletion is ever approved, it must be its own narrowly scoped PR that
removes the legacy branch, its selector arm, and its tests together, updates
this policy to closed, and records the approving decision.
