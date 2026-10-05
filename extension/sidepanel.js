"use strict";

// The backend runs on this machine. Keep in sync with host_permissions in manifest.json.
const API_BASE = "http://127.0.0.1:8000";
const REQUEST_TIMEOUT_MS = 90000; // the first request loads the models
const MAX_CHARS = 5000; // matches the API limit
const RECENT_KEY = "infosure.recent";
const LANG_KEY = "infosure.lang";
const MAX_RECENT = 5;

/* ---------- text (English and Tagalog) ---------- */

const I18N = {
  en: {
    tagline: "Health claim check",
    inputLabel: "Claim to check",
    inputPlaceholder: "Highlight a health claim on the page, or paste it here.",
    check: "Check the claim",
    footer:
      "The model gives an estimate, not a verified fact. Always check the sources shown.",
    connOk: "Connected to this page. Highlight text to fill the field.",
    connOff:
      "Cannot read highlights on this page (browser pages, the Web Store, PDFs and local files are blocked). Type or paste the text instead.",
    hintStart:
      "Highlight a health claim on the page. The text appears here as you highlight; then click Check.",
    hintUpdated: "Selection updated. Click Check to verify it.",
    hintTruncated:
      "Only the first {n} characters will be checked. Click Check.",
    checking:
      "Checking… the first check can take a while because the models are loading.",
    welcomeTitle: "Check a health claim",
    welcomeStep1: "Highlight a sentence on any web page.",
    welcomeStep2: "It appears above. Click Check.",
    welcomeStep3: "See the model's verdict, then the evidence.",
    tryExample: "Try an example",
    examples: [
      "Garlic cures cancer.",
      "Washing hands with soap reduces the spread of infections.",
    ],
    recent: "Recent checks",
    clear: "Clear",
    verdictKicker: "Model verdict",
    estimateTag: "Estimate, not verified",
    Reliable: "Reliable",
    Misinformation: "Misinformation",
    subReliable:
      "This looks like reliable health information, based on patterns the model learned.",
    subMisinformation:
      "This looks like health misinformation, based on patterns the model learned.",
    conf: {
      low: "Low confidence",
      medium: "Medium confidence",
      high: "High confidence",
    },
    evidenceTitle: "Evidence check",
    ev: {
      Supported: "Supported",
      Contradicted: "Contradicted",
      "Insufficient Evidence": "Not enough evidence",
    },
    agree: "The model and the evidence agree.",
    conflict:
      "The model and the evidence disagree. Read the sources before you trust either one.",
    none: "No matching evidence in our validated sources. Treat the model's estimate with caution.",
    rel: {
      entailment: "supports claim",
      contradiction: "contradicts claim",
      neutral: "unclear",
    },
    published: "Published {d}",
    dateUnknown: "Date unknown",
    showMore: "Show more",
    showLess: "Show less",
    openSource: "Open source",
    howTitle: "How to read this",
    howModel:
      "<b>Model verdict</b> is a guess from patterns it learned. It does not look anything up, and it can be wrong.",
    howEvidence:
      "<b>Evidence check</b> compares the claim with validated sources. It can only answer when a matching source exists.",
    howConflict:
      "When the two disagree, do not trust either blindly. Open the sources.",
    feedbackQ: "Was this right?",
    Agree: "Yes",
    Disagree: "No",
    Flag: "Flag",
    thanks: "Thanks. Saved for review.",
    copy: "Copy summary",
    copied: "Copied",
    newCheck: "New check",
    scopeOutTitle: "Not a health topic",
    scopeOutText: "InfoSure only checks health-related claims.",
    scopeNoneTitle: "No checkable health claim",
    scopeNoneText: "Opinions, questions and personal feelings are not checked.",
    errorTitle: "Something went wrong",
    retry: "Try again",
    errUnreachable:
      "Cannot reach the InfoSure server at {api}. Start it first (see extension/README.md).",
    errTimeout: "The server took too long to answer.",
    errNotReady:
      "The server is not ready (no model deployed or the evidence index is out of date).",
    errNotImplemented: "Not implemented yet: {d}",
    errRejected:
      "The server rejected this input. The text may be empty or too long.",
    errServer: "Server error ({s}).",
    sumVerdict: "InfoSure: {v} ({c}, model estimate, not verified)",
    sumEvidence: "Evidence: {e}",
    sumClaim: "Claim: {c}",
    sumSources: "Sources:",
  },
  tl: {
    tagline: "Pagsusuri ng claim sa kalusugan",
    inputLabel: "Teksto na susuriin",
    inputPlaceholder:
      "I-highlight ang isang health claim sa page, o i-paste dito.",
    check: "Suriin",
    footer:
      "Tantiya lang ang ibinibigay ng model, hindi napatunayang katotohanan. Laging tingnan ang mga source.",
    connOk:
      "Nakakonekta sa page na ito. I-highlight ang teksto para mapunan ang field.",
    connOff:
      "Hindi mabasa ang mga highlight sa page na ito (bawal ang mga pahina ng browser, Web Store, PDF, at lokal na file). I-type o i-paste na lang ang teksto.",
    hintStart:
      "I-highlight ang isang health claim sa page. Lalabas ang teksto rito habang nagha-highlight ka; pagkatapos ay i-click ang Suriin.",
    hintUpdated: "Napalitan ang napili. I-click ang Suriin.",
    hintTruncated: "Unang {n} character lang ang susuriin. I-click ang Suriin.",
    checking:
      "Sinusuri… maaaring matagalan ang unang pagsusuri dahil nilo-load pa ang mga model.",
    welcomeTitle: "Suriin ang isang health claim",
    welcomeStep1: "Mag-highlight ng pangungusap sa kahit anong web page.",
    welcomeStep2: "Lalabas ito sa itaas. I-click ang Suriin.",
    welcomeStep3: "Makikita ang hatol ng model, at pagkatapos ang ebidensya.",
    tryExample: "Subukan ang halimbawa",
    examples: [
      "Ang bawang ay gamot sa kanser.",
      "Ang pagbabakuna ay nakakaiwas sa tigdas.",
    ],
    recent: "Mga kamakailang pagsusuri",
    clear: "Burahin",
    verdictKicker: "Hatol ng model",
    estimateTag: "Tantiya, hindi pa napatunayan",
    Reliable: "Maaasahan",
    Misinformation: "Maling impormasyon",
    subReliable:
      "Mukhang maaasahang impormasyon ito sa kalusugan, batay sa mga pattern na natutunan ng model.",
    subMisinformation:
      "Mukhang maling impormasyon ito sa kalusugan, batay sa mga pattern na natutunan ng model.",
    conf: {
      low: "Mababang kumpiyansa",
      medium: "Katamtamang kumpiyansa",
      high: "Mataas na kumpiyansa",
    },
    evidenceTitle: "Pagsusuri ng ebidensya",
    ev: {
      Supported: "Sinusuportahan",
      Contradicted: "Sinasalungat",
      "Insufficient Evidence": "Kulang ang ebidensya",
    },
    agree: "Magkasundo ang model at ang ebidensya.",
    conflict:
      "Magkasalungat ang model at ang ebidensya. Basahin ang mga source bago magtiwala sa alinman.",
    none: "Walang tugmang ebidensya sa aming mga napatunayang source. Mag-ingat sa tantiya ng model.",
    rel: {
      entailment: "sumusuporta sa claim",
      contradiction: "sumasalungat sa claim",
      neutral: "hindi malinaw",
    },
    published: "Inilathala noong {d}",
    dateUnknown: "Hindi alam ang petsa",
    showMore: "Ipakita pa",
    showLess: "Ipakita nang mas kaunti",
    openSource: "Buksan ang source",
    howTitle: "Paano basahin ito",
    howModel:
      "Ang <b>hatol ng model</b> ay hula mula sa mga pattern na natutunan nito. Hindi ito naghahanap ng sagot, at maaari itong magkamali.",
    howEvidence:
      "Ang <b>pagsusuri ng ebidensya</b> ay naghahambing ng claim sa mga napatunayang source. May sagot lang ito kapag may tugmang source.",
    howConflict:
      "Kapag magkasalungat ang dalawa, huwag magtiwala nang bulag sa alinman. Buksan ang mga source.",
    feedbackQ: "Tama ba ito?",
    Agree: "Oo",
    Disagree: "Hindi",
    Flag: "I-flag",
    thanks: "Salamat. Naka-save para sa pagsusuri.",
    copy: "Kopyahin ang buod",
    copied: "Nakopya",
    newCheck: "Bagong pagsusuri",
    scopeOutTitle: "Hindi paksang pangkalusugan",
    scopeOutText:
      "Mga claim na may kinalaman sa kalusugan lang ang sinusuri ng InfoSure.",
    scopeNoneTitle: "Walang maisusuring claim sa kalusugan",
    scopeNoneText:
      "Hindi sinusuri ang mga opinyon, tanong, at personal na damdamin.",
    errorTitle: "May nangyaring problema",
    retry: "Subukan ulit",
    errUnreachable:
      "Hindi maabot ang InfoSure server sa {api}. Simulan muna ito (tingnan ang extension/README.md).",
    errTimeout: "Natagalan ang sagot ng server.",
    errNotReady:
      "Hindi pa handa ang server (walang naka-deploy na model o luma na ang evidence index).",
    errNotImplemented: "Hindi pa naipapatupad: {d}",
    errRejected:
      "Tinanggihan ng server ang input. Maaaring walang laman o masyadong mahaba ang teksto.",
    errServer: "May error sa server ({s}).",
    sumVerdict: "InfoSure: {v} ({c}, tantiya ng model, hindi pa napatunayan)",
    sumEvidence: "Ebidensya: {e}",
    sumClaim: "Claim: {c}",
    sumSources: "Mga source:",
  },
};

