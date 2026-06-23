/* ============================================
   My Sugya — React Components
   ============================================ */

const { useState, useEffect, useMemo, useRef, useCallback } = React;

// ----- localStorage helpers -----------------------------------------------
const LS = {
  get(key, fallback) {
    try { const v = localStorage.getItem(key); return v == null ? fallback : JSON.parse(v); }
    catch { return fallback; }
  },
  set(key, val) {
    try { localStorage.setItem(key, JSON.stringify(val)); } catch {}
  },
};

// ----- utilities -----------------------------------------------------------
function tractatePerek(dafId) {
  const entry = DAF_INDEX.find(d => d.id === dafId);
  return entry ? PERAKIM.find(p => p.n === entry.perek) : PERAKIM[0];
}
function dafEntry(dafId) { return DAF_INDEX.find(d => d.id === dafId); }
function dafIdx(dafId)   { return DAF_INDEX.findIndex(d => d.id === dafId); }

function hebrewNum(n) {
  const ones = ["", "א", "ב", "ג", "ד", "ה", "ו", "ז", "ח", "ט"];
  const tens = ["", "י", "כ", "ל", "מ", "נ", "ס", "ע", "פ", "צ"];
  if (n === 15) return "טו";
  if (n === 16) return "טז";
  return (tens[Math.floor(n / 10)] || "") + (ones[n % 10] || "");
}

function hebrewizeDaf(id) {
  const m = id.match(/^(\d+)([ab])$/);
  if (!m) return id;
  const amud = m[2] === "a" ? "עמוד א" : "עמוד ב";
  return `${hebrewNum(parseInt(m[1], 10))} ${amud}`;
}

// Gemara-style: טו. (amud a) or טו: (amud b)
function gemaraId(id) {
  const m = id.match(/^(\d+)([ab])$/);
  if (!m) return id;
  return hebrewNum(parseInt(m[1], 10)) + (m[2] === "a" ? "." : ":");
}

// =============================================================================
// ICONS — small inline set
// =============================================================================
const Icons = {
  Search: () => <span aria-hidden="true">⌕</span>,
  Bookmark: () => <span aria-hidden="true">☆</span>,
  BookmarkFilled: () => <span aria-hidden="true">★</span>,
  Check: () => <span aria-hidden="true">✓</span>,
  Arrow: ({ dir = "right" }) => <span aria-hidden="true">{dir === "left" ? "←" : "→"}</span>,
  Settings: () => <span aria-hidden="true">⚙</span>,
};

// =============================================================================
// VILNA POSITION FEATURES
// =============================================================================

function AmudGauge({ pct }) {
  return (
    <div className="amud-gauge" aria-hidden="true">
      <div className="amud-gauge-fill" style={{ width: `${Math.min(100, pct * 100)}%` }}/>
    </div>
  );
}

function SugyaTimeline({ sugyot, currentIdx }) {
  if (!sugyot?.length) return null;
  return (
    <nav className="sugya-timeline" aria-label="Sugya navigation">
      {sugyot.map((s, i) => {
        const vl = (s.lines || []).find(l => l?.vilna_line != null)?.vilna_line;
        return (
          <button
            key={s.id}
            className={"tl-btn" + (i === currentIdx ? " is-active" : "")}
            onClick={() => document.getElementById(s.id)?.scrollIntoView({ behavior: "smooth" })}
            title={s.title}
          >
            {vl != null && <span className="tl-vl">L{vl}</span>}
            <span className="tl-label">{s.title?.split(":")[0] ?? s.title}</span>
          </button>
        );
      })}
    </nav>
  );
}

function SugyaPipDots({ sugyot, currentIdx }) {
  if (!sugyot?.length) return null;
  return (
    <div className="pip-dots" aria-hidden="true">
      {sugyot.map((s, i) => (
        <button
          key={s.id}
          className={"pip-dot" + (i <= currentIdx ? " reached" : "") + (i === currentIdx ? " current" : "")}
          onClick={() => document.getElementById(s.id)?.scrollIntoView({ behavior: "smooth" })}
          title={s.title}
        />
      ))}
    </div>
  );
}

function BottomDock({ sugyot, currentIdx }) {
  if (!sugyot?.length) return null;
  return (
    <nav className="bottom-dock" aria-label="Sugya navigation">
      {sugyot.map((s, i) => (
        <button
          key={s.id}
          className={"dock-btn" + (i === currentIdx ? " is-active" : "")}
          onClick={() => document.getElementById(s.id)?.scrollIntoView({ behavior: "smooth" })}
          title={s.title}
        >
          <span className="dock-num">{i + 1}</span>
          <span className="dock-label">{s.title?.split(":")[0] ?? s.title}</span>
        </button>
      ))}
    </nav>
  );
}

// =============================================================================
// LINE TAGS — labels for question / answer / etc
// =============================================================================
const LINE_TAGS = {
  question:   { en: "Question",   he: "שְׁאֵלָה" },
  answer:     { en: "Answer",     he: "תְּשׁוּבָה" },
  objection:  { en: "Objection",  he: "קוּשְׁיָא" },
  proof:      { en: "Proof",      he: "רְאָיָה" },
  conclusion: { en: "Conclusion", he: "מַסְקָנָא" },
  mishnah:    { en: "Mishnah",    he: "מִשְׁנָה" },
  aside:      { en: "Aside",      he: "אַגַּב" },
};

// =============================================================================
// CHROME — top bar with daf navigator & actions
// =============================================================================
function Chrome({ daf, perek, hasPrev, hasNext, onPrev, onNext, isBookmarked, onBookmark, onJump, onTweaks, scrollPct, showGaugeBar }) {
  return (
    <header className="chrome">
      <div className="chrome-inner">

        <div className="brand">
          <div className="brand-mark">ס</div>
          <span className="brand-name">My Sugya</span>
        </div>

        <div className="chrome-location">
          <button className="chrome-nav-arrow" disabled={!hasPrev} onClick={onPrev} aria-label="Previous daf">
            <Icons.Arrow dir="left"/>
          </button>
          <button className="chrome-daf" onClick={onJump} title="Pick a daf (⌘K)">
            <div className="chrome-daf-id">
              <span>{daf}</span>
              <span className="chrome-daf-he" lang="he" dir="rtl">{gemaraId(daf)}</span>
            </div>
            <span className="chrome-perek-name">Perek {perek.n} · {perek.name_en}</span>
          </button>
          <button className="chrome-nav-arrow" disabled={!hasNext} onClick={onNext} aria-label="Next daf">
            <Icons.Arrow dir="right"/>
          </button>
        </div>

        <div className="chrome-actions">
          <button
            className={"icon-btn " + (isBookmarked ? "is-active" : "")}
            onClick={onBookmark}
            title={isBookmarked ? "Remove bookmark" : "Bookmark this daf"}
          >
            {isBookmarked ? <Icons.BookmarkFilled/> : <Icons.Bookmark/>}
          </button>
          <button className="icon-btn" onClick={onTweaks} title="Open Tweaks">
            <Icons.Settings/>
          </button>
        </div>

      </div>
      {showGaugeBar && <AmudGauge pct={scrollPct}/>}
    </header>
  );
}

