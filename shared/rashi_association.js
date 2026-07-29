/* ============================================
   Rashi linked-association helper
   ============================================
   Pure function shared between app.jsx (browser, plain global-scope script)
   and tests/unit/rashi-association.test.mjs (Node, via the CommonJS export
   guard below). This is the single source of truth: neither consumer may
   re-implement or copy it, so the two can never drift.

   groupRashiByLinkedId groups rashiLines entries by the Gemara/Mishnah line
   ids they declare in linkedGemaraLineIds. This is the authoritative and
   ONLY association mechanism - it does NOT fall back to vilnaLine
   coincidence. An entry with an empty linkedGemaraLineIds array is an
   authorized daf-boundary truncation (see
   modules/yoma/scripts/allowlists/rashi_boundary_authorizations.json) and
   is intentionally never attached to any line, so it never renders beneath
   an unrelated line.

   The legacy vilnaLine-coincidence renderer and the ?rashiAssoc selector
   were removed at VERSION 15.346. There is no renderer selection and no
   rollback path: every URL, with or without a rashiAssoc parameter of any
   value, renders from linkedGemaraLineIds.
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

/* CommonJS export for Node tooling; harmless as a plain browser script. */
if (typeof module !== "undefined" && module.exports) {
  module.exports = { groupRashiByLinkedId };
}
