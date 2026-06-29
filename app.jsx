/* ============================================
   My Sugya — React Components
   ============================================ */

const { useState, useEffect, useMemo, useRef, useCallback } = React;

/* global __MYSUGYA_PLATFORM_VERSION__ */
const PLATFORM_VERSION = typeof __MYSUGYA_PLATFORM_VERSION__ !== "undefined"
  ? __MYSUGYA_PLATFORM_VERSION__
  : (typeof DATA_VERSION !== "undefined" ? DATA_VERSION : "");

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
// LOGO — samekh (ס · Sugya) holding the two-partner S (My / chavruta).
// Single-color via currentColor, so it adapts to light and dark surfaces.
// =============================================================================
function Logo({ className }) {
  return (
    <svg
      className={className || "brand-logo"}
      viewBox="0 0 64 64"
      width="28"
      height="28"
      fill="none"
      stroke="currentColor"
      strokeLinecap="round"
      strokeLinejoin="round"
      role="img"
      aria-label="My Sugya"
    >
      <rect x="10" y="13" width="44" height="42" rx="16" strokeWidth="4.5" />
      <path d="M16 14 C11 11 10 7 14 5" strokeWidth="4.5" />
      <g strokeWidth="3.6">
        <path d="M39 27 C32 24 28 28 32 32 C36 36 32 41 25 38" />
        <circle cx="40.5" cy="26.5" r="3.4" fill="currentColor" stroke="none" />
        <circle cx="23.5" cy="38.5" r="3.4" fill="currentColor" stroke="none" />
      </g>
    </svg>
  );
}

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
            aria-label={s.title}
            aria-current={i === currentIdx ? "true" : undefined}
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
    <nav className="pip-dots" aria-label="Sugya navigation">
      {sugyot.map((s, i) => (
        <button
          key={s.id}
          className={"pip-dot" + (i <= currentIdx ? " reached" : "") + (i === currentIdx ? " current" : "")}
          onClick={() => document.getElementById(s.id)?.scrollIntoView({ behavior: "smooth" })}
          title={s.title}
          aria-label={s.title}
          aria-current={i === currentIdx ? "true" : undefined}
        />
      ))}
    </nav>
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
          aria-label={s.title}
          aria-current={i === currentIdx ? "true" : undefined}
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
          <Logo className="brand-logo" />
          <span className="brand-name">My Sugya</span>
          <span className="brand-beta">BETA</span>
        </div>

        <div className="chrome-location">
          <button className="chrome-nav-arrow" disabled={!hasPrev} onClick={onPrev} aria-label="Previous daf">
            <Icons.Arrow dir="left"/>
          </button>
          <button className="chrome-daf" onClick={onJump} title="Pick a daf (⌘K)" aria-label="Open daf picker">
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
            aria-label={isBookmarked ? "Remove bookmark" : "Bookmark this daf"}
          >
            {isBookmarked ? <Icons.BookmarkFilled/> : <Icons.Bookmark/>}
          </button>
          <button className="icon-btn" onClick={onTweaks} title="Open Tweaks" aria-label="Open tweaks settings">
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
            const label = [d.id, isDone && "completed", isBm && "bookmarked", isRich && "rich content"].filter(Boolean).join(", ");
            return (
              <button key={d.id} className={cls} onClick={() => onSelect(d.id)} aria-label={label} aria-current={isActive ? "true" : undefined}>
                <span className="rail-tip" aria-hidden="true">{d.id}{isRich ? " · rich" : ""}</span>
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
function Line({ line, idx, showNekudot, showVilnaLines, showEnglish, boldLiteral, hasRashi, onRashiToggle, rashiActive }) {
  const tag = LINE_TAGS[line.kind] || LINE_TAGS.aside;
  const heRaw = stripHtml(line.he);
  const heText = showNekudot ? heRaw : stripNekudot(heRaw);
  const hasVilna = line.vilna_line != null;
  return (
    <div className="line" data-kind={line.kind} data-has-rashi={hasRashi ? "1" : "0"}>
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
          {hasRashi && (
            <button
              className="rashi-badge"
              onClick={onRashiToggle}
              aria-pressed={rashiActive}
              title="Show Rashi for this line"
            >
              ᾨ Rashi
            </button>
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

function stripHtml(s) { return String(s || "").replace(/<[^>]+>/g, ""); }

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
  return s.replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;").replace(/"/g, "&quot;");
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
    const params = new URLSearchParams({ module: TRACTATE_META.id, daf });
    const baseUrl = window.location.origin + window.location.pathname;
    const url = `${baseUrl}?${params.toString()}#${sugya.id}`;
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
function ArgumentFlowPanel({ steps, hideLabel = false }) {
  if (!steps || !steps.length) return null;
  return (
    <div className="learn-panel learn-args">
      {!hideLabel && <span className="learn-label">Argument flow</span>}
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

function useMediaQuery(query) {
  const getMatches = () => (
    typeof window !== "undefined" && typeof window.matchMedia === "function"
      ? window.matchMedia(query).matches
      : false
  );
  const [matches, setMatches] = useState(getMatches);

  useEffect(() => {
    if (typeof window === "undefined" || typeof window.matchMedia !== "function") return undefined;
    const mediaQuery = window.matchMedia(query);
    const handleChange = event => setMatches(event.matches);
    setMatches(mediaQuery.matches);
    if (typeof mediaQuery.addEventListener === "function") {
      mediaQuery.addEventListener("change", handleChange);
      return () => mediaQuery.removeEventListener("change", handleChange);
    }
    mediaQuery.addListener(handleChange);
    return () => mediaQuery.removeListener(handleChange);
  }, [query]);

  return matches;
}

function ArgumentFlowDisclosure({ steps }) {
  const isMobile = useMediaQuery("(max-width: 720px)");
  const [open, setOpen] = useState(() => (
    typeof window !== "undefined" && typeof window.matchMedia === "function"
      ? !window.matchMedia("(max-width: 720px)").matches
      : true
  ));

  useEffect(() => {
    setOpen(!isMobile);
  }, [isMobile]);

  if (!steps || !steps.length) return null;
  return (
    <details
      className="argument-flow-disclosure"
      open={open}
      onToggle={event => setOpen(event.currentTarget.open)}
    >
      <summary>Argument flow</summary>
      <div className="argument-flow-disclosure-content">
        <ArgumentFlowPanel steps={steps} hideLabel />
      </div>
    </details>
  );
}

function SugyaWhats({ whats }) {
  if (!whats) return null;
  return (
    <div className="sugya-whats">
      <span className="label">What's happening</span>
      <p>{whats}</p>
    </div>
  );
}

function LearningPanel({ learning, display }) {
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
function Sugya({ sugya, idx, total, tweaks, rashiMap }) {
  const [nusachOpen, setNusachOpen] = useState(false);
  const [learnOpen, setLearnOpen]   = useState(false);
  const [storiesOpen, setStoriesOpen] = useState(false);
  const [scenesOpen, setScenesOpen] = useState(false);
  const [activeRashiLine, setActiveRashiLine] = useState(null);

  const display  = sugya.display  || {};
  const learning = sugya.learning || null;
  const whats    = display.whats  || sugya.whats;
  const oneLine  = display.oneLine;
  const hint     = display.hint   || sugya.hint;
  const title    = display.title  || sugya.title;

  // Aggregate narrative quiz questions (stories)
  const narrativeQuizzes = useMemo(() => {
    return (sugya.quizSeeds || []).filter(q => q.question && q.answer);
  }, [sugya.quizSeeds]);

  // Aggregate visualizable elements (scenes)
  const visualScenes = useMemo(() => {
    return (sugya.visualizableElements || []).filter(v => v.item || v.description);
  }, [sugya.visualizableElements]);

  const hasUnderstanding = !!whats || !!learning;

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

        <div className="desktop-understanding">
          <SugyaWhats whats={whats} />
          {learning && (
            <LearningPanel learning={learning} display={display} />
          )}
        </div>

        <div className="lines">
          {sugya.lines.filter(Boolean).map((line, i) => {
            const rashi = line.vilna_line != null ? rashiMap?.get(line.vilna_line) : null;
            return (
              <div key={i}>
                <Line
                  line={line} idx={i}
                  showNekudot={tweaks.nekudot}
                  showVilnaLines={tweaks.vilnaLines}
                  showEnglish={tweaks.showEnglish}
                  boldLiteral={tweaks.boldLiteral}
                  hasRashi={!!rashi}
                  onRashiToggle={() => setActiveRashiLine(activeRashiLine === line.vilna_line ? null : line.vilna_line)}
                  rashiActive={activeRashiLine === line.vilna_line}
                />
                {rashi && activeRashiLine === line.vilna_line && (
                  <div className="rashi-inline">
                    <p className="rashi-inline-he" lang="he" dir="rtl">{tweaks.nekudot ? rashi.he : stripNekudot(rashi.he)}</p>
                    {rashi.en && tweaks.showEnglish && (
                      <p className="rashi-inline-en">
                        <span dangerouslySetInnerHTML={{__html: enHtml(rashi.en)}}/>
                      </p>
                    )}
                  </div>
                )}
              </div>
            );
          })}
        </div>

        {hasUnderstanding && (
          <details className="mobile-understanding">
            <summary>Understand this sugya</summary>
            <div className="mobile-understanding-content">
              <SugyaWhats whats={whats} />
              {learning && (
                <LearningPanel learning={learning} display={display} />
              )}
            </div>
          </details>
        )}

        {sugya.argumentFlow && sugya.argumentFlow.length > 0 && (
          <ArgumentFlowDisclosure steps={sugya.argumentFlow} />
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
          {narrativeQuizzes.length > 0 && (
            <Chip
              open={storiesOpen}
              onToggle={() => setStoriesOpen(v => !v)}
              label="Stories" labelHe="סִפּוּרִים"
              kind="Narrative Questions"
            >
              <div className="stories-list">
                {narrativeQuizzes.map((q, i) => (
                  <div key={i} className="story-item">
                    <p className="story-q"><strong>Q:</strong> {q.question}</p>
                    <p className="story-a"><strong>A:</strong> {q.answer}</p>
                  </div>
                ))}
              </div>
            </Chip>
          )}
          {visualScenes.length > 0 && (
            <Chip
              open={scenesOpen}
              onToggle={() => setScenesOpen(v => !v)}
              label="Scenes" labelHe="תַּמּוּנוֹת"
              kind="Visual Elements"
            >
              <div className="scenes-list">
                {visualScenes.map((s, i) => (
                  <div key={i} className="scene-item">
                    <p className="scene-desc">{s.item || s.description}</p>
                    {s.role && <span className="scene-role">{s.role}</span>}
                    {s.priority && <span className="scene-priority">Priority: {s.priority}</span>}
                  </div>
                ))}
              </div>
            </Chip>
          )}
        </div>
      </div>

    </article>
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
  const modalRef = useRef(null);
  const prevFocusRef = useRef(null);

  useEffect(() => {
    if (!open) return;
    prevFocusRef.current = document.activeElement;
    return () => { prevFocusRef.current?.focus?.(); };
  }, [open]);

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
      } else if (e.key === "Tab") {
        const focusable = modalRef.current?.querySelectorAll(
          'button:not([disabled]),input:not([disabled]),[tabindex]:not([tabindex="-1"])'
        );
        if (!focusable?.length) { e.preventDefault(); return; }
        const first = focusable[0], last = focusable[focusable.length - 1];
        if (e.shiftKey) {
          if (document.activeElement === first) { e.preventDefault(); last.focus(); }
        } else {
          if (document.activeElement === last) { e.preventDefault(); first.focus(); }
        }
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
      <div ref={modalRef} className="modal" role="dialog" aria-modal="true" aria-label="Jump to daf" onClick={e => e.stopPropagation()}>
        <div className="modal-search">
          <Icons.Search/>
          <input
            ref={inputRef}
            value={q}
            onChange={e => { setQ(e.target.value); setFocusIdx(0); }}
            placeholder="Jump to daf — type number, topic, or 'rich'…"
            aria-label="Search daf by number, topic, or content type"
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

  // Font sizes applied to <html>; mode/accent are locked to Mist+Gold via html attributes.
  useEffect(() => {
    const root = document.documentElement;
    root.style.setProperty("--fs-hebrew",  tweaks.fontSizeHe + "rem");
    root.style.setProperty("--fs-english", tweaks.fontSizeEn + "rem");
  }, [tweaks.fontSizeHe, tweaks.fontSizeEn]);

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

  const rashiMap = useMemo(() => {
    const map = new Map();
    content?.rashiLines?.forEach(r => {
      if (r.vilnaLine != null) {
        map.set(r.vilnaLine, r);
      }
    });
    return map;
  }, [content?.rashiLines]);

  const renderedSugyot = useMemo(() => {
    if (!content?.sugyot) return null;
    return content.sugyot.map((s, i) => (
      <Sugya key={s.id} sugya={s} idx={i} total={content.sugyot.length} tweaks={tweaks} rashiMap={rashiMap}/>
    ));
  }, [content?.sugyot, rashiMap, tweaks]);

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
        onTweaks={() => window.postMessage({ type: '__activate_edit_mode' }, window.location.origin)}
        scrollPct={scrollPct}
        showGaugeBar={tweaks.gaugeBar}
      />

      {tweaks.timeline && <SugyaTimeline sugyot={content?.sugyot} currentIdx={currentSugyaIdx}/>}

      <main className="daf" key={currentDaf}>
        {entry?.status === "title" ? (
          currentDaf === "1a" ? <VilnaTitlePage/> : <VilnaChapterList/>
        ) : content ? (
          <>
            {renderedSugyot}
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
        <span>Version {PLATFORM_VERSION}</span>
        <span className="footer-dedication" lang="he" dir="rtl">לרפואת יעקב בן דינה · לעילוי נשמת אהרן בן יהודה ואהרן בן יוסף</span>
      </footer>
      <MySugyaTweaksPanel tweaks={tweaks} setTweak={setTweak}/>
    </div>
  );
}

// =============================================================================
// TWEAKS — defaults + panel
// =============================================================================

const TWEAK_DEFAULTS = /*EDITMODE-BEGIN*/{
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

function MySugyaTweaksPanel({ tweaks, setTweak }) {
  const reset = () => setTweak(TWEAK_DEFAULTS);
  return (
    <TweaksPanel title={TRACTATE_META.title + " · Tweaks"}>
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
        {tweaks.showEnglish && (
          <TweakToggle label="Bold literal text" value={tweaks.boldLiteral} onChange={v => setTweak("boldLiteral", v)}/>
        )}
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

// ----- scroll reveal (fade + rise when scrolled into view) ----------------
function Reveal({ children, className, delay, tag }) {
  const ref = useRef(null);
  const [shown, setShown] = useState(false);
  useEffect(() => {
    const el = ref.current;
    if (!el) return;
    const reduce = window.matchMedia && window.matchMedia("(prefers-reduced-motion: reduce)").matches;
    if (reduce) { setShown(true); return; }
    const io = new IntersectionObserver(([e]) => {
      if (e.isIntersecting) { setShown(true); io.disconnect(); }
    }, { threshold: 0.12 });
    io.observe(el);
    return () => io.disconnect();
  }, []);
  const Tag = tag || "div";
  return (
    <Tag
      ref={ref}
      className={"reveal" + (className ? " " + className : "")}
      data-shown={shown ? "1" : "0"}
      style={delay ? { transitionDelay: delay + "ms" } : undefined}
    >
      {children}
    </Tag>
  );
}

// ----- count-up stat (animates when scrolled into view) -------------------
function CountUpStat({ value, label, suffix }) {
  const ref = useRef(null);
  const [n, setN] = useState(0);
  useEffect(() => {
    const el = ref.current;
    if (!el) return;
    const reduce = window.matchMedia && window.matchMedia("(prefers-reduced-motion: reduce)").matches;
    if (reduce) { setN(value); return; }
    let fired = false;
    const io = new IntersectionObserver((entries) => {
      entries.forEach(en => {
        if (en.isIntersecting && !fired) {
          fired = true;
          const dur = 1200, t0 = performance.now();
          const tick = (t) => {
            const p = Math.min(1, (t - t0) / dur);
            const eased = 1 - Math.pow(1 - p, 3);
            setN(Math.round(value * eased));
            if (p < 1) requestAnimationFrame(tick);
          };
          requestAnimationFrame(tick);
        }
      });
    }, { threshold: 0.4 });
    io.observe(el);
    return () => io.disconnect();
  }, [value]);
  return (
    <div ref={ref} className="lsg-item">
      <span className="lsg-num">{n.toLocaleString()}{suffix || ""}</span>
      <span className="lsg-label">{label}</span>
    </div>
  );
}

// ----- argument step metadata: maps schema step types to symbol + Hebrew ----
const STEP_META = {
  case:              { he: "מַעֲשֶׂה",  sym: "▦", en: "Case" },
  question:          { he: "שְׁאֵלָה",  sym: "?", en: "Question" },
  proposal:          { he: "הַצָּעָה",  sym: "✎", en: "Proposal" },
  challenge:         { he: "קֻשְׁיָא",  sym: "↯", en: "Challenge" },
  objection:         { he: "קֻשְׁיָא",  sym: "↯", en: "Objection" },
  counter_objection: { he: "פִּרְכָא",  sym: "⇄", en: "Counter" },
  proof:             { he: "רְאָיָה",   sym: "§", en: "Proof" },
  answer:            { he: "תֵּירוּץ",  sym: "✓", en: "Answer" },
  distinction:       { he: "חִילּוּק",  sym: "⌥", en: "Distinction" },
  qualification:     { he: "סְיָג",     sym: "≈", en: "Qualification" },
  rejection:         { he: "דְּחִיָּה", sym: "✗", en: "Rejection" },
  resolution:        { he: "מַסְקָנָא", sym: "✓", en: "Resolution" },
  takeaway:          { he: "כְּלָל",    sym: "★", en: "Takeaway" },
};
const FLOW_FALLBACK = [
  { type: "question",   label: "A question is raised" },
  { type: "proof",      label: "A proof is brought" },
  { type: "objection",  label: "An objection is pressed" },
  { type: "resolution", label: "The matter is resolved" },
];

// ----- argument-flow demo (the signature feature, animated live) ----------
// Accepts real argumentFlow steps from a loaded sugya; falls back to a
// generic four-move shape until module data arrives.
function ArgumentFlowDemo({ steps, sugyaTitle }) {
  const flow = (steps && steps.length >= 2 ? steps : FLOW_FALLBACK).slice(0, 6);
  const [active, setActive] = useState(0);
  const [paused, setPaused] = useState(false);
  useEffect(() => { setActive(0); }, [steps]);
  useEffect(() => {
    if (paused) return;
    const reduce = window.matchMedia && window.matchMedia("(prefers-reduced-motion: reduce)").matches;
    if (reduce) return;
    const id = setInterval(() => setActive(a => (a + 1) % flow.length), 1700);
    return () => clearInterval(id);
  }, [paused, flow.length]);
  const cur = flow[active] || flow[0];
  return (
    <div className="flow-wrap">
      <div className="flow-demo" onMouseEnter={() => setPaused(true)} onMouseLeave={() => setPaused(false)}>
        {flow.map((s, i) => {
          const m = STEP_META[s.type] || STEP_META.question;
          return (
            <React.Fragment key={s.id || (s.type + "-" + i)}>
              <button
                type="button"
                className="flow-node"
                data-active={i === active ? "1" : "0"}
                onFocus={() => { setPaused(true); setActive(i); }}
                onBlur={() => setPaused(false)}
                onClick={() => setActive(i)}
                aria-label={m.en}
              >
                <span className="flow-sym" aria-hidden="true">{m.sym}</span>
                <span className="flow-he" lang="he" dir="rtl">{m.he}</span>
                <span className="flow-en">{m.en}</span>
              </button>
              {i < flow.length - 1 && (
                <span className="flow-link" data-active={i < active ? "1" : "0"} aria-hidden="true" />
              )}
            </React.Fragment>
          );
        })}
      </div>
      <div className="flow-caption" key={active}>
        {sugyaTitle ? <span className="flow-caption-src">{sugyaTitle}</span> : null}
        <span className="flow-caption-label">{cur && cur.label}</span>
        {cur && cur.text ? <span className="flow-caption-text">{cur.text}</span> : null}
      </div>
    </div>
  );
}

// ----- the Living Daf: 3D folio that tilts to pointer / device motion -----
// Renders a real daf (core Gemara + Rashi column) once module data loads,
// with an instant manifest-based skeleton until then.
function LivingDaf({ featured, mod }) {
  const stageRef = useRef(null);
  const [tilt, setTilt] = useState({ x: 0, y: 0 });
  const [motionOn, setMotionOn] = useState(false);
  const [needsTap, setNeedsTap] = useState(false);

  // iOS gates DeviceOrientation behind a permission prompt requiring a gesture.
  useEffect(() => {
    const DOE = window.DeviceOrientationEvent;
    if (DOE && typeof DOE.requestPermission === "function") {
      setNeedsTap(true);
    } else if (DOE) {
      setMotionOn(true);
    }
  }, []);

  useEffect(() => {
    if (!motionOn) return;
    const reduce = window.matchMedia && window.matchMedia("(prefers-reduced-motion: reduce)").matches;
    if (reduce) return;
    function onOrient(e) {
      const y = Math.max(-20, Math.min(20, (e.gamma || 0) * 0.45));
      const x = Math.max(-20, Math.min(20, ((e.beta || 0) - 45) * 0.32));
      setTilt({ x: -x, y });
    }
    window.addEventListener("deviceorientation", onOrient, true);
    return () => window.removeEventListener("deviceorientation", onOrient, true);
  }, [motionOn]);

  const onPointerMove = useCallback((e) => {
    const el = stageRef.current;
    if (!el || e.pointerType === "touch") return;
    const r = el.getBoundingClientRect();
    const px = (e.clientX - r.left) / r.width - 0.5;
    const py = (e.clientY - r.top) / r.height - 0.5;
    setTilt({ x: py * -14, y: px * 16 });
  }, []);
  const onLeave = useCallback(() => setTilt({ x: 0, y: 0 }), []);

  const enableMotion = useCallback(() => {
    const DOE = window.DeviceOrientationEvent;
    if (DOE && typeof DOE.requestPermission === "function") {
      DOE.requestPermission().then(state => {
        if (state === "granted") { setMotionOn(true); setNeedsTap(false); }
      }).catch(() => {});
    }
  }, []);

  const folioStyle = {
    transform: `perspective(1000px) rotateX(${tilt.x}deg) rotateY(${tilt.y}deg)`,
  };
  const sheenStyle = {
    transform: `translate3d(${tilt.y * 2.2}px, ${-tilt.x * 2.2}px, 60px)`,
    opacity: 0.55 + Math.min(0.35, (Math.abs(tilt.x) + Math.abs(tilt.y)) / 60),
  };

  // ---- derive real content from loaded data, fall back to manifest ----
  const titleHe = (featured && featured.meta && featured.meta.title_he) || (mod && mod.title_he) || "";
  const refHe = hebrewizeDaf((featured && featured.dafId) || (mod && mod.dafRange && mod.dafRange.first) || "2a")
    .replace(/ עמוד.*/, "");
  const coreLines = (featured && featured.heroSugya && (featured.heroSugya.lines || [])
    .filter(l => l.he).slice(0, 4)) || [];
  const rashiLines = (featured && featured.daf && (featured.daf.rashiLines || [])
    .filter(r => r.he).slice(0, 8)) || [];
  const firstStep = featured && featured.heroSugya && featured.heroSugya.argumentFlow &&
    featured.heroSugya.argumentFlow[0];
  const stepMeta = firstStep && (STEP_META[firstStep.type] || STEP_META.question);
  const hot = coreLines.length > 2 ? 2 : 0;

  return (
    <div
      className="living-daf-stage"
      ref={stageRef}
      onPointerMove={onPointerMove}
      onPointerLeave={onLeave}
      onClick={needsTap ? enableMotion : undefined}
      role="img"
      aria-label="Interactive Talmud folio"
    >
      <div className="living-daf" style={folioStyle} data-live={coreLines.length ? "1" : "0"}>
        <div className="ld-aura" aria-hidden="true" />
        <div className="ld-folio">
          <div className="ld-head">
            <span className="ld-head-he" lang="he" dir="rtl">{titleHe}</span>
            <span className="ld-head-ref" lang="he" dir="rtl">{refHe}</span>
          </div>
          <div className="ld-body">
            <div className="ld-col ld-col-side ld-col-rashi">
              <span className="ld-col-tag" lang="he" dir="rtl">רש״י</span>
              {rashiLines.length ? (
                rashiLines.map((r, i) => (
                  <span className="ld-microline" lang="he" dir="rtl" key={r.id || i}>{r.he}</span>
                ))
              ) : (
                ["92%","78%","85%","64%","80%","70%"].map((w, i) => (
                  <span className="ld-bar" style={{ width: w }} key={i} aria-hidden="true" />
                ))
              )}
            </div>
            <div className="ld-col ld-col-core">
              {coreLines.length ? (
                coreLines.map((l, i) => (
                  <p className={"ld-line" + (i === hot ? " ld-line-hot" : "")} lang="he" dir="rtl" key={l.id || i}>{l.he}</p>
                ))
              ) : (
                ["96%","88%","92%","72%"].map((w, i) => (
                  <span className="ld-bar ld-bar-core" style={{ width: w }} key={i} aria-hidden="true" />
                ))
              )}
              {stepMeta ? (
                <span className="ld-core-tag" lang="he" dir="rtl">{stepMeta.he} · {stepMeta.en}</span>
              ) : null}
            </div>
            <div className="ld-col ld-col-side" aria-hidden="true">
              <span className="ld-col-tag" lang="he" dir="rtl">תוס׳</span>
              {["80%","88%","66%","82%","74%","90%"].map((w, i) => (
                <span className="ld-bar" style={{ width: w }} key={i} />
              ))}
            </div>
          </div>
        </div>
        <div className="ld-sheen" style={sheenStyle} aria-hidden="true" />
      </div>
      <span className="ld-hint">
        {needsTap ? "Tap to bring it to life" : "Move to explore the daf"}
      </span>
    </div>
  );
}

// ============================================================================
// LANDING DATA — generic module-data loading + derivation (no Yoma specifics)
// ============================================================================

// Generate the amud sequence (2a, 2b, 3a ...) from a module's daf range.
function genAmudim(first, last) {
  const parse = s => { const m = String(s || "").match(/^(\d+)([ab])$/); return m ? [parseInt(m[1], 10), m[2]] : null; };
  const a = parse(first), b = parse(last);
  if (!a || !b) return [];
  const out = [];
  let n = a[0], l = a[1], guard = 0;
  while (guard++ < 2000) {
    out.push(n + l);
    if (n === b[0] && l === b[1]) break;
    if (l === "a") l = "b"; else { l = "a"; n++; }
    if (n > b[0] + 1) break;
  }
  return out;
}

// Lazy-load a module's data script once; resolves when its globals are live.
function loadModuleData(mod) {
  return new Promise((resolve, reject) => {
    if (!mod || !mod.id || typeof mod.dataScript !== "string" || !mod.dataScript) {
      reject(new Error("loadModuleData: invalid module descriptor"));
      return;
    }
    const sel = 'script[data-mod-data="' + mod.id + '"]';
    const existing = document.querySelector(sel);
    if (existing) {
      if (existing.getAttribute("data-loaded")) resolve();
      else {
        existing.addEventListener("load", () => resolve());
        existing.addEventListener("error", () => reject(new Error("Module script failed to load: " + mod.dataScript)));
      }
      return;
    }
    const s = document.createElement("script");
    s.src = mod.dataScript + "?v=" + (mod.dataVersion || "1");
    s.setAttribute("data-mod-data", mod.id);
    s.onload = () => { s.setAttribute("data-loaded", "1"); resolve(); };
    s.onerror = () => reject(new Error("Module script failed to load: " + mod.dataScript));
    document.head.appendChild(s);
  });
}

// Read the module globals defined by a loaded data script.
function readModuleGlobals() {
  return {
    meta:       typeof TRACTATE_META !== "undefined" ? TRACTATE_META : null,
    perakim:    typeof PERAKIM       !== "undefined" ? PERAKIM       : null,
    dafIndex:   typeof DAF_INDEX     !== "undefined" ? DAF_INDEX     : null,
    dafContent: typeof DAF_CONTENT   !== "undefined" ? DAF_CONTENT   : null,
  };
}

// Pick the daf of the day deterministically, plus useful sample sugyot.
function deriveFeatured(g) {
  if (!g || !g.dafContent || !g.meta) return null;
  const dc = g.dafContent;
  const enriched = (g.meta.fullyStructured && g.meta.fullyStructured.length
    ? g.meta.fullyStructured
    : Object.keys(dc)).filter(id => dc[id] && dc[id].sugyot && dc[id].sugyot.length);
  if (!enriched.length) return null;
  const epochDay = Math.floor(Date.now() / 86400000);
  const dafId = enriched[epochDay % enriched.length];
  const daf = dc[dafId];
  const sugyot = daf.sugyot || [];
  const heroSugya = sugyot.find(s => (s.lines || []).some(l => l.he)) || sugyot[0] || null;
  const flowSugya = sugyot.find(s => s.argumentFlow && s.argumentFlow.length >= 3) || heroSugya;
  // generic corpus counts
  let sugyaCount = 0, rashiCount = 0;
  for (const id of Object.keys(dc)) {
    const d = dc[id];
    if (d.sugyot) sugyaCount += d.sugyot.length;
    if (d.rashiLines) rashiCount += d.rashiLines.length;
  }
  return { dafId, daf, heroSugya, flowSugya, meta: g.meta, sugyaCount, rashiCount, enrichedCount: enriched.length };
}

// ----- Command bar: jump to any daf in any tractate -----------------------
function CommandBar({ open, onClose }) {
  const [q, setQ] = useState("");
  const [sel, setSel] = useState(0);
  const inputRef = useRef(null);
  const panelRef = useRef(null);
  const prevFocusRef = useRef(null);

  const entries = useMemo(() => {
    const list = [];
    MYSUGYA_MANIFEST.forEach(mod => {
      genAmudim(mod.dafRange.first, mod.dafRange.last).forEach(daf => {
        list.push({ mod, daf, label: mod.title + " " + daf, he: mod.title_he });
      });
    });
    return list;
  }, []);

  const results = useMemo(() => {
    const term = q.trim().toLowerCase();
    if (!term) return entries.slice(0, 8);
    const toks = term.split(/\s+/);
    return entries.filter(e => {
      const hay = (e.mod.title + " " + e.daf + " " + e.mod.id).toLowerCase();
      return toks.every(t => hay.includes(t));
    }).slice(0, 8);
  }, [q, entries]);

  useEffect(() => { setSel(0); }, [q]);
  useEffect(() => { if (open && inputRef.current) inputRef.current.focus(); }, [open]);

  useEffect(() => {
    if (!open) return;
    prevFocusRef.current = document.activeElement;
    return () => { prevFocusRef.current?.focus?.(); };
  }, [open]);

  const go = (e) => { if (e) window.location.href = "?module=" + e.mod.id + "&daf=" + e.daf; };
  const onKey = (ev) => {
    if (ev.key === "Escape") { onClose(); }
    else if (ev.key === "ArrowDown") { ev.preventDefault(); setSel(s => Math.min(results.length - 1, s + 1)); }
    else if (ev.key === "ArrowUp") { ev.preventDefault(); setSel(s => Math.max(0, s - 1)); }
    else if (ev.key === "Enter") { ev.preventDefault(); go(results[sel]); }
    else if (ev.key === "Tab") {
      const focusable = panelRef.current?.querySelectorAll(
        'button:not([disabled]),input:not([disabled]),[tabindex]:not([tabindex="-1"])'
      );
      if (!focusable?.length) { ev.preventDefault(); return; }
      const first = focusable[0], last = focusable[focusable.length - 1];
      if (ev.shiftKey) {
        if (document.activeElement === first) { ev.preventDefault(); last.focus(); }
      } else {
        if (document.activeElement === last) { ev.preventDefault(); first.focus(); }
      }
    }
  };

  if (!open) return null;
  return (
    <div className="cmd-overlay" onClick={onClose}>
      <div ref={panelRef} className="cmd-panel" onClick={e => e.stopPropagation()} role="dialog" aria-label="Jump to a daf">
        <div className="cmd-input-row">
          <span className="cmd-icon" aria-hidden="true">⌕</span>
          <input
            ref={inputRef}
            className="cmd-input"
            placeholder="Jump to any daf -  try &quot;Yoma 28b&quot;"
            value={q}
            onChange={e => setQ(e.target.value)}
            onKeyDown={onKey}
            aria-label="Search for a daf"
          />
          <kbd className="cmd-kbd">esc</kbd>
        </div>
        <ul className="cmd-list">
          {results.length ? results.map((e, i) => (
            <li key={e.mod.id + e.daf}>
              <button
                type="button"
                className="cmd-item"
                data-sel={i === sel ? "1" : "0"}
                onMouseEnter={() => setSel(i)}
                onClick={() => go(e)}
              >
                <span className="cmd-item-he" lang="he" dir="rtl">{e.he}</span>
                <span className="cmd-item-main">{e.mod.title} <strong>{e.daf}</strong></span>
                <span className="cmd-item-go" aria-hidden="true">↵</span>
              </button>
            </li>
          )) : (
            <li className="cmd-empty">No daf matches "{q}"</li>
          )}
        </ul>
      </div>
    </div>
  );
}

// ----- Daf of the Day -----------------------------------------------------
function DafOfDay({ featured }) {
  if (!featured) {
    return (
      <div className="dotd-card dotd-skeleton" aria-hidden="true">
        <div className="dotd-skel-line" style={{ width: "40%" }} />
        <div className="dotd-skel-line" style={{ width: "75%" }} />
        <div className="dotd-skel-line" style={{ width: "60%" }} />
      </div>
    );
  }
  const { meta, dafId, daf, heroSugya } = featured;
  const sugya = heroSugya || (daf.sugyot && daf.sugyot[0]);
  const title = (sugya && sugya.display && sugya.display.title) || (daf.summary || "").slice(0, 60);
  const oneLine = (sugya && sugya.display && (sugya.display.oneLine || sugya.display.whats)) || daf.summary || "";
  const teaserHe = sugya && (sugya.lines || []).find(l => l.he);
  const stepCount = (sugya && sugya.argumentFlow && sugya.argumentFlow.length) || 0;
  const url = "?module=" + meta.id + "&daf=" + dafId;
  return (
    <a className="dotd-card" href={url}>
      <div className="dotd-ribbon">
        <span className="dotd-kicker">Daf of the day</span>
        <span className="dotd-ref">{meta.title} {dafId}<span className="dotd-ref-he" lang="he" dir="rtl">{hebrewizeDaf(dafId)}</span></span>
      </div>
      <div className="dotd-body">
        <h3 className="dotd-title">{title}</h3>
        {teaserHe ? <p className="dotd-teaser" lang="he" dir="rtl">{teaserHe.he}</p> : null}
        <p className="dotd-oneline">{oneLine}</p>
      </div>
      <div className="dotd-foot">
        {stepCount ? <span className="dotd-meta">{stepCount} argument steps</span> : <span className="dotd-meta">{(daf.sugyot || []).length} sugyot</span>}
        <span className="dotd-cta">Study this daf <span aria-hidden="true">→</span></span>
      </div>
    </a>
  );
}

// ----- Peek inside: scroll-driven layer reveal of a real sugya ------------
const PEEK_STAGES = ["Hebrew", "English", "Rashi", "Argument"];
function PeekInside({ featured }) {
  const sectionRef = useRef(null);
  const [stage, setStage] = useState(0);
  useEffect(() => {
    const el = sectionRef.current;
    if (!el) return;
    let raf = 0;
    const onScroll = () => {
      if (raf) return;
      raf = requestAnimationFrame(() => {
        raf = 0;
        const r = el.getBoundingClientRect();
        const vh = window.innerHeight || 800;
        const total = r.height - vh;
        const progressed = Math.min(1, Math.max(0, -r.top / (total || 1)));
        setStage(Math.min(PEEK_STAGES.length - 1, Math.floor(progressed * PEEK_STAGES.length * 0.999)));
      });
    };
    window.addEventListener("scroll", onScroll, { passive: true });
    onScroll();
    return () => window.removeEventListener("scroll", onScroll);
  }, [featured]);

  const sugya = featured && featured.heroSugya;
  const lines = sugya ? (sugya.lines || []).filter(l => l.he).slice(0, 3) : [];
  const rashi = featured && featured.daf && (featured.daf.rashiLines || []).find(r => r.he);
  const steps = sugya && sugya.argumentFlow ? sugya.argumentFlow.slice(0, 4) : [];

  return (
    <section className="peek" ref={sectionRef}>
      <div className="peek-sticky">
        <div className="peek-head">
          <p className="landing-hero-eyebrow landing-flow-eyebrow">See it in layers</p>
          <h2 className="landing-flow-title">One page, every layer</h2>
          <div className="peek-progress" aria-hidden="true">
            {PEEK_STAGES.map((s, i) => (
              <span className="peek-dot" data-on={i <= stage ? "1" : "0"} key={s}>{s}</span>
            ))}
          </div>
        </div>
        <div className="peek-folio">
          {lines.length ? lines.map((l, i) => (
            <div className="peek-line" key={l.id || i}>
              <p className="peek-he" lang="he" dir="rtl">{l.he}</p>
              <p className="peek-en" data-on={stage >= 1 ? "1" : "0"}>{stripHtml(l.en)}</p>
            </div>
          )) : (
            <p className="peek-placeholder">Loading a real daf...</p>
          )}
          {rashi ? (
            <div className="peek-rashi" data-on={stage >= 2 ? "1" : "0"}>
              <span className="peek-tag" lang="he" dir="rtl">רש״י</span>
              <p className="peek-rashi-he" lang="he" dir="rtl">{rashi.he}</p>
              {rashi.en ? <p className="peek-rashi-en">{stripHtml(rashi.en)}</p> : null}
            </div>
          ) : null}
          {steps.length ? (
            <div className="peek-args" data-on={stage >= 3 ? "1" : "0"}>
              {steps.map((s, i) => {
                const m = STEP_META[s.type] || STEP_META.question;
                return <span className="peek-arg" key={s.id || i}><span aria-hidden="true">{m.sym}</span> {m.en}</span>;
              })}
            </div>
          ) : null}
        </div>
        <p className="peek-hint">Scroll to peel back the layers</p>
      </div>
    </section>
  );
}

// ----- Continue your journey (returning visitors only) --------------------
function ContinueJourney() {
  const started = useMemo(() => {
    let best = null;
    MYSUGYA_MANIFEST.forEach(mod => {
      const last = LS.get(mod.id + ":lastDaf", null);
      const completed = LS.get(mod.id + ":completed", []);
      const begun = last && last !== "1a" && last !== mod.dafRange.first;
      if (begun || (completed && completed.length)) {
        const pct = mod.totalDaf ? Math.round((completed.length / mod.totalDaf) * 100) : 0;
        if (!best || completed.length > best.completed) best = { mod, last, completed: completed.length, pct };
      }
    });
    return best;
  }, []);
  if (!started) return null;
  const { mod, last, completed, pct } = started;
  return (
    <section className="journey">
      <a className="journey-card" href={"?module=" + mod.id}>
        <div className="journey-ring" style={{ "--pct": pct }}>
          <span className="journey-ring-num">{pct}<small>%</small></span>
        </div>
        <div className="journey-text">
          <span className="journey-kicker">Welcome back</span>
          <span className="journey-title">Continue {mod.title}</span>
          <span className="journey-sub">
            {last ? <>Last at daf {last}<span lang="he" dir="rtl"> · {hebrewizeDaf(last)}</span></> : null}
            {completed ? " · " + completed + " complete" : ""}
          </span>
        </div>
        <span className="journey-cta" aria-hidden="true">→</span>
      </a>
    </section>
  );
}

// ----- Map of Shas: every Bavli masechta, lit up as it goes live ----------
const SHAS = [
  { seder: "Zeraim",   he: "זְרָעִים",  masechtot: [["Berakhot","berakhot"]] },
  { seder: "Moed",     he: "מוֹעֵד",   masechtot: [["Shabbat","shabbat"],["Eruvin","eruvin"],["Pesachim","pesachim"],["Rosh Hashanah","rosh-hashanah"],["Yoma","yoma"],["Sukkah","sukkah"],["Beitzah","beitzah"],["Taanit","taanit"],["Megillah","megillah"],["Moed Katan","moed-katan"],["Chagigah","chagigah"]] },
  { seder: "Nashim",   he: "נָשִׁים",  masechtot: [["Yevamot","yevamot"],["Ketubot","ketubot"],["Nedarim","nedarim"],["Nazir","nazir"],["Sotah","sotah"],["Gittin","gittin"],["Kiddushin","kiddushin"]] },
  { seder: "Nezikin",  he: "נְזִיקִין", masechtot: [["Bava Kamma","bava-kamma"],["Bava Metzia","bava-metzia"],["Bava Batra","bava-batra"],["Sanhedrin","sanhedrin"],["Makkot","makkot"],["Shevuot","shevuot"],["Avodah Zarah","avodah-zarah"],["Horayot","horayot"]] },
  { seder: "Kodashim", he: "קֳדָשִׁים", masechtot: [["Zevachim","zevachim"],["Menachot","menachot"],["Chullin","chullin"],["Bekhorot","bekhorot"],["Arakhin","arakhin"],["Temurah","temurah"],["Keritot","keritot"],["Meilah","meilah"],["Tamid","tamid"]] },
  { seder: "Taharot",  he: "טָהֳרוֹת",  masechtot: [["Niddah","niddah"]] },
];
function ShasMap() {
  const liveById = useMemo(() => {
    const m = {};
    MYSUGYA_MANIFEST.forEach(mod => { m[mod.id] = mod; });
    return m;
  }, []);
  const liveCount = MYSUGYA_MANIFEST.length;
  const total = SHAS.reduce((a, s) => a + s.masechtot.length, 0);
  return (
    <div className="shas">
      <div className="shas-legend">
        <span className="shas-legend-item"><span className="shas-swatch shas-swatch-live" />{liveCount} live</span>
        <span className="shas-legend-item"><span className="shas-swatch" />{total - liveCount} coming</span>
      </div>
      <div className="shas-sedarim">
        {SHAS.map(s => (
          <div className="shas-seder" key={s.seder}>
            <div className="shas-seder-head">
              <span className="shas-seder-en">{s.seder}</span>
              <span className="shas-seder-he" lang="he" dir="rtl">{s.he}</span>
            </div>
            <div className="shas-cells">
              {s.masechtot.map(([name, slug]) => {
                const live = liveById[slug];
                return live ? (
                  <a className="shas-cell shas-cell-live" key={slug} href={"?module=" + slug} title={name}>
                    <span className="shas-cell-he" lang="he" dir="rtl">{live.title_he}</span>
                    <span className="shas-cell-en">{name}</span>
                  </a>
                ) : (
                  <span className="shas-cell" key={slug} title={name + " - coming soon"}>
                    <span className="shas-cell-en">{name}</span>
                  </span>
                );
              })}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}

function TractateCard({ mod }) {
  const seder = SEDER_LABELS[mod.seder] || { he: mod.seder, en: mod.seder };
  const url = "?module=" + mod.id;
  const completed = LS.get(mod.id + ":completed", []);
  const lastDaf = LS.get(mod.id + ":lastDaf", null);
  const total = mod.totalDaf || 0;
  const pct = total ? Math.min(100, Math.round((completed.length / total) * 100)) : 0;
  const started = !!lastDaf && lastDaf !== "1a" && lastDaf !== mod.dafRange.first;
  return (
    <a className="tractate-card" href={url} aria-label={"Study " + mod.title}>
      <div className="tc-header">
        <span className="tc-seder-badge">
          <span lang="he" dir="rtl">{seder.he}</span>
          {" · "}{mod.seder}
        </span>
        <span className="tc-live"><span className="tc-live-dot" aria-hidden="true" />Live</span>
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
      </div>
      {pct > 0 && (
        <div className="tc-progress" aria-label={pct + "% complete"}>
          <span className="tc-progress-bar"><span className="tc-progress-fill" style={{ width: pct + "%" }} /></span>
          <span className="tc-progress-label">{pct}%</span>
        </div>
      )}
      <div className="tc-footer">
        <span className="tc-cta">
          {started ? "Resume daf " + lastDaf : "Begin studying"}
          {" "}<span aria-hidden="true">→</span>
        </span>
      </div>
    </a>
  );
}

// ----- Help overlay: how to use the app + beta status ---------------------
function HelpOverlay({ open, onClose }) {
  const panelRef = useRef(null);
  const prevFocusRef = useRef(null);

  useEffect(() => {
    if (!open) return;
    prevFocusRef.current = document.activeElement;
    const onKey = (e) => {
      if (e.key === "Escape") { onClose(); return; }
      if (e.key === "Tab") {
        const focusable = panelRef.current?.querySelectorAll(
          'button:not([disabled]),input:not([disabled]),[tabindex]:not([tabindex="-1"])'
        );
        if (!focusable?.length) { e.preventDefault(); return; }
        const first = focusable[0], last = focusable[focusable.length - 1];
        if (e.shiftKey) {
          if (document.activeElement === first) { e.preventDefault(); last.focus(); }
        } else {
          if (document.activeElement === last) { e.preventDefault(); first.focus(); }
        }
      }
    };
    window.addEventListener("keydown", onKey);
    return () => {
      window.removeEventListener("keydown", onKey);
      prevFocusRef.current?.focus?.();
    };
  }, [open, onClose]);
  if (!open) return null;
  return (
    <div className="help-overlay" onClick={onClose}>
      <div ref={panelRef} className="help-panel" onClick={e => e.stopPropagation()} role="dialog" aria-modal="true" aria-label="How to use My Sugya">
        <div className="help-head">
          <h2 className="help-title">How to use My Sugya</h2>
          <button type="button" className="help-close" onClick={onClose} aria-label="Close help">×</button>
        </div>
        <span className="help-beta-pill">Open beta · work in progress</span>
        <p className="help-lead">
          A free Talmud study companion, in active development. Yoma is complete;
          more masechtot are being added over time.
        </p>
        <ul className="help-list">
          <li><strong>Pick a masechta</strong> from the home page, or press <kbd>/</kbd> to jump straight to any daf.</li>
          <li><strong>Read side by side.</strong> Hebrew with nekudot and elucidated English, Rashi shown inline with the gemara.</li>
          <li><strong>Follow the argument.</strong> Each sugya is mapped into its moves - question, proof, objection, resolution.</li>
          <li><strong>Track your place.</strong> Bookmark, mark complete, and resume where you left off - saved on your device.</li>
          <li><strong>Tune the page.</strong> Open Tweaks inside a daf for theme, font sizes, and reading aids.</li>
        </ul>
        <p className="help-foot">
          Because this is an early release, some daf are still being enriched and details may change.
          Feedback is always welcome.
        </p>
      </div>
    </div>
  );
}

function LandingPage() {
  const firstMod = MYSUGYA_MANIFEST[0];
  const startUrl = firstMod ? "?module=" + firstMod.id : "#tractates";
  const startName = firstMod ? firstMod.title : "Yoma";
  const amudimTotal = MYSUGYA_MANIFEST.reduce((a, m) => a + (m.totalDaf || 0), 0);
  const liveCount = MYSUGYA_MANIFEST.length;
  const shasTotal = SHAS.reduce((a, s) => a + s.masechtot.length, 0);

  const [data, setData] = useState(null);
  const [cmdOpen, setCmdOpen] = useState(false);
  const [helpOpen, setHelpOpen] = useState(false);
  const featured = useMemo(() => deriveFeatured(data), [data]);

  // Lazy-load the featured module's data after the hero paints, then enrich.
  useEffect(() => {
    if (!firstMod) return;
    let alive = true;
    const run = () => loadModuleData(firstMod).then(() => { if (alive) setData(readModuleGlobals()); }).catch((err) => { console.warn("[MySugya] preview load failed:", err && err.message || err); });
    const ric = window.requestIdleCallback;
    let h;
    if (ric) h = ric(run, { timeout: 2500 }); else h = setTimeout(run, 1200);
    return () => { alive = false; if (ric && window.cancelIdleCallback) window.cancelIdleCallback(h); else clearTimeout(h); };
  }, [firstMod]);

  // "/" opens the command bar (jump to any daf).
  useEffect(() => {
    const onKey = (e) => {
      const tag = (e.target && e.target.tagName) || "";
      if (e.key === "/" && !/input|textarea/i.test(tag)) { e.preventDefault(); setCmdOpen(true); }
    };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, []);

  return (
    <div className="landing">
      <div className="landing-aurora" aria-hidden="true" />

      <header className="landing-chrome">
        <div className="brand">
          <Logo className="brand-logo" />
          <span className="brand-name">My Sugya</span>
          <span className="brand-beta">BETA</span>
        </div>
        <nav className="landing-nav">
          <a className="landing-nav-link" href="#how">
            <span className="landing-nav-ic" aria-hidden="true">✦</span>
            <span className="landing-nav-label">Features</span>
          </a>
          <button type="button" className="landing-nav-link" onClick={() => setHelpOpen(true)}>
            <span className="landing-nav-ic" aria-hidden="true">?</span>
            <span className="landing-nav-label">Help</span>
          </button>
          <button type="button" className="chrome-jump" onClick={() => setCmdOpen(true)}>
            <span aria-hidden="true">⌕</span> <span className="chrome-jump-label">Jump to a daf</span> <kbd>/</kbd>
          </button>
        </nav>
      </header>

      {/* HERO */}
      <section className="landing-hero">
        <Reveal className="landing-hero-inner">
          <p className="landing-hero-eyebrow">Talmud, reimagined for how you actually learn</p>
          <h1 className="landing-hero-title">
            Understand the Gemara.
            <span className="lht-he" lang="he" dir="rtl">הַגְּמָרָא</span>
          </h1>
          <p className="landing-hero-sub">
            Every daf, mapped sugya by sugya. Hebrew and English side by side,
            Rashi inline, the argument laid bare. Free, in your browser.
          </p>
          <div className="landing-cta-row">
            <a className="lcta lcta-primary" href={startUrl}>
              Begin with {startName} <span aria-hidden="true">→</span>
            </a>
            <a className="lcta lcta-ghost" href="#how">See how it works <span aria-hidden="true">→</span></a>
          </div>
          <button type="button" className="cmd-trigger" onClick={() => setCmdOpen(true)}>
            <span className="cmd-trigger-icon" aria-hidden="true">⌕</span>
            <span className="cmd-trigger-text">Jump to any daf in any tractate</span>
            <kbd className="cmd-trigger-kbd">/</kbd>
          </button>
          <div className="landing-stats-grid">
            <CountUpStat value={amudimTotal} label="amudim" />
            <CountUpStat value={featured ? featured.sugyaCount : 0} label="sugyot" />
            <CountUpStat value={featured ? featured.rashiCount : 0} label="Rashi lines" />
            <CountUpStat value={liveCount} label={"of " + shasTotal + " masechtot"} />
          </div>
          <p className="landing-beta-note">
            <span className="lbn-pill">Beta</span>
            Yoma is complete and live. More masechtot are being added - this is an
            early, evolving release.
            <button type="button" className="lbn-link" onClick={() => setHelpOpen(true)}>
              How it works
            </button>
          </p>
        </Reveal>

        <Reveal className="landing-hero-deco" delay={160}>
          <LivingDaf featured={featured} mod={firstMod} />
        </Reveal>
      </section>

      {/* CONTINUE (returning visitors only) */}
      <ContinueJourney />

      {/* DAF OF THE DAY */}
      <section className="landing-daily">
        <Reveal className="landing-section-inner landing-daily-inner">
          <DafOfDay featured={featured} />
        </Reveal>
      </section>

      {/* SIGNATURE FEATURE — argument flow from a real sugya */}
      <section className="landing-flow">
        <Reveal className="landing-section-inner landing-flow-inner">
          <p className="landing-hero-eyebrow landing-flow-eyebrow">The signature view</p>
          <h2 className="landing-flow-title">Every sugya, mapped as an argument</h2>
          <p className="landing-section-sub landing-flow-sub">
            We label the moves of the Gemara so the logic is visible at a glance -
            question, proof, objection, resolution.
          </p>
          <ArgumentFlowDemo
            steps={featured && featured.flowSugya ? featured.flowSugya.argumentFlow : null}
            sugyaTitle={featured && featured.flowSugya
              ? featured.meta.title + " " + featured.dafId +
                (featured.flowSugya.display && featured.flowSugya.display.title
                  ? " · " + featured.flowSugya.display.title : "")
              : null}
          />
        </Reveal>
      </section>

      {/* PEEK INSIDE — scroll-driven layer reveal of a real daf */}
      <PeekInside featured={featured} />

      {/* TRACTATE PICKER */}
      <section className="landing-tractates" id="tractates">
        <Reveal className="landing-section-inner">
          <h2 className="landing-section-title">
            Choose a Masechta
            <span className="lst-he" lang="he" dir="rtl">בְּחַר מַסֶּכֶת</span>
          </h2>
          <p className="landing-section-sub">Pick a tractate and dive in. More are on the way.</p>
          <div className="tractate-grid">
            {MYSUGYA_MANIFEST.map(mod => <TractateCard key={mod.id} mod={mod}/>)}
            <a className="tractate-card tc-more" href="#shas">
              <div className="tc-header">
                <span className="tc-seder-badge">The whole Shas</span>
              </div>
              <div className="tc-body tc-more-body">
                <span className="tc-more-num">{shasTotal - liveCount}</span>
                <span className="tc-more-label">more masechtot in preparation</span>
              </div>
              <div className="tc-footer">
                <span className="tc-cta tc-cta--mute">See the map <span aria-hidden="true">↓</span></span>
              </div>
            </a>
          </div>
        </Reveal>
      </section>

      {/* MAP OF SHAS */}
      <section className="landing-shas" id="shas">
        <Reveal className="landing-section-inner">
          <h2 className="landing-section-title landing-section-title--center">The whole Shas, lighting up</h2>
          <p className="landing-section-sub landing-section-sub--center">
            Every masechta of the Talmud Bavli. The lit ones are ready now; the rest arrive over time.
          </p>
          <ShasMap />
        </Reveal>
      </section>

      {/* FEATURES */}
      <section className="landing-how" id="how">
        <Reveal className="landing-section-inner">
          <h2 className="landing-section-title landing-section-title--center">Everything you need on the page</h2>
          <div className="landing-features">
            {[
              { ic: "§",   he: false, t: "Sugya structure",            d: "Each daf split into labeled discussion units. Navigate by topic, not just by line." },
              { ic: "א",   he: false, t: "Interlinear Hebrew-English", d: "Full nekudot with Sefaria-sourced English. Toggle vowel marks anytime." },
              { ic: "↯",   he: false, t: "Argument flow",              d: "Question, proof, objection, resolution - mapped for every sugya." },
              { ic: "רש\"י", he: true, t: "Rashi commentary",          d: "All Rashi lines, shown inline with the gemara, with Vilna references and English helpers." },
              { ic: "מ",   he: false, t: "Glossary per daf",           d: "Aramaic and Hebrew key terms defined in context, in plain language." },
              { ic: "★",   he: false, t: "Progress tracking",          d: "Bookmark, mark complete, and resume exactly where you left off - stored on your device." },
            ].map(f => (
              <div className="lf-item" key={f.t}>
                <span className={"lf-icon" + (f.he ? " lf-icon--he" : "")} aria-hidden="true">{f.ic}</span>
                <div className="lf-text">
                  <strong>{f.t}</strong>
                  <p>{f.d}</p>
                </div>
              </div>
            ))}
          </div>
        </Reveal>
      </section>

      {/* CLOSING CTA */}
      <section className="landing-cta-band">
        <Reveal className="landing-section-inner cta-band-inner">
          <h2 className="cta-band-title">Open the daf.</h2>
          <p className="cta-band-sub">No account. No install. Just you and the page.</p>
          <a className="lcta lcta-primary lcta-lg" href={startUrl}>
            Begin with {startName} <span aria-hidden="true">→</span>
          </a>
          <p className="cta-band-quote" lang="he" dir="rtl">הֲפֹךְ בָּהּ וַהֲפֹךְ בָּהּ דְּכֹלָּא בָהּ</p>
          <p className="cta-band-quote-en">"Turn it over and over, for everything is in it." · Avot 5:22</p>
        </Reveal>
      </section>

      <footer className="landing-footer">
        <div className="landing-footer-inner">
          <span className="footer-dedication" lang="he" dir="rtl">לרפואת יעקב בן דינה · לעילוי נשמת אהרן בן יהודה ואהרן בן יוסף</span>
          <span className="lf-version">v{PLATFORM_VERSION}</span>
        </div>
      </footer>

      <CommandBar open={cmdOpen} onClose={() => setCmdOpen(false)} />
      <HelpOverlay open={helpOpen} onClose={() => setHelpOpen(false)} />
    </div>
  );
}

// =============================================================================
// MOUNT — dynamic module loading
// =============================================================================
(function() {
  const qp = new URLSearchParams(window.location.search);
  const moduleId = qp.get("module");

  // The landing is its own light, designed experience. Force the root to a
  // light scheme so a saved dark reading theme cannot bleed behind it.
  // (Entering a module is a full page load, so this never affects the daf view.)
  function renderLanding() {
    const html = document.documentElement;
    html.setAttribute("data-mode", "light");
    html.classList.add("on-landing");
    const meta = document.querySelector('meta[name="color-scheme"]');
    if (meta) meta.content = "light";
    const rootEl = ReactDOM.createRoot(document.getElementById("root"));
    rootEl.render(<LandingPage/>);
  }

  function showRootError(msg) {
    const root = document.getElementById("root");
    const p = document.createElement("p");
    p.style.cssText = "padding:2rem;font-family:sans-serif;color:#c00";
    p.textContent = msg;
    root.replaceChildren(p);
  }

  if (!moduleId) {
    renderLanding();
    return;
  }

  const mod = MYSUGYA_MANIFEST.find(function(m) { return m.id === moduleId; });

  if (!mod) {
    renderLanding();
    return;
  }

  if (typeof mod.dataScript !== "string" || !mod.dataScript) {
    showRootError("Module \"" + mod.id + "\" is missing a dataScript path.");
    return;
  }

  const s = document.createElement("script");
  s.src = mod.dataScript + "?v=" + (mod.dataVersion || "1");
  s.onload = function() {
    if (typeof TRACTATE_META === "undefined" || typeof DAF_CONTENT === "undefined") {
      showRootError("Module \"" + mod.id + "\" loaded but required globals are missing. Check " + mod.dataScript + ".");
      return;
    }
    initEnCache();
    initPerekByN();
    const rootEl = ReactDOM.createRoot(document.getElementById("root"));
    rootEl.render(<App/>);
  };
  s.onerror = function() {
    showRootError("Failed to load module data: " + mod.dataScript);
  };
  document.head.appendChild(s);
})();