// =============================================================================
// PROGRESS RAIL — all amudim, current/bookmarked/completed/rich
// =============================================================================
function ProgressRail({ currentDaf, bookmarks, completed, onSelect }) {
  const currentPerek = tractatePerek(currentDaf);
  return (
    <div className="progress-rail">
      <div className="progress-rail-inner">
        <div className="rail-cells">
          {DAF_INDEX.map(d => {
            const isActive = d.id === currentDaf;
            const isBm = bookmarks.includes(d.id);
            const isDone = completed.includes(d.id);
            const isRich = d.status === "rich";
            const cls = [
              "rail-cell",
              isActive && "is-active",
              isBm && "is-bookmarked",
              isDone && "is-completed",
              isRich && "is-rich",
            ].filter(Boolean).join(" ");
            return (
              <button key={d.id} className={cls} onClick={() => onSelect(d.id)}>
                <span className="rail-tip">{d.id}{isRich ? " · rich" : ""}</span>
              </button>
            );
          })}
        </div>
      </div>
    </div>
  );
}

// =============================================================================
// DAF HEAD
// =============================================================================
function DafHead({ daf, perek, summary, isBookmarked, onBookmark, isCompleted, onComplete }) {
  return (
    <header className="daf-head">
      <div>
        <p className="daf-eyebrow">
          <span className="dot"/>
          Tractate {TRACTATE_META.title} · Perek {perek.n} · {perek.name_en}
        </p>
        <div className="daf-title-row">
          <h1 className="daf-title-he">{hebrewizeDaf(daf)}</h1>
          <h2 className="daf-title-en">{TRACTATE_META.title} {daf}</h2>
        </div>
        {summary && <p className="daf-summary">{summary}</p>}
      </div>
      <div className="daf-meta">
        <button className={"daf-meta-pill" + (isBookmarked ? " is-bookmarked" : "")} onClick={onBookmark}>
          {isBookmarked ? <Icons.BookmarkFilled/> : <Icons.Bookmark/>}
          {isBookmarked ? "Bookmarked" : "Bookmark"}
        </button>
        <button className={"daf-meta-pill" + (isCompleted ? " is-bookmarked" : "")} onClick={onComplete}>
          <Icons.Check/>
          {isCompleted ? "Completed" : "Mark complete"}
        </button>
      </div>
    </header>
  );
}

// =============================================================================
// LINE — Hebrew + elucidated English (literal portions bolded per WD convention)
// =============================================================================
function Line({ line, idx, showNekudot, showVilnaLines, showEnglish, boldLiteral }) {
  const tag = LINE_TAGS[line.kind] || LINE_TAGS.aside;
  const heRaw = stripHtml(line.he);
  const heText = showNekudot ? heRaw : stripNekudot(heRaw);
  const hasVilna = line.vilna_line != null;
  return (
    <div className="line" data-kind={line.kind}>
      <span className="line-marker" aria-hidden="true"/>
      <div className="line-tag">
        <span>{tag.en}</span>
        <span className="tag-he">{tag.he}</span>
      </div>
      {hasVilna ? (
        <div className="line-he" lang="he" dir="rtl">
          {heText.split("\n").map((row, i) => (
            <div key={i} className="vilna-row">
              <span className="vilna-row-text">{row}</span>
              {showVilnaLines && (
                <span className="vilna-row-num" title="Vilna column line">{line.vilna_line + i}</span>
              )}
            </div>
          ))}
        </div>
      ) : (
        <p className="line-he" lang="he" dir="rtl">{heText}</p>
      )}
      {showEnglish !== false && (
        <p className="line-en">
          <span dangerouslySetInnerHTML={{__html: boldLiteral !== false ? enHtml(line.en) : enHtml(line.en).replace(/<\/?b>/g, "")}}/>
          {line.flag && (
            <span className="src-flag" title={line.flag}>
              ⚠ Sources differ
            </span>
          )}
        </p>
      )}
    </div>
  );
}

function stripNekudot(s) {
  if (!s) return s;
  return s.replace(/[\u0591-\u05C7]/g, "");
}

function stripHtml(s) {
  if (!s) return s;
  return s.replace(/<[^>]+>/g, "");
}

// =============================================================================
// SEFARIA REFERENCE LINKER
// =============================================================================
const BOOK_MAP = {
  // Torah
  "Genesis": "Genesis", "Gen.": "Genesis",
  "Exodus": "Exodus", "Ex.": "Exodus", "Exod.": "Exodus",
  "Leviticus": "Leviticus", "Lev.": "Leviticus",
  "Numbers": "Numbers", "Num.": "Numbers",
  "Deuteronomy": "Deuteronomy", "Deut.": "Deuteronomy",
  // Nevi'im
  "Joshua": "Joshua", "Judges": "Judges",
  "I Samuel": "I_Samuel", "II Samuel": "II_Samuel",
  "I Kings": "I_Kings", "II Kings": "II_Kings",
  "Isaiah": "Isaiah", "Jeremiah": "Jeremiah", "Ezekiel": "Ezekiel",
  "Hosea": "Hosea", "Joel": "Joel", "Amos": "Amos",
  "Obadiah": "Obadiah", "Jonah": "Jonah", "Micah": "Micah",
  "Nahum": "Nahum", "Habakkuk": "Habakkuk", "Zephaniah": "Zephaniah",
  "Haggai": "Haggai", "Zechariah": "Zechariah", "Malachi": "Malachi",
  // Ketuvim
  "Psalms": "Psalms", "Ps.": "Psalms",
  "Proverbs": "Proverbs", "Prov.": "Proverbs",
  "Job": "Job",
  "Song of Songs": "Song_of_Songs",
  "Ruth": "Ruth",
  "Lamentations": "Lamentations", "Lam.": "Lamentations",
  "Ecclesiastes": "Ecclesiastes", "Eccl.": "Ecclesiastes",
  "Esther": "Esther", "Daniel": "Daniel",
  "Ezra": "Ezra", "Nehemiah": "Nehemiah",
  "I Chronicles": "I_Chronicles", "II Chronicles": "II_Chronicles",
};

// Sort longest-first so multi-word names match before their prefixes
const _bookKeys = Object.keys(BOOK_MAP).sort((a, b) => b.length - a.length);
const _reStr = `(${_bookKeys.map(k => k.replace(/[.*+?^${}()|[\]\\]/g, "\\$&")).join("|")})\\s+(\\d+):(\\d+)`;
const BOOK_RE = new RegExp(_reStr, "g");

function linkifyEn(raw) {
  if (!raw) return "";
  // Split on HTML tags; keep <b>, <i>, <em>, <strong> (normalize strong->b);
  // linkify Bible refs in text nodes; strip all other tags.
  const parts = raw.split(/(<[^>]+>)/);
  let result = "";
  for (const part of parts) {
    if (part.startsWith("<")) {
      if (/^<\/?(b|i|em)\b/i.test(part)) { result += part; continue; }
      if (/^<strong\b/i.test(part))       { result += "<b>"; continue; }
      if (/^<\/strong>/i.test(part))      { result += "</b>"; continue; }
      // strip other tags
    } else {
      BOOK_RE.lastIndex = 0;
      let last = 0, m;
      while ((m = BOOK_RE.exec(part)) !== null) {
        result += escHtml(part.slice(last, m.index));
        const url = `https://www.sefaria.org/${BOOK_MAP[m[1]]}.${m[2]}.${m[3]}`;
        result += `<a href="${url}" target="_blank" rel="noreferrer">${escHtml(m[0])}</a>`;
        last = m.index + m[0].length;
      }
      result += escHtml(part.slice(last));
    }
  }
  return result;
}