function storageGet(key) {
  try {
    return localStorage.getItem(key);
  } catch (error) {
    return null;
  }
}
function storageSet(key, value) {
  try {
    localStorage.setItem(key, value);
  } catch (error) {
    /* storage unavailable: keep working without it */
  }
}

let lang = storageGet(LANG_KEY) === "tl" ? "tl" : "en";
const T = () => I18N[lang];
function fmt(text, vars) {
  return text.replace(/\{(\w+)\}/g, (_, k) =>
    vars && k in vars ? vars[k] : "",
  );
}

/* ---------- small DOM helpers (page text, claims and evidence are untrusted: textContent only) ---------- */

const els = {
  text: document.getElementById("text"),
  check: document.getElementById("check"),
  status: document.getElementById("status"),
  result: document.getElementById("result"),
  connection: document.getElementById("connection"),
};

function el(tag, className, text) {
  const node = document.createElement(tag);
  if (className) node.className = className;
  if (text !== undefined) node.textContent = text;
  return node;
}

const ICONS = {
  good: ["M12 3l7 3v5c0 5-3.5 8.5-7 10-3.5-1.5-7-5-7-10V6z", "M9 12l2 2 4-4"],
  bad: [
    "M12 3l7 3v5c0 5-3.5 8.5-7 10-3.5-1.5-7-5-7-10V6z",
    "M12 8v5",
    "M12 16.5v.01",
  ],
  question: [
    "M12 3l7 3v5c0 5-3.5 8.5-7 10-3.5-1.5-7-5-7-10V6z",
    "M9.7 9.7a2.4 2.4 0 014.6.8c0 1.5-2.3 1.8-2.3 3.2",
    "M12 16.7v.01",
  ],
  info: ["M12 21a9 9 0 100-18 9 9 0 000 18z", "M12 11v5", "M12 7.5v.01"],
  warn: ["M12 3l10 18H2z", "M12 10v5", "M12 18v.01"],
  check: ["M5 12l5 5 9-10"],
  copy: ["M9 9h11v11H9z", "M5 15V4h11"],
  link: ["M14 4h6v6", "M10 14L20 4", "M20 14v6H4V4h6"],
  chevron: ["M6 9l6 6 6-6"],
  retry: ["M20 12a8 8 0 11-2.5-5.8", "M20 4v5h-5"],
  book: ["M4 5a2 2 0 012-2h13v16H6a2 2 0 00-2 2z", "M4 19V5"],
  up: ["M7 10v11", "M15 5.9L14 10h5.8a2 2 0 011.9 2.6l-2.3 8A2 2 0 0117.5 22H4a2 2 0 01-2-2v-8a2 2 0 012-2h2.8a2 2 0 001.8-1.1L12 2a3.1 3.1 0 013 3.9z"],
  flag: ["M4 22V4", "M4 4h13l-2.5 4L17 12H4"],
};
function icon(name) {
  const svg = document.createElementNS("http://www.w3.org/2000/svg", "svg");
  svg.setAttribute("viewBox", "0 0 24 24");
  svg.setAttribute("aria-hidden", "true");
  for (const d of ICONS[name]) {
    const path = document.createElementNS("http://www.w3.org/2000/svg", "path");
    path.setAttribute("d", d);
    svg.append(path);
  }
  return svg;
}

