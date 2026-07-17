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
   with an empty linkedGemaraLineIds array is a boundary case (not yet
   linked) and is never attached to any line.

   rashiRendererFromUrl reads the test-only ?rashiAssoc=linked query
   parameter. It is read fresh on every call (never cached, never persisted
   to localStorage) so the linked renderer can only ever be reached by
   explicit URL, never by a stored user preference. Legacy (vilnaLine
   coincidence) remains the production default.
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
  if (typeof window === "undefined" || !window.location) return "legacy";
  const qp = new URLSearchParams(window.location.search);
  return qp.get("rashiAssoc") === "linked" ? "linked" : "legacy";
}

/* CommonJS export for Node tooling; harmless as a plain browser script. */
if (typeof module !== "undefined" && module.exports) {
  module.exports = { groupRashiByLinkedId, rashiRendererFromUrl };
}