function escHtml(s) {
  return s.replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;");
}

// Pre-process all en: fields once at startup into a Map<raw, linkedHtml>
// Initialized in s.onload after learning_data.js is available.
let EN_CACHE = null;
function initEnCache() {
  EN_CACHE = new Map();
  const addStr = s => { if (s && !EN_CACHE.has(s)) EN_CACHE.set(s, linkifyEn(s)); };
  for (const daf of Object.values(DAF_CONTENT)) {
    for (const sugya of (daf.sugyot || [])) {
      if (sugya.nusach)  { addStr(sugya.nusach.ashkenaz); addStr(sugya.nusach.sephardic); }
      for (const line of (sugya.lines || [])) if (line) addStr(line.en);
    }
  }
}

function enHtml(s) { return EN_CACHE.get(s) ?? linkifyEn(s); }

// =============================================================================
// CHIP — collapsible section
// =============================================================================
function Chip({ open, onToggle, label, labelHe, children, kind, dh }) {
  return (
    <>
      <button className="chip" aria-expanded={open} onClick={onToggle}>
        <span>{label}</span>
        {labelHe && <span className="chip-he">{labelHe}</span>}
        <span aria-hidden="true" style={{transform: open ? "rotate(180deg)" : "none", transition: "transform 160ms", display:"inline-block"}}>⌄</span>
      </button>
      {open && (
        <div className="reveal" style={{flexBasis: "100%"}}>
          <div className="reveal-label">
            <span>{kind}</span>
            {dh && <span className="ref">{dh}</span>}
          </div>
          {children}
        </div>
      )}
    </>
  );
}

// =============================================================================
// SHARE BUTTON
// =============================================================================
function ShareButton({ sugya }) {
  const [copied, setCopied] = useState(false);
  const share = () => {
    const daf = sugya.daf || sugya.id.replace(/-\d+$/, "");
    const url = `${SITE_BASE}/index.html?module=${TRACTATE_META.id}&daf=${daf}#${sugya.id}`;
    if (navigator.share) {
      navigator.share({ title: sugya.title, url }).catch(() => {});
    } else {
      navigator.clipboard.writeText(url).then(() => {
        setCopied(true);
        setTimeout(() => setCopied(false), 2000);
      });
    }
  };
  return (
    <button className={"share-btn" + (copied ? " copied" : "")} onClick={share}
      title="Copy link to this sugya" aria-label="Share">
      {copied ? "✓ Copied" : "⇧ Share"}
    </button>
  );
}

// =============================================================================
// LEARNING LAYER COMPONENTS (v1.0 schema fields)
// =============================================================================
function ArgumentFlowPanel({ steps }) {
  if (!steps || !steps.length) return null;
  return (
    <div className="learn-panel learn-args">
      <span className="learn-label">Argument flow</span>
      <ol className="arg-steps">
        {steps.map(step => (
          <li key={step.id} className={"arg-step arg-step--" + step.type}>
            <span className="arg-type">{step.type}</span>
            {step.label && <strong className="arg-label">{step.label}</strong>}
            {step.speaker && <em className="arg-speaker">{step.speaker}</em>}
            <span className="arg-text">{step.text}</span>
          </li>
        ))}
      </ol>
    </div>
  );
}

function LearningPanel({ learning, display }) {
  const [open, setOpen] = useState(false);
  if (!learning) return null;
  const { learnerQuestion, coreTension, takeaway, ahaMoment } = learning;
  if (!learnerQuestion && !takeaway) return null;
  return (
    <div className="learn-panel learn-meta">
      {learnerQuestion && (
        <div className="learn-row">
          <span className="learn-label">Learner question</span>
          <p className="learn-q">{learnerQuestion}</p>
        </div>
      )}
      {coreTension && (
        <div className="learn-row">
          <span className="learn-label">Core tension</span>
          <p>{coreTension}</p>
        </div>
      )}
      {takeaway && takeaway.text && (
        <div className="learn-row learn-takeaway">
          <span className="learn-label">Takeaway</span>
          <p>{takeaway.text}</p>
        </div>
      )}
      {ahaMoment && (
        <div className="learn-row">
          <span className="learn-label">Aha moment</span>
          <p className="learn-aha">{ahaMoment}</p>
        </div>
      )}
    </div>
  );
}

// =============================================================================
// SUGYA
// =============================================================================
function Sugya({ sugya, idx, total, tweaks }) {
  const [nusachOpen, setNusachOpen] = useState(false);
  const [learnOpen, setLearnOpen]   = useState(false);

  const display  = sugya.display  || {};
  const learning = sugya.learning || null;
  const whats    = display.whats  || sugya.whats;
  const oneLine  = display.oneLine;
  const hint     = display.hint   || sugya.hint;
  const title    = display.title  || sugya.title;

  return (
    <article className="sugya" id={sugya.id}>
      <div className="sugya-body">
        <div className="sugya-num">
          <span className="num">{String(idx + 1).padStart(2, "0")}</span>
          <span>SUGYA · {idx + 1} of {total}</span>
          <ShareButton sugya={sugya} />
        </div>
        <h3 className="sugya-title">{title}</h3>
        {sugya.title_he && <p className="sugya-title-he" dir="rtl">{sugya.title_he}</p>}

        {oneLine && <p className="sugya-one-line">{oneLine}</p>}

        {whats && (
          <div className="sugya-whats">
            <span className="label">What's happening</span>
            <p>{whats}</p>
          </div>
        )}

        {learning && (
          <LearningPanel learning={learning} display={display} />
        )}

        <div className="lines">
          {sugya.lines.filter(Boolean).map((line, i) => (
            <Line key={i} line={line} idx={i}
              showNekudot={tweaks.nekudot}
              showVilnaLines={tweaks.vilnaLines}
              showEnglish={tweaks.showEnglish}
              boldLiteral={tweaks.boldLiteral}
            />
          ))}
        </div>

        {sugya.argumentFlow && sugya.argumentFlow.length > 0 && (
          <ArgumentFlowPanel steps={sugya.argumentFlow} />
        )}


        <div className="chips">
          {sugya.image && (
            <div className="sugya-image">
              <img
                src={`assets/generated-images/${sugya.image}`}
                alt={sugya.image_alt || title}
                className="sugya-infographic"
                loading="lazy"
              />
            </div>
          )}
          {hint && (
            <Chip
              open={learnOpen}
              onToggle={() => setLearnOpen(v => !v)}
              label="Hint" labelHe="רֶמֶז"
              kind="hint"
            >
              <p>{hint}</p>
            </Chip>
          )}
          {sugya.nusach && sugya.nusach[tweaks.nusach] && (
            <Chip
              open={nusachOpen}
              onToggle={() => setNusachOpen(v => !v)}
              label="Nusach" labelHe="נוּסָח"
              kind="Nusach"
            >
              <p className="nusach-tradition">{tweaks.nusach === "sephardic" ? "Sephardic" : "Ashkenaz"}</p>
              <p>{sugya.nusach[tweaks.nusach]}</p>
            </Chip>
          )}
        </div>
      </div>

    </article>
  );
}