// Basic markup (<b>) only for our own fixed strings above, never for page or server text.
function richText(container, html) {
  for (const part of html.split(/(<b>.*?<\/b>)/)) {
    if (!part) continue;
    if (part.startsWith("<b>"))
      container.append(el("b", "", part.slice(3, -4)));
    else container.append(document.createTextNode(part));
  }
}

/* ---------- static text, language switch ---------- */

function applyStaticText() {
  document.documentElement.lang = lang;
  for (const node of document.querySelectorAll("[data-i18n]"))
    node.textContent = T()[node.dataset.i18n];
  for (const node of document.querySelectorAll("[data-i18n-placeholder]"))
    node.placeholder = T()[node.dataset.i18nPlaceholder];
  for (const button of document.querySelectorAll(".lang button"))
    button.setAttribute("aria-pressed", String(button.dataset.lang === lang));
}

function setLang(next) {
  lang = next;
  storageSet(LANG_KEY, next);
  applyStaticText();
  renderConnection();
  rerender();
}
for (const button of document.querySelectorAll(".lang button"))
  button.addEventListener("click", () => setLang(button.dataset.lang));

/* ---------- status line and connection ---------- */

let statusState = null; // { key, vars, error } so the message follows the language
function setStatus(key, vars, error) {
  statusState = key ? { key, vars, error: !!error } : null;
  renderStatus();
}
function renderStatus() {
  els.status.hidden = !statusState;
  els.status.className = statusState && statusState.error ? "error" : "";
  els.status.textContent = statusState
    ? statusState.raw || fmt(T()[statusState.key], statusState.vars)
    : "";
}

