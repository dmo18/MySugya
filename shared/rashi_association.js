/* ============================================
   Rashi linked-association helpers
   ============================================
   Pure functions shared between app.jsx (browser, plain global-scope script)
   and tests/unit/rashi-association.test.mjs (Node, via the CommonJS export
   guard below). This is the single source of truth: neither consumer may
   re-implement or copy these functions, so the two can never drift.

   groupRashiByLinkedId groups rashiLines entries by the Gemara/Mishnah line
   ids they declare in linkedGemaraLineIds. This is the authoritative
   association - it does NOT fall back to vilnaLine coincidence. An entry
   with an empty linkedGemaraLineIds array is a boundary case (an authorized
   daf-boundary truncation, see
   modules/yoma/scripts/allowlists/rashi_boundary_authorizations.json) and
   is intentionally never attached to any line, so it never renders beneath
   an unrelated line.

   rashiRendererFromUrl selects the renderer. As of the VERSION 15.338
   cutover, LINKED IS THE PRODUCTION DEFAULT: an ordinary URL with no
   rashiAssoc parameter renders via linkedGemaraLineIds.

     (no parameter)         -> "linked"  (production default)
     ?rashiAssoc=linked     -> "linked"  (still accepted, no longer required)
     ?rashiAssoc=legacy     -> "legacy"  (temporary rollback override)
     any other/malformed    -> "linked"  (never silently falls back to legacy)

   Only the exact string "legacy" selects the legacy vilnaLine-coincidence
   renderer. That renderer has NOT been deleted: it remains fully intact in
   app.jsx as a rollback path, reachable solely through this explicit
   override.

   The value is read fresh from the URL on every call and is never cached
   and never persisted to localStorage or any other storage, so the renderer
   can never be pinned by a stored user preference and never leaks across
   navigations.
*/
function groupRashiByLinkedId(rashiLines) {
  const map = new Map();
  (rashiLines || []).forEach(r => {
    (r.linkedGemaraLineIds || []).forEach(lineId => {
      if (!map.has(lineId)) map.set(lineId, []);
      map.get(lineId).push(r);
    });
  });
  return map;
}

function rashiRendererFromUrl() {
  // No URL to read (non-browser context): the production default applies.
  if (typeof window === "undefined" || !window.location) return "linked";
  const qp = new URLSearchParams(window.location.search);
  // Only the exact opt-out string selects legacy; everything else, including
  // an absent, unknown, or malformed value, gets the linked default.
  return qp.get("rashiAssoc") === "legacy" ? "legacy" : "linked";
}

/* CommonJS export for Node tooling; harmless as a plain browser script. */
if (typeof module !== "undefined" && module.exports) {
  module.exports = { groupRashiByLinkedId, rashiRendererFromUrl };
}