// =============================================================================
// RASHI PANEL
// =============================================================================
function RashiPanel({ lines, showNekudot }) {
  const [open, setOpen] = useState(false);
  const [showEn, setShowEn] = useState(true);
  if (!lines || !lines.length) return null;
  const hasEn = lines.some(r => r.en);
  return (
    <section className="rashi-panel">
      <button
        className="rashi-toggle"
        onClick={() => setOpen(v => !v)}
        aria-expanded={open}
      >
        <span className="rashi-toggle-he" lang="he" dir="rtl">רַשִׁ&quot;י</span>
        <span className="rashi-toggle-label">Rashi on this daf</span>
        <span className="rashi-toggle-count">{lines.length} lines (Vilna)</span>
        <span className="rashi-toggle-arrow" aria-hidden="true">{open ? "▲" : "▼"}</span>
      </button>
      {open && (
        <div className="rashi-body">
          {hasEn && (
            <div className="rashi-controls">
              <label className="rashi-en-toggle">
                <input
                  type="checkbox"
                  checked={showEn}
                  onChange={() => setShowEn(v => !v)}
                />
                Show English helper translation
              </label>
              <span className="rashi-helper-note">
                English is an editorial helper translation, not source-validated.
              </span>
            </div>
          )}
          <ol className="rashi-lines">
            {lines.map((r, i) => {
              const he = showNekudot ? r.he : stripNekudot(r.he);
              return (
                <li key={r.id || i} className="rashi-row">
                  <span className="rashi-vl" aria-hidden="true">{r.vilnaLine}</span>
                  <div className="rashi-pair">
                    <p className="rashi-he" lang="he" dir="rtl">{he}</p>
                    {showEn && r.en && (
                      <p className="rashi-en">
                        <span dangerouslySetInnerHTML={{__html: enHtml(r.en)}}/>
                      </p>
                    )}
                  </div>
                </li>
              );
            })}
          </ol>
        </div>
      )}
    </section>
  );
}

// =============================================================================
// GLOSSARY
// =============================================================================
function Glossary({ items }) {
  if (!items || !items.length) return null;
  return (
    <section className="glossary">
      <div className="glossary-head">
        <h2><span className="he">מִלָּשׁוֹן</span> Glossary for this daf</h2>
      </div>
      <div className="glossary-grid">
        {items.map((g, i) => (
          <div key={i} className="glossary-item">
            <p className="gi-he" dir="rtl">{g.he}</p>
            <p className="gi-translit">{g.translit}</p>
            <p className="gi-en">{stripHtml(g.en)}</p>
          </div>
        ))}
      </div>
    </section>
  );
}

// =============================================================================
// PLACEHOLDER DAF VIEW
// =============================================================================
// =============================================================================
// VILNA TITLE PAGES — 1a (front) and 1b (chapter list)
// =============================================================================
function VilnaTitlePage() {
  return (
    <div className="vilna-page" lang="he" dir="rtl">
      <div className="vilna-frame">
        <div className="vilna-frame-inner">
          <p className="vilna-top-band">תַּלְמוּד בַּבְלִי</p>
          <p className="vilna-sub">עִם כׇּל הַמְּפָרְשִׁים</p>
          <div className="vilna-rule"/>
          <p className="vilna-label">מַסֶּכֶת</p>
          <p className="vilna-name">יוֹמָא</p>
          <p className="vilna-seder">מִסֵּדֶר מוֹעֵד</p>
          <div className="vilna-rule"/>
          <div className="vilna-body">
            <p>יֵשׁ בָּהּ שְׁמוֹנָה פְּרָקִים וּפ״ח דַּפִּים</p>
            <p>מְדַבֶּרֶת מֵעִנְיְנֵי יוֹם הַכִּפּוּרִים</p>
            <p>וְסֵדֶר הָעֲבוֹדָה שֶׁהָיָה הַכֹּהֵן הַגָּדוֹל עוֹשֶׂה בּוֹ</p>
          </div>
          <div className="vilna-ornament">✦</div>
          <div className="vilna-imprint">
            <p>נִדְפַּס פֹּה וִוילְנָא</p>
            <p>בְּדַפּוּס הָאַלְמָנָה וְהָאַחִים רֹאם</p>
            <p className="vilna-year">תר״מ</p>
          </div>
        </div>
      </div>
    </div>
  );
}

function VilnaChapterList() {
  const chapters = [
    { n: "א", he: "שִׁבְעַת יָמִים", en: "Seven days before Yom Kippur" },
    { n: "ב", he: "בָּרִאשׁוֹנָה", en: "Originally the lots were cast" },
    { n: "ג", he: "אָמַר לָהֶם הַמְמוּנֶּה", en: "The overseer said to them" },
    { n: "ד", he: "טָבַל וְקִידֵּשׁ", en: "He immersed and sanctified" },
    { n: "ה", he: "הוֹצִיאוּ לוֹ", en: "They brought out to him" },
    { n: "ו", he: "בָּא לוֹ כֹּהֵן גָּדוֹל", en: "The Kohen Gadol came" },
    { n: "ז", he: "שִׁלַּח לַעֲזָאזֵל", en: "He sent the scapegoat" },
    { n: "ח", he: "כָּפְרָה עוֹשָׂה", en: "Atonement takes effect" },
  ];
  return (
    <div className="vilna-page" lang="he" dir="rtl">
      <div className="vilna-frame">
        <div className="vilna-frame-inner">
          <p className="vilna-top-band">פִּרְקֵי הַמַּסֶּכֶת</p>
          <div className="vilna-rule"/>
          <div className="vilna-chapters">
            {chapters.map(c => (
              <div key={c.n} className="vilna-ch-row">
                <span className="vilna-ch-n">{c.n}</span>
                <span className="vilna-ch-he">{c.he}</span>
                <span className="vilna-ch-en" dir="ltr">{c.en}</span>
              </div>
            ))}
          </div>
          <div className="vilna-rule"/>
          <div className="vilna-body" style={{fontSize:"0.85em"}}>
            <p>מַסֶּכֶת יוֹמָא · מִסֵּדֶר מוֹעֵד · ח׳ פְּרָקִים</p>
            <p>פֶּרֶק רִאשׁוֹן מַתְחִיל בְּדַף ב׳ עַמּוּד א׳</p>
          </div>
          <div className="vilna-ornament">✦</div>
        </div>
      </div>
    </div>
  );
}