let connState = null; // "ok" | "off" | null
function renderConnection() {
  els.connection.className = "conn" + (connState ? " " + connState : "");
  els.connection.textContent =
    connState === "ok" ? T().connOk : connState === "off" ? T().connOff : "";
}

/* ---------- API ---------- */

class ApiError extends Error {
  constructor(status, detail) {
    super(detail);
    this.status = status;
  }
}

async function postJson(path, body) {
  const controller = new AbortController();
  const timer = setTimeout(() => controller.abort(), REQUEST_TIMEOUT_MS);
  try {
    const response = await fetch(API_BASE + path, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
      signal: controller.signal,
    });
    const data = await response.json().catch(() => ({}));
    if (!response.ok)
      throw new ApiError(
        response.status,
        typeof data.detail === "string" ? data.detail : "",
      );
    return data;
  } finally {
    clearTimeout(timer);
  }
}

function describeError(error) {
  const t = T();
  if (error instanceof ApiError) {
    if (error.status === 503) return error.message || t.errNotReady;
    if (error.status === 501)
      return fmt(t.errNotImplemented, { d: error.message });
    if (error.status === 422) return t.errRejected;
    return `${fmt(t.errServer, { s: error.status })} ${error.message}`.trim();
  }
  if (error && error.name === "AbortError") return t.errTimeout;
  return fmt(t.errUnreachable, { api: API_BASE });
}

/* ---------- reading the page selection ---------- */

async function activeTab() {
  const [tab] = await chrome.tabs.query({
    active: true,
    lastFocusedWindow: true,
  });
  return tab && tab.id !== undefined ? tab : null;
}