function PlaceholderDaf({ daf, perek }) {
  const entry = dafEntry(daf);
  return (
    <>
      <DafHead daf={daf} perek={perek} summary={entry?.topic || ""} isBookmarked={false} onBookmark={()=>{}} isCompleted={false} onComplete={()=>{}}/>

      <div className="placeholder-banner">
        <span className="icon" aria-hidden="true">🕒</span>
        <div>
          <strong>This amud is in the queue.</strong> Full sugyot and glossary are being prepared. The structure below previews what's coming.
        </div>
      </div>

      <div className="placeholder">
        <div className="placeholder-card">
          <h3>What this amud covers</h3>
          <p>{entry?.topic || "Continuing the sugya from the previous amud."}</p>
        </div>
        <div className="placeholder-card">
          <h3>Cross-references being prepared</h3>
          <p>Artscroll · Koren · Soncino · Steinsaltz, with verified mefarshim and inline ⚠ flags where editions disagree.</p>
        </div>
      </div>

      <div className="ph-topics">
        {["Mishnah",
          "Opening question",
          "First proof",
          "Counter-objection",
          "Rabbinic resolution",
          "Practical halakhah",
        ].map((t, i) => (
          <div className="ph-topic" key={t}>
            <span className="n">SUGYA · {String(i+1).padStart(2,"0")}</span>
            <span className="t">{t}</span>
            <span className="he">{["מַתְנִיתִין","קוּשְׁיָא","רְאָיָה","תְּיוּבְתָּא","מַסְקָנָא","הֲלָכָה לְמַעֲשֶׂה"][i]}</span>
          </div>
        ))}
      </div>
    </>
  );
}

// =============================================================================
// FOOT NAV
// =============================================================================
function FootNav({ daf, onSelect }) {
  const i = dafIdx(daf);
  const prev = i > 0 ? DAF_INDEX[i - 1] : null;
  const next = i < DAF_INDEX.length - 1 ? DAF_INDEX[i + 1] : null;
  return (
    <nav className="footnav">
      <button className="footnav-btn" disabled={!prev} onClick={() => prev && onSelect(prev.id)}>
        <span className="dir"><Icons.Arrow dir="left"/> Previous</span>
        {prev && <span className="name">{TRACTATE_META.title} {prev.id}</span>}
        {prev && <span className="name-he">{hebrewizeDaf(prev.id)}</span>}
      </button>
      <button className="footnav-btn next" disabled={!next} onClick={() => next && onSelect(next.id)}>
        <span className="dir">Next <Icons.Arrow dir="right"/></span>
        {next && <span className="name">{TRACTATE_META.title} {next.id}</span>}
        {next && <span className="name-he">{hebrewizeDaf(next.id)}</span>}
      </button>
    </nav>
  );
}

// =============================================================================
// JUMP MODAL — command-palette
// =============================================================================
function JumpModal({ open, onClose, currentDaf, bookmarks, completed, onSelect }) {
  const [q, setQ] = useState("");
  const [focusIdx, setFocusIdx] = useState(0);
  const inputRef = useRef(null);

  useEffect(() => {
    if (open) {
      setQ("");
      const idx = DAF_INDEX.findIndex(d => d.id === currentDaf);
      setFocusIdx(idx >= 0 ? idx : 0);
      setTimeout(() => {
        inputRef.current?.focus();
        document.querySelector(".modal-row.is-active")?.scrollIntoView({ block: "center", behavior: "instant" });
      }, 30);
    }
  }, [open, currentDaf]);

  const filtered = useMemo(() => {
    if (!q.trim()) return DAF_INDEX;
    const Q = q.trim().toLowerCase();
    return DAF_INDEX.filter(d => {
      return d.id.toLowerCase().includes(Q)
          || d.topic.toLowerCase().includes(Q)
          || ("perek " + d.perek).includes(Q)
          || (d.status === "rich" && "rich".includes(Q));
    });
  }, [q]);

  useEffect(() => {
    if (!open) return;
    const onKey = (e) => {
      if (e.key === "Escape") { onClose(); }
      else if (e.key === "ArrowDown") { e.preventDefault(); setFocusIdx(i => Math.min(i + 1, filtered.length - 1)); }
      else if (e.key === "ArrowUp")   { e.preventDefault(); setFocusIdx(i => Math.max(i - 1, 0)); }
      else if (e.key === "Enter") {
        const pick = filtered[focusIdx];
        if (pick) { onSelect(pick.id); onClose(); }
      }
    };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [open, filtered, focusIdx, onClose, onSelect]);

  if (!open) return null;

  // Group by perek
  const byPerek = {};
  filtered.forEach(d => {
    (byPerek[d.perek] = byPerek[d.perek] || []).push(d);
  });

  let row = 0;
  return (
    <div className="modal-backdrop" onClick={onClose}>
      <div className="modal" onClick={e => e.stopPropagation()}>
        <div className="modal-search">
          <Icons.Search/>
          <input
            ref={inputRef}
            value={q}
            onChange={e => { setQ(e.target.value); setFocusIdx(0); }}
            placeholder="Jump to daf — type number, topic, or 'rich'…"
          />
          <span className="esc">esc</span>
        </div>
        <div className="modal-list">
          {Object.keys(byPerek).map(pn => {
            const perek = PEREK_BY_N[pn];
            return (
              <div key={pn}>
                <div className="modal-perek">Perek {pn}</div>
                {byPerek[pn].map(d => {
                  const myRow = row++;
                  const isActive = d.id === currentDaf;
                  const isFocused = myRow === focusIdx;
                  const isBm = bookmarks.includes(d.id);
                  const isDone = completed.includes(d.id);
                  return (
                    <button
                      key={d.id}
                      className={"modal-row" + (isActive ? " is-active" : "") + (isFocused ? " is-focused" : "")}
                      onClick={() => { onSelect(d.id); onClose(); }}
                      onMouseEnter={() => setFocusIdx(myRow)}
                    >
                      <span className="n">{TRACTATE_META.title} {d.id} <span className="n-he" lang="he" dir="rtl">{gemaraId(d.id)}</span></span>
                      <span className="t">{d.topic}</span>
                      <span className="badges">
                        {d.status === "rich" && <span className="badge rich">RICH</span>}
                        {isBm && <span className="badge bm">★</span>}
                        {isDone && <span className="badge done">✓</span>}
                      </span>
                    </button>
                  );
                })}
              </div>
            );
          })}
          {filtered.length === 0 && (
            <div style={{padding: "24px 14px", color: "var(--ink-mute)", fontSize: "0.9rem", textAlign: "center"}}>
              No amudim match — try a different search.
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

// Initialized in s.onload after learning_data.js is available.
let PEREK_BY_N = null;
function initPerekByN() {
  PEREK_BY_N = PERAKIM.reduce((acc, p) => { acc[p.n] = p; return acc; }, {});
}

// =============================================================================
// APP
// =============================================================================
function initialDafFromUrl() {
  const qp = new URLSearchParams(window.location.search);
  const daf = qp.get("daf");
  return DAF_INDEX.some(d => d.id === daf) ? daf : null;
}

const SITE_BASE = "https://dmo18.github.io/MySugya";

function syncUrlDaf(daf) {
  const url = new URL(window.location.href);
  url.searchParams.set("module", TRACTATE_META.id);
  url.searchParams.set("daf", daf);
  history.replaceState({}, "", url);
}

function App() {
  const normalizeDaf = useCallback((daf) => (
    DAF_INDEX.some(d => d.id === daf) ? daf : DAF_INDEX[0].id
  ), []);

  // Persistent state
  const [currentDaf, setCurrentDaf] = useState(() =>
    normalizeDaf(initialDafFromUrl() || LS.get(TRACTATE_META.id + ":lastDaf", "1a"))
  );
  const [bookmarks, setBookmarks]   = useState(() => LS.get(TRACTATE_META.id + ":bookmarks", []));
  const [completed, setCompleted]   = useState(() => LS.get(TRACTATE_META.id + ":completed", []));

  // Tweaks (persisted by TweaksPanel via __edit_mode_set_keys)
  // mysugya:tweaks is universal; fall back to yoma:tweaks once for existing users
  const [tweaks, setTweak] = useTweaks({ ...TWEAK_DEFAULTS, ...LS.get("mysugya:tweaks", LS.get("yoma:tweaks", {})) });

  // Jump modal
  const [jumpOpen, setJumpOpen] = useState(false);

  // Vilna position tracking
  const [scrollPct, setScrollPct] = useState(0);
  const [currentSugyaIdx, setCurrentSugyaIdx] = useState(0);

  useEffect(() => {
    const onScroll = () => {
      const doc = document.documentElement;
      const max = doc.scrollHeight - doc.clientHeight;
      setScrollPct(max > 0 ? window.scrollY / max : 0);
      const els = document.querySelectorAll(".sugya[id]");
      let best = 0;
      els.forEach((el, i) => { if (el.getBoundingClientRect().top <= 120) best = i; });
      setCurrentSugyaIdx(best);
    };
    window.addEventListener("scroll", onScroll, { passive: true });
    return () => window.removeEventListener("scroll", onScroll);
  }, []);

  useEffect(() => { setScrollPct(0); setCurrentSugyaIdx(0); }, [currentDaf]);

  // localStorage syncs
  useEffect(() => { LS.set(TRACTATE_META.id + ":lastDaf", currentDaf); syncUrlDaf(currentDaf); }, [currentDaf]);
  useEffect(() => { LS.set("mysugya:tweaks", tweaks); }, [tweaks]);
  useEffect(() => { LS.set(TRACTATE_META.id + ":bookmarks", bookmarks); }, [bookmarks]);
  useEffect(() => { LS.set(TRACTATE_META.id + ":completed", completed); }, [completed]);

  // Save scroll per daf
  useEffect(() => {
    const saved = LS.get(TRACTATE_META.id + ":scroll:" + currentDaf, 0);
    requestAnimationFrame(() => window.scrollTo({top: saved, behavior: "auto"}));
    let timer = null;
    const onScroll = () => {
      clearTimeout(timer);
      timer = setTimeout(() => {
        LS.set(TRACTATE_META.id + ":scroll:" + currentDaf, window.scrollY);
      }, 150);
    };
    window.addEventListener("scroll", onScroll);
    return () => { window.removeEventListener("scroll", onScroll); clearTimeout(timer); };
  }, [currentDaf]);

  // Theme + accent + font sizes applied to <html>
  useEffect(() => {
    const root = document.documentElement;
    const mql = window.matchMedia?.('(prefers-color-scheme: dark)');
    const lightModes = new Set(["light", "mist", "sepia"]);
    const apply = () => {
      const resolved = tweaks.mode === "system"
        ? (mql?.matches ? "dark" : "mist")
        : tweaks.mode;
      root.setAttribute("data-mode", resolved);
      root.setAttribute("data-accent", accentToToken(tweaks.accent));
      root.style.setProperty("--fs-hebrew",  tweaks.fontSizeHe + "rem");
      root.style.setProperty("--fs-english", tweaks.fontSizeEn + "rem");
      const meta = document.querySelector('meta[name="color-scheme"]');
      if (meta) meta.content = lightModes.has(resolved) ? "light" : "dark";
    };
    apply();
    if (tweaks.mode === "system") mql?.addEventListener('change', apply);
    return () => mql?.removeEventListener('change', apply);
  }, [tweaks.mode, tweaks.accent, tweaks.fontSizeHe, tweaks.fontSizeEn]);

  // Keyboard shortcuts
  useEffect(() => {
    const onKey = (e) => {
      const meta = e.metaKey || e.ctrlKey;
      const target = e.target;
      const isEditable = target && (
        target.tagName === "INPUT" ||
        target.tagName === "TEXTAREA" ||
        target.tagName === "SELECT" ||
        target.isContentEditable
      );
      if (meta && e.key.toLowerCase() === "k") {
        e.preventDefault();
        setJumpOpen(v => !v);
      } else if (!meta && !isEditable && !jumpOpen) {
        if (e.key === "ArrowLeft")  goPrev();
        if (e.key === "ArrowRight") goNext();
      }
    };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [currentDaf, jumpOpen]);

  const entry = dafEntry(currentDaf);
  const perek = PERAKIM.find(p => p.n === entry.perek) || PERAKIM[0];
  const content = DAF_CONTENT[currentDaf];

  const isBookmarked = bookmarks.includes(currentDaf);
  const isCompleted  = completed.includes(currentDaf);

  const toggleBookmark = () => setBookmarks(bs => bs.includes(currentDaf) ? bs.filter(x => x !== currentDaf) : [...bs, currentDaf]);
  const toggleCompleted = () => setCompleted(cs => cs.includes(currentDaf) ? cs.filter(x => x !== currentDaf) : [...cs, currentDaf]);

  const goPrev = useCallback(() => {
    const i = dafIdx(currentDaf);
    if (i > 0) { setCurrentDaf(DAF_INDEX[i - 1].id); window.scrollTo({top: 0, behavior: "auto"}); }
  }, [currentDaf]);
  const goNext = useCallback(() => {
    const i = dafIdx(currentDaf);
    if (i < DAF_INDEX.length - 1) { setCurrentDaf(DAF_INDEX[i + 1].id); window.scrollTo({top: 0, behavior: "auto"}); }
  }, [currentDaf]);

  const onSelect = (id) => { setCurrentDaf(normalizeDaf(id)); window.scrollTo({top: 0, behavior: "auto"}); };

  return (
    <div className="app">
      <Chrome
        daf={currentDaf}
        perek={perek}
        hasPrev={dafIdx(currentDaf) > 0}
        hasNext={dafIdx(currentDaf) < DAF_INDEX.length - 1}
        onPrev={goPrev}
        onNext={goNext}
        isBookmarked={isBookmarked}
        onBookmark={toggleBookmark}
        onJump={() => setJumpOpen(true)}
        onTweaks={() => window.postMessage({ type: '__activate_edit_mode' }, '*')}
        scrollPct={scrollPct}
        showGaugeBar={tweaks.gaugeBar}
      />

      {tweaks.timeline && <SugyaTimeline sugyot={content?.sugyot} currentIdx={currentSugyaIdx}/>}

      <main className="daf" key={currentDaf}>
        {entry?.status === "title" ? (
          currentDaf === "1a" ? <VilnaTitlePage/> : <VilnaChapterList/>
        ) : content ? (
          <>
            {content.sugyot.map((s, i) => (
              <Sugya key={s.id} sugya={s} idx={i} total={content.sugyot.length} tweaks={tweaks}/>
            ))}
            {content.rashiLines && <RashiPanel lines={content.rashiLines} showNekudot={tweaks.nekudot}/>}
            <Glossary items={content.glossary}/>
          </>
        ) : (
          <PlaceholderDaf daf={currentDaf} perek={perek}/>
        )}

        <FootNav daf={currentDaf} onSelect={onSelect}/>
      </main>

      <JumpModal
        open={jumpOpen}
        onClose={() => setJumpOpen(false)}
        currentDaf={currentDaf}
        bookmarks={bookmarks}
        completed={completed}
        onSelect={onSelect}
      />

      {tweaks.pipDots && <SugyaPipDots sugyot={content?.sugyot} currentIdx={currentSugyaIdx}/>}
      {tweaks.bottomDock && <BottomDock sugyot={content?.sugyot} currentIdx={currentSugyaIdx}/>}

      <footer className="app-footer">
        <span>Version {DATA_VERSION}</span>
        <span className="footer-dedication" lang="he" dir="rtl">לרפואת יעקב בן דינה · לעילוי נשמת אהרן בן יהודה ואהרן בן יוסף</span>
      </footer>
      <MySugyaTweaksPanel tweaks={tweaks} setTweak={setTweak}/>
    </div>
  );
}

// =============================================================================
// TWEAKS — defaults + panel
// =============================================================================
// DATA_VERSION from learning_data.js is the canonical version.

const TWEAK_DEFAULTS = /*EDITMODE-BEGIN*/{
  "mode": "system",
  "accent": "#06b6d4",
  "fontSizeHe": 1.4,
  "fontSizeEn": 1.0,
  "nekudot": true,
  "showEnglish": true,
  "boldLiteral": true,
  "vilnaLines": true,
  "gaugeBar": false,
  "timeline": false,
  "pipDots": false,
  "bottomDock": false,
}/*EDITMODE-END*/;

function accentToToken(hex) {
  if (!hex) return "gold";
  return ACCENT_BY_HEX[String(hex).toLowerCase()] || "gold";
}

const ACCENT_BY_HEX = {
  "#a37a2c": "gold",
  "#7a2a2a": "oxblood",
  "#1f3c66": "navy",
  "#2e4a36": "ink-green",
  "#0ea5e9": "sky",
  "#8b5cf6": "violet",
  "#f43f5e": "rose",
  "#14b8a6": "teal",
  "#06b6d4": "cyan",
  "#22c55e": "lime",
  "#f59e0b": "amber",
  "#6366f1": "indigo",
};

function MySugyaTweaksPanel({ tweaks, setTweak }) {
  const reset = () => setTweak(TWEAK_DEFAULTS);
  return (
    <TweaksPanel title={TRACTATE_META.title + " · Tweaks"}>
      <TweakSection label="Theme">
        <TweakRadio
          label="Mode"
          value={tweaks.mode}
          options={[
            { value: "system", label: "System" },
            { value: "mist", label: "Mist" },
            { value: "light", label: "Light" },
            { value: "sepia", label: "Sepia" },
            { value: "night", label: "Night" },
            { value: "dark",  label: "Dark"  },
          ]}
          onChange={v => setTweak("mode", v)}
        />
        <TweakColor
          label="Accent"
          value={tweaks.accent}
          options={["#a37a2c", "#7a2a2a", "#1f3c66", "#2e4a36"]}
          onChange={v => setTweak("accent", v)}
        />
      </TweakSection>

      <TweakSection label="Typography">
        <TweakSlider
          label="Hebrew size"
          value={tweaks.fontSizeHe}
          min={1.0} max={2.0} step={0.05} unit="rem"
          onChange={v => setTweak("fontSizeHe", v)}
        />
        <TweakSlider
          label="English size"
          value={tweaks.fontSizeEn}
          min={0.85} max={1.3} step={0.025} unit="rem"
          onChange={v => setTweak("fontSizeEn", v)}
        />
      </TweakSection>

      <TweakSection label="Reading aids">
        <TweakToggle label="English (elucidated)" value={tweaks.showEnglish} onChange={v => setTweak("showEnglish", v)}/>
        <TweakToggle label="Bold literal text" value={tweaks.boldLiteral} onChange={v => setTweak("boldLiteral", v)}/>
        <TweakToggle label="Nekudot (vowel marks)" value={tweaks.nekudot} onChange={v => setTweak("nekudot", v)}/>
        <TweakToggle label="Vilna line numbers" value={tweaks.vilnaLines} onChange={v => setTweak("vilnaLines", v)}/>
      </TweakSection>

      <TweakSection label="Position indicators">
        <TweakToggle label="Gauge bar" value={tweaks.gaugeBar} onChange={v => setTweak("gaugeBar", v)}/>
        <TweakToggle label="Timeline strip" value={tweaks.timeline} onChange={v => setTweak("timeline", v)}/>
        <TweakToggle label="Pip dots" value={tweaks.pipDots} onChange={v => setTweak("pipDots", v)}/>
        <TweakToggle label="Bottom dock" value={tweaks.bottomDock} onChange={v => setTweak("bottomDock", v)}/>
      </TweakSection>

      <TweakSection label="Reset">
        <button className="twk-btn secondary" style={{width:"100%"}} onClick={reset}>
          Reset all to defaults
        </button>
      </TweakSection>

    </TweaksPanel>
  );
}

// =============================================================================
// LANDING PAGE — shown when no ?module= param is present
// =============================================================================

const SEDER_LABELS = {
  Moed:    { he: "מוֹעֵד",    en: "Festivals" },
  Nashim:  { he: "נָשִׁים",   en: "Women" },
  Nezikin: { he: "נְזִיקִין", en: "Damages" },
  Zeraim:  { he: "זְרָעִים",  en: "Seeds" },
  Kodashim:{ he: "קֳדָשִׁים", en: "Holy Things" },
  Taharot: { he: "טָהֳרוֹת",  en: "Purities" },
};

function TractateCard({ mod }) {
  const seder = SEDER_LABELS[mod.seder] || { he: mod.seder, en: mod.seder };
  const url = "?module=" + mod.id;
  return (
    <a className="tractate-card" href={url} aria-label={"Study " + mod.title}>
      <div className="tc-header">
        <span className="tc-seder-badge">
          <span lang="he" dir="rtl">{seder.he}</span>
          {" · "}{mod.seder}
        </span>
      </div>
      <div className="tc-body">
        <span className="tc-title-he" lang="he" dir="rtl">{mod.title_he}</span>
        <span className="tc-title-en">{mod.title}</span>
        <span className="tc-subtitle">
          Seder {mod.seder} · {seder.en}
        </span>
      </div>
      <div className="tc-stats">
        <span className="tc-stat"><strong>{mod.totalDaf}</strong> amudim</span>
        <span className="tc-stat-sep" aria-hidden="true">·</span>
        <span className="tc-stat">Daf {mod.dafRange.first} – {mod.dafRange.last}</span>
        <span className="tc-stat-sep" aria-hidden="true">·</span>
        <span className="tc-stat"><strong>8</strong> perakim</span>
      </div>
      <div className="tc-footer">
        <span className="tc-cta">Begin studying <span aria-hidden="true">→</span></span>
      </div>
    </a>
  );
}

function LandingPage() {
  return (
    <div className="landing">

      <header className="landing-chrome">
        <div className="brand">
          <div className="brand-mark">ס</div>
          <span className="brand-name">My Sugya</span>
        </div>
        <span className="landing-tagline-top">Talmud study, sugya by sugya</span>
      </header>

      {/* HERO */}
      <section className="landing-hero">
        <div className="landing-hero-inner">
          <p className="landing-hero-eyebrow">Babylonian Talmud · Interactive Study</p>
          <h1 className="landing-hero-title">
            Understand the Gemara.
            <span className="lht-he" lang="he" dir="rtl">הַגְּמָרָא</span>
          </h1>
          <p className="landing-hero-sub">
            Each daf is broken into labeled sugyot with interlinear Hebrew-English,
            Rashi, argument flow, and glossary. No account needed.
          </p>
          <div className="landing-stats-grid">
            <div className="lsg-item">
              <span className="lsg-num">492</span>
              <span className="lsg-label">enriched sugyot</span>
            </div>
            <div className="lsg-item">
              <span className="lsg-num">8,854</span>
              <span className="lsg-label">Rashi lines</span>
            </div>
            <div className="lsg-item">
              <span className="lsg-num">173</span>
              <span className="lsg-label">amudim</span>
            </div>
            <div className="lsg-item">
              <span className="lsg-num">8</span>
              <span className="lsg-label">perakim</span>
            </div>
          </div>
        </div>

        <div className="landing-hero-deco" aria-hidden="true">
          <div className="lhd-folio">
            <div className="lhd-folio-inner">
              <p className="lhd-tractate">מַסֶּכֶת יוֹמָא</p>
              <div className="lhd-rule"/>
              <p className="lhd-ref">דף כ״ח עמוד ב׳</p>
              <p className="lhd-line">אָמַר רַב יְהוּדָה אָמַר שְׁמוּאֵל</p>
              <p className="lhd-line">כׇּל כְּהוּנָה שֶׁמִּינָה אוֹתָהּ</p>
              <p className="lhd-line">שַׁבְּתָאי בֶּן מַרְיָנוּס</p>
              <div className="lhd-rule"/>
              <p className="lhd-line lhd-line-en">On the appointment of the Kohen Gadol</p>
              <p className="lhd-tag">Question · שְׁאֵלָה</p>
            </div>
          </div>
        </div>
      </section>

      {/* TRACTATE PICKER — primary CTA, shown before features */}
      <section className="landing-tractates">
        <div className="landing-section-inner">
          <h2 className="landing-section-title">
            Choose a Masechta
            <span className="lst-he" lang="he" dir="rtl">בְּחַר מַסֶּכֶת</span>
          </h2>
          <p className="landing-section-sub">Select a tractate to begin. More coming soon.</p>
          <div className="tractate-grid">
            {MYSUGYA_MANIFEST.map(mod => <TractateCard key={mod.id} mod={mod}/>)}
            <div className="tractate-card tc-coming-soon" aria-hidden="true">
              <div className="tc-header">
                <span className="tc-seder-badge">Coming soon</span>
              </div>
              <div className="tc-body">
                <span className="tc-title-he" lang="he" dir="rtl">בְּרָכוֹת</span>
                <span className="tc-title-en">Berakhot</span>
                <span className="tc-subtitle">Seder Zeraim · Prayers and blessings</span>
              </div>
              <div className="tc-footer">
                <span className="tc-cta tc-cta--mute">In preparation</span>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* FEATURES */}
      <section className="landing-how">
        <div className="landing-section-inner">
          <h2 className="landing-section-title">What you get</h2>
          <div className="landing-features">
            <div className="lf-item">
              <span className="lf-icon" aria-hidden="true">§</span>
              <div className="lf-text">
                <strong>Sugya structure</strong>
                <p>Each daf split into labeled discussion units. Navigate by topic, not just by line.</p>
              </div>
            </div>
            <div className="lf-item">
              <span className="lf-icon" aria-hidden="true">א</span>
              <div className="lf-text">
                <strong>Interlinear Hebrew-English</strong>
                <p>Full nekudot with Sefaria-sourced English. Toggle vowel marks anytime.</p>
              </div>
            </div>
            <div className="lf-item">
              <span className="lf-icon" aria-hidden="true">↯</span>
              <div className="lf-text">
                <strong>Argument flow</strong>
                <p>Question, proof, objection, resolution - mapped for every sugya.</p>
              </div>
            </div>
            <div className="lf-item">
              <span className="lf-icon lf-icon--he" aria-hidden="true">רש"י</span>
              <div className="lf-text">
                <strong>Rashi commentary</strong>
                <p>All Rashi lines with Vilna references and English helper translations.</p>
              </div>
            </div>
            <div className="lf-item">
              <span className="lf-icon" aria-hidden="true">מ</span>
              <div className="lf-text">
                <strong>Glossary per daf</strong>
                <p>Aramaic and Hebrew key terms defined in context, with transliterations.</p>
              </div>
            </div>
            <div className="lf-item">
              <span className="lf-icon" aria-hidden="true">★</span>
              <div className="lf-text">
                <strong>Progress tracking</strong>
                <p>Bookmark daf, mark complete, resume exactly where you left off - stored locally.</p>
              </div>
            </div>
          </div>
        </div>
      </section>

      <footer className="landing-footer">
        <div className="landing-footer-inner">
          <span className="footer-dedication" lang="he" dir="rtl">לרפואת יעקב בן דינה · לעילוי נשמת אהרן בן יהודה ואהרן בן יוסף</span>
          <span className="lf-version">v{MYSUGYA_MANIFEST[0]?.dataVersion || ""}</span>
        </div>
      </footer>

    </div>
  );
}

// =============================================================================
// MOUNT — dynamic module loading
// =============================================================================
(function() {
  const qp = new URLSearchParams(window.location.search);
  const moduleId = qp.get("module");

  if (!moduleId) {
    const rootEl = ReactDOM.createRoot(document.getElementById("root"));
    rootEl.render(<LandingPage/>);
    return;
  }

  const mod = MYSUGYA_MANIFEST.find(function(m) { return m.id === moduleId; });

  if (!mod) {
    const rootEl = ReactDOM.createRoot(document.getElementById("root"));
    rootEl.render(<LandingPage/>);
    return;
  }

  const s = document.createElement("script");
  s.src = mod.dataScript + "?v=" + (mod.dataVersion || "1");
  s.onload = function() {
    initEnCache();
    initPerekByN();
    const rootEl = ReactDOM.createRoot(document.getElementById("root"));
    rootEl.render(<App/>);
  };
  s.onerror = function() {
    document.getElementById("root").innerHTML =
      '<p style="padding:2rem;font-family:sans-serif;color:#c00">Failed to load module data: ' +
      mod.dataScript + '</p>';
  };
  document.head.appendChild(s);
})();