// Is the page script listening in this tab? Pages opened before the extension was loaded have none, so inject it
// once and ask again. Restricted pages (chrome://, the Web Store, PDFs, file:// without permission) cannot be read.
async function ping(tabId) {
  try {
    const reply = await chrome.tabs.sendMessage(
      tabId,
      { type: "infosure-ping" },
      { frameId: 0 },
    );
    return !!(reply && reply.ok);
  } catch (error) {
    return false;
  }
}

async function ensureConnected(tab) {
  if (!tab) return false;
  if (await ping(tab.id)) return true;
  if (!/^https?:\/\//.test(tab.url || "")) return false;
  try {
    await chrome.scripting.executeScript({
      target: { tabId: tab.id, allFrames: true },
      files: ["content.js"],
    });
  } catch (error) {
    return false;
  }
  return ping(tab.id);
}

async function refreshConnection(tab) {
  const connected = await ensureConnected(tab || (await activeTab()));
  connState = connected ? "ok" : "off";
  renderConnection();
  return connected;
}

// Current selection of a tab's main frame, asked from the content script.
async function getSelectedText(tabId) {
  try {
    const tab = tabId === undefined ? await activeTab() : { id: tabId };
    if (!tab) return "";
    const reply = await chrome.tabs.sendMessage(
      tab.id,
      { type: "infosure-get-selection" },
      { frameId: 0 },
    );
    return ((reply && reply.text) || "").trim();
  } catch (error) {
    return "";
  }
}

// Live selection: the field follows what the user highlights. The old result no longer matches, so reset the view.
function setSelectedText(text) {
  els.text.value = text.slice(0, MAX_CHARS);
  if (view.state !== "loading") showEmpty();
  setStatus(text.length > MAX_CHARS ? "hintTruncated" : "hintUpdated", {
    n: MAX_CHARS,
  });
}

/* ---------- results ---------- */

const view = { state: "empty", data: null, error: null };
function show(state, children) {
  view.state = state;
  els.result.dataset.state = state;
  els.result.replaceChildren(...children);
  for (const child of els.result.children) child.classList.add("enter");
}

function rerender() {
  if (view.state === "verified") renderVerified(view.data);
  else if (view.state === "scope") renderScope(view.data);
  else if (view.state === "error") renderError(view.error);
  else if (view.state === "empty") showEmpty();
  renderStatus();
}

function confidenceBand(confidence) {
  if (typeof confidence !== "number") return null;
  if (confidence < 0.6) return "low"; // placeholder bands for an UNCALIBRATED score; never shown as a percentage
  if (confidence < 0.75) return "medium";
  return "high";
}

function agreementState(assessment) {
  if (assessment.startsWith("Conflicting")) return "conflict";
  if (assessment.startsWith("Not verified")) return "none";
  return "agree";
}

function safeHttpUrl(value) {
  try {
    const url = new URL(value);
    return url.protocol === "http:" || url.protocol === "https:" ? url : null;
  } catch (error) {
    return null;
  }
}

function noticeCard(tone, iconName, title, text) {
  const card = el("section", `card notice-card tone-${tone}`);
  card.append(icon(iconName));
  const body = el("div");
  body.append(el("h2", "", title), el("p", "", text));
  card.append(body);
  return card;
}

/* empty state: how it works, examples, recent checks */
function showEmpty() {
  const t = T();
  const welcome = el("section", "card");
  welcome.append(el("h2", "", t.welcomeTitle));
  const steps = el("ol", "steps");
  for (const s of [t.welcomeStep1, t.welcomeStep2, t.welcomeStep3])
    steps.append(el("li", "", s));
  welcome.append(steps);

  const examples = el("div", "examples");
  examples.append(el("small", "", t.tryExample));
  const chips = el("div", "chips");
  for (const text of t.examples) {
    const chip = el("button", "chipbtn example", text);
    chip.type = "button";
    chip.addEventListener("click", () => {
      els.text.value = text;
      analyze(text);
    });
    chips.append(chip);
  }
  examples.append(chips);
  welcome.append(examples);

  const children = [welcome];
  const recent = loadRecent();
  if (recent.length) children.push(recentCard(recent));
  show("empty", children);
}

function loadRecent() {
  try {
    const list = JSON.parse(storageGet(RECENT_KEY) || "[]");
    return Array.isArray(list)
      ? list.filter((x) => x && typeof x.text === "string").slice(0, MAX_RECENT)
      : [];
  } catch (error) {
    return [];
  }
}
function saveRecent(text, label) {
  const list = loadRecent().filter((x) => x.text !== text);
  list.unshift({ text: text.slice(0, 300), label });
  storageSet(RECENT_KEY, JSON.stringify(list.slice(0, MAX_RECENT)));
}

function recentCard(list) {
  const card = el("section", "card recent");
  const head = el("div", "recent-head");
  head.append(el("small", "", T().recent));
  const clear = el("button", "linkbtn", T().clear);
  clear.type = "button";
  clear.addEventListener("click", () => {
    storageSet(RECENT_KEY, "[]");
    showEmpty();
  });
  head.append(clear);
  card.append(head);
  const items = el("div", "recent-list");
  for (const entry of list) {
    const item = el(
      "button",
      `recent-item tone-${entry.label === "Reliable" ? "good" : "bad"}`,
    );
    item.type = "button";
    item.append(el("span", "dot"), el("span", "t", entry.text));
    item.addEventListener("click", () => {
      els.text.value = entry.text;
      analyze(entry.text);
    });
    items.append(item);
  }
  card.append(items);
  return card;
}

function renderLoading() {
  const hero = el("section", "card skeleton");
  hero.append(
    el("div", "sk short"),
    el("div", "sk big"),
    el("div", "sk"),
    el("div", "sk short"),
  );
  const evidence = el("section", "card skeleton");
  evidence.append(el("div", "sk short"), el("div", "sk"), el("div", "sk"));
  show("loading", [hero, evidence]);
}

function renderError(error) {
  view.error = error;
  const card = noticeCard("bad", "warn", T().errorTitle, describeError(error));
  const retry = el("button", "chipbtn retry");
  retry.type = "button";
  retry.append(icon("retry"), el("span", "", T().retry));
  retry.addEventListener("click", () => analyze(els.text.value));
  card.lastChild.append(retry);
  show("error", [card]);
}

function renderScope(data) {
  const out = data.scope === "out_of_scope";
  show("scope", [
    noticeCard(
      "neutral",
      out ? "info" : "question",
      out ? T().scopeOutTitle : T().scopeNoneTitle,
      out ? T().scopeOutText : T().scopeNoneText,
    ),
  ]);
}

function heroCard(data) {
  const t = T();
  const good = data.ml_label === "Reliable";
  const hero = el("section", `card hero tone-${good ? "good" : "bad"}`);

  const kicker = el("div", "hero-kicker");
  kicker.append(
    el("span", "kicker", t.verdictKicker),
    el("span", "tag", t.estimateTag),
  );
  hero.append(kicker);

  const verdict = el("div", "verdict");
  verdict.append(
    icon(good ? "good" : "bad"),
    el("span", "verdict-word", t[data.ml_label] || data.ml_label),
  );
  hero.append(verdict);
  hero.append(
    el("p", "verdict-sub", good ? t.subReliable : t.subMisinformation),
  );

  const band = confidenceBand(data.ml_confidence);
  if (band) {
    const meter = el("div", "meter");
    const bars = el("div", "meter-bars");
    const level = { low: 1, medium: 2, high: 3 }[band];
    for (let i = 1; i <= 3; i++) bars.append(el("i", i <= level ? "on" : ""));
    meter.append(bars, el("span", "meter-label", t.conf[band]));
    hero.append(meter);
  }

  return hero;
}

function evidenceCard(item) {
  const t = T();
  const card = el("div", "ev");
  const top = el("div", "ev-top");
  const source = el("div");
  source.append(el("div", "ev-source", item.source_name));
  const url = safeHttpUrl(item.source_url);
  const domain = url ? url.hostname.replace(/^www\./, "") : "";
  const date = item.publication_date
    ? fmt(t.published, { d: item.publication_date })
    : t.dateUnknown;
  const meta = el("div", "ev-meta");
  [domain, date].filter(Boolean).forEach((part, i) => {
    if (i) meta.append(document.createTextNode(" · "));
    meta.append(el("span", "", part));
  });
  source.append(meta);
  top.append(source);
  const tone =
    { entailment: "good", contradiction: "bad" }[item.relation] || "neutral";
  const chip = el(
    "span",
    `chip tone-${tone}`,
    t.rel[item.relation] || t.rel.neutral,
  );
  top.append(chip);
  card.append(top);

  const text = el("p", "ev-text clamped", item.evidence_text);
  card.append(text);
  const actions = el("div", "ev-actions");
  if (item.evidence_text.length > 220) {
    const toggle = el("button", "linkbtn", t.showMore);
    toggle.type = "button";
    toggle.addEventListener("click", () => {
      const clamped = text.classList.toggle("clamped");
      toggle.textContent = clamped ? T().showMore : T().showLess;
    });
    actions.append(toggle);
  }
  if (url) {
    const link = el("a", "linkbtn");
    link.href = url.href;
    link.target = "_blank";
    link.rel = "noopener noreferrer";
    link.append(icon("link"), el("span", "", t.openSource));
    actions.append(link);
  }
  card.append(actions);
  return card;
}

function evidenceSection(data) {
  const t = T();
  const state = agreementState(data.assessment);
  const section = el("section", "card");
  const head = el("div", "section-head");
  head.append(el("h2", "", t.evidenceTitle));
  const tone =
    { Supported: "good", Contradicted: "bad" }[data.evidence_result] ||
    "neutral";
  head.append(
    el(
      "span",
      `chip tone-${tone}`,
      t.ev[data.evidence_result] || data.evidence_result,
    ),
  );
  section.append(head);

  const tones = { agree: "good", conflict: "warn", none: "neutral" };
  const icons = { agree: "check", conflict: "warn", none: "info" };
  const strip = el("div", `agree tone-${tones[state]}`);
  strip.append(icon(icons[state]), el("span", "", t[state]));
  section.append(strip);

  for (const item of data.evidence) section.append(evidenceCard(item));
  return section;
}

function howToRead() {
  const t = T();
  const details = el("details", "card");
  const summary = el("summary");
  summary.append(icon("book"), el("span", "", t.howTitle), icon("chevron"));
  const body = el("div", "explain");
  for (const html of [t.howModel, t.howEvidence, t.howConflict]) {
    const p = el("p");
    richText(p, html);
    body.append(p);
  }
  details.append(summary, body);
  return details;
}

function feedbackCard(data) {
  const t = T();
  const card = el("section", "card feedback");

  const head = el("div", "fb-head");
  head.append(el("p", "feedback-q", t.feedbackQ));
  card.append(head);

  const grid = el("div", "fb-grid");
  const note = el("div", "note");
  const choices = [
    ["Agree", "up", "good"],
    ["Disagree", "up", "bad"],
    ["Flag", "flag", "warn"],
  ];
  const buttons = [];

  function showNote(tone, iconName, text) {
    note.className = `note tone-${tone}`;
    note.replaceChildren(icon(iconName), el("span", "", text));
  }

  for (const [choice, iconName, tone] of choices) {
    const button = el("button", `fb-btn tone-${tone}${choice === "Disagree" ? " down" : ""}`);
    button.type = "button";
    button.setAttribute("aria-pressed", "false");
    button.append(icon(iconName), el("span", "", t[choice]));
    button.addEventListener("click", async () => {
      buttons.forEach((b) => (b.disabled = true));
      button.classList.add("busy");
      note.className = "note";
      note.replaceChildren();
      try {
        await postJson("/feedback", {
          claim_text: data.claim,
          model_prediction: data.ml_label,
          model_confidence: data.ml_confidence,
          evidence_result: data.evidence_result,
          user_feedback: choice,
          model_version: data.model_version,
        });
        button.classList.remove("busy");
        button.classList.add("selected");
        button.setAttribute("aria-pressed", "true");
        buttons.filter((b) => b !== button).forEach((b) => b.classList.add("dim"));
        showNote("good", "check", T().thanks);
      } catch (error) {
        button.classList.remove("busy");
        buttons.forEach((b) => (b.disabled = false));
        showNote("bad", "warn", describeError(error));
      }
    });
    buttons.push(button);
    grid.append(button);
  }
  card.append(grid, note);
  return card;
}

function summaryText(data) {
  const t = T();
  const band = confidenceBand(data.ml_confidence);
  const lines = [
    fmt(t.sumVerdict, {
      v: t[data.ml_label] || data.ml_label,
      c: band ? t.conf[band].toLowerCase() : "",
    }),
    fmt(t.sumEvidence, {
      e: t.ev[data.evidence_result] || data.evidence_result,
    }),
    fmt(t.sumClaim, { c: data.claim }),
  ];
  const urls = data.evidence
    .map((e) => e.source_url)
    .filter((u) => safeHttpUrl(u));
  if (urls.length) lines.push(t.sumSources, ...urls);
  return lines.join("\n");
}

function actionsRow(data) {
  const t = T();
  const row = el("div", "actions");
  const copy = el("button", "chipbtn");
  copy.type = "button";
  copy.append(icon("copy"), el("span", "", t.copy));
  copy.addEventListener("click", async () => {
    try {
      await navigator.clipboard.writeText(summaryText(data));
      copy.lastChild.textContent = T().copied;
      setTimeout(() => (copy.lastChild.textContent = T().copy), 1500);
    } catch (error) {
      /* clipboard blocked: nothing to do */
    }
  });
  const fresh = el("button", "chipbtn");
  fresh.type = "button";
  fresh.append(icon("retry"), el("span", "", t.newCheck));
  fresh.addEventListener("click", () => {
    els.text.value = "";
    setStatus(null);
    showEmpty();
    els.text.focus();
  });
  row.append(copy, fresh);
  return row;
}

function renderVerified(data) {
  view.data = data;
  show("verified", [
    heroCard(data),
    evidenceSection(data),
    howToRead(),
    feedbackCard(data),
    actionsRow(data),
  ]);
}

/* ---------- running a check ---------- */

async function analyze(rawText) {
  const text = rawText.trim();
  if (!text) {
    setStatus("hintStart");
    return;
  }
  els.check.disabled = true;
  setStatus("checking");
  renderLoading();
  try {
    const data = await postJson("/analyze", { text });
    setStatus(null);
    view.data = data;
    if (data.scope === "verified") {
      saveRecent(data.claim, data.ml_label);
      renderVerified(data);
    } else {
      renderScope(data);
    }
  } catch (error) {
    setStatus(null);
    renderError(error);
  } finally {
    els.check.disabled = false;
  }
}

els.check.addEventListener("click", () => analyze(els.text.value));
els.text.addEventListener("keydown", (event) => {
  if (event.key === "Enter" && (event.ctrlKey || event.metaKey))
    analyze(els.text.value);
});

/* ---------- live selection from the page ---------- */

chrome.runtime.onMessage.addListener((message, sender) => {
  if (
    !message ||
    message.type !== "infosure-selection" ||
    typeof message.text !== "string"
  )
    return;
  activeTab().then((tab) => {
    if (tab && sender.tab && sender.tab.id === tab.id)
      setSelectedText(message.text);
  });
});

chrome.tabs.onActivated.addListener(({ tabId }) => {
  chrome.tabs
    .get(tabId)
    .then(async (tab) => {
      if (!(await refreshConnection(tab))) return;
      const text = await getSelectedText(tabId);
      if (text) setSelectedText(text);
    })
    .catch(() => {});
});

chrome.tabs.onUpdated.addListener((tabId, change, tab) => {
  if (change.status !== "complete" || !tab.active) return;
  refreshConnection(tab);
});

/* ---------- start ---------- */

(async function init() {
  applyStaticText();
  showEmpty();
  setStatus("hintStart");
  await refreshConnection();
  const selected = await getSelectedText();
  if (!selected) {
    els.text.focus();
    return;
  }
  els.text.value = selected.slice(0, MAX_CHARS);
  await analyze(els.text.value); // opened on a selection: check it right away
  if (selected.length > MAX_CHARS) setStatus("hintTruncated", { n: MAX_CHARS });
})();
