/* =========================================================================
   Test harness for the BRSR extraction app (brsr-app.html).

   Run it:      node tools/test-extract.js
   Prints a PASS/FAIL line per check and exits non-zero if any fail.

   HOW IT WORKS: no browser and no test framework. It reads the built
   brsr-app.html, lifts out the app's own script, and runs it under a
   minimal stub of the few DOM calls the script makes while starting up.
   The app hands its internals to window.BRSR_INTERNALS, so the functions
   checked here are the shipped ones, not copies.

   The functions covered are pure: they take arrays of {text, y, runs} —
   the same shape pdf.js produces once lines are assembled — and return
   ranges, codes and CSV text. That is why no PDF is needed.

   WHAT THIS DOES NOT COVER: reading an actual PDF, and anything visual.
   tools/test_app.js drives the real app in a browser against a fixture
   PDF; appearance still needs a person. A green run here is not "the app
   works", it is "these rules still hold".
   ========================================================================= */
"use strict";

const fs = require("fs");
const path = require("path");
const vm = require("vm");

const ROOT = path.resolve(__dirname, "..");
const APP = path.join(ROOT, "brsr-app.html");

const fails = [];
function check(label, got, want) {
  const ok = JSON.stringify(got) === JSON.stringify(want);
  console.log(`  ${ok ? "PASS" : "FAIL"}  ${label.padEnd(58)} ${JSON.stringify(got)}`);
  if (!ok) fails.push(`${label}: got ${JSON.stringify(got)}, wanted ${JSON.stringify(want)}`);
}

/* --- load the shipped app under a stub DOM ---------------------------- */

if (!fs.existsSync(APP)) {
  console.error("ERROR: brsr-app.html not built. Run: python3 tools/build_app.py");
  process.exit(1);
}
const html = fs.readFileSync(APP, "utf8");

function scriptById(id) {
  const re = new RegExp(`<script id="${id}"[^>]*>([\\s\\S]*?)</script>`);
  const m = re.exec(html);
  return m ? m[1] : "";
}

// The app's own code is the script block that publishes BRSR_INTERNALS.
const appScript = (() => {
  const re = /<script\s*>([\s\S]*?)<\/script>/g;
  let m;
  while ((m = re.exec(html)) !== null) {
    if (m[1].indexOf("BRSR_INTERNALS") !== -1) return m[1];
  }
  throw new Error("could not find the app script inside brsr-app.html");
})();

// Only what the script touches before it finishes loading: three JSON
// blocks it parses, and addEventListener on a handful of controls.
const jsonBlocks = {
  "gri-map": scriptById("gri-map"),
  "ifc-map": scriptById("ifc-map"),
  "ifc-names": scriptById("ifc-names"),
};

function stubEl(id) {
  return {
    id,
    textContent: jsonBlocks[id] !== undefined ? jsonBlocks[id] : "",
    innerHTML: "", value: "", hidden: false, disabled: false, title: "",
    style: {}, dataset: {}, classList: { add() {}, remove() {}, toggle() {} },
    addEventListener() {}, appendChild() {}, insertAdjacentHTML() {},
    querySelector() { return null; }, querySelectorAll() { return []; },
    click() {}, focus() {},
  };
}

const els = {};
const sandbox = {
  console,
  setTimeout, clearTimeout, JSON, Math, Date, parseInt, parseFloat, isNaN,
  String, Number, Object, Array, RegExp, Error, Promise, Blob: function () {},
  TextDecoder: function () { return { decode: () => "" }; },
  URL: { createObjectURL: () => "", revokeObjectURL() {} },
  atob: (b) => Buffer.from(b, "base64").toString("binary"),
  Uint8Array,
  document: {
    getElementById(id) { return (els[id] = els[id] || stubEl(id)); },
    createElement: (t) => stubEl(t),
    body: { appendChild() {}, removeChild() {} },
    addEventListener() {},
  },
  localStorage: {
    _d: {},
    getItem(k) { return Object.prototype.hasOwnProperty.call(this._d, k) ? this._d[k] : null; },
    setItem(k, v) { this._d[k] = String(v); },
    removeItem(k) { delete this._d[k]; },
  },
  addEventListener() {},
};
sandbox.window = sandbox;
sandbox.globalThis = sandbox;
vm.createContext(sandbox);
vm.runInContext(appScript, sandbox, { filename: "brsr-app.html" });

const A = sandbox.window.BRSR_INTERNALS;
if (!A || !A.locate) {
  console.error("ERROR: the app did not publish its internals; harness needs updating.");
  process.exit(1);
}

/* --- synthetic pages -------------------------------------------------- */
// A line as the app models one: text, a baseline, and the runs it was
// assembled from. Only the first run's x matters (the left margin).
function line(text, y, x) {
  return { text, y, runs: [{ x: x === undefined ? 51 : x, y, s: text, w: text.length * 5, h: 9 }] };
}
function page(lines) { return { lines, tables: [] }; }
const BLANK = page([line("Nothing of interest here", 700)]);

/* --- 1. the principle search is fenced to Section C -------------------- */
console.log("\nThe principle search starts at Section C");
{
  // Section B talks about the principles long before the annexure answers
  // them. That mention must not become Principle 9's anchor.
  const pages = [
    page([line("Section B: Management and Process Disclosures", 700),
          line("Principle 9 of the NGRBCs is covered by our policies", 600)]),
    BLANK,
    page([line("SECTION C: PRINCIPLE WISE PERFORMANCE DISCLOSURE", 760),
          line("Principle 1 - Businesses should conduct themselves with integrity", 700),
          line("Essential Indicators", 660),
          line("1. Percentage coverage by training", 620)]),
    page([line("Principle 9 - Businesses should engage with consumers", 700),
          line("Essential Indicators", 660),
          line("1. Describe the mechanisms in place", 620)]),
  ];
  const loc = A.locate(pages, () => {});
  check("Section C is found on its real page", loc.sectionC, 3);
  check("a principle named before Section C is ignored", loc.ranges[9][0], 4);
  check("Principle 1 anchors inside Section C", loc.ranges[1][0], 3);
  check("no fallback was needed", loc.sectionCFallback, false);
}

/* --- 2. a mention of Section C in a contents list is not the section --- */
{
  const pages = [
    page([line("Contents", 760), line("Section C: Principle wise performance ....... 40", 700)]),
    page([line("SECTION C: PRINCIPLE WISE PERFORMANCE DISCLOSURE", 760),
          line("Principle 1 - Businesses should conduct themselves with integrity", 700),
          line("Essential Indicators", 660),
          line("1. Percentage coverage by training", 620)]),
  ];
  const loc = A.locate(pages, () => {});
  check("a contents-page mention is not mistaken for the section", loc.sectionC, 2);
}

/* --- 3. no Section C heading at all falls back, and says so ------------ */
{
  const pages = [
    BLANK,
    page([line("Principle 1 - Businesses should conduct themselves with integrity", 700),
          line("Essential Indicators", 660),
          line("1. Percentage coverage by training", 620)]),
  ];
  const notes = [];
  const loc = A.locate(pages, (m) => notes.push(m));
  check("falls back to the first Principle 1 heading", loc.sectionC, 2);
  check("the fallback is recorded", loc.sectionCFallback, true);
  check("and it is said in plain language", /no 'Section C' heading/i.test(notes.join(" ")), true);
}

/* --- 4. two principles sharing one page still split -------------------- */
console.log("\nTwo principles on one page");
{
  const pages = [
    page([line("SECTION C: PRINCIPLE WISE PERFORMANCE DISCLOSURE", 780),
          line("Principle 1 - Businesses should conduct themselves with integrity", 760),
          line("Essential Indicators", 740),
          line("1. Percentage coverage by training", 720)]),
    page([line("Principle 7 - Businesses when engaging in policy", 700),
          line("Essential Indicators", 680),
          line("1. Number of affiliations with trade chambers", 660),
          line("Principle 8 - Businesses should promote inclusive growth", 400),
          line("Essential Indicators", 380),
          line("1. Details of Social Impact Assessments", 360)]),
  ];
  const loc = A.locate(pages, () => {});
  check("both principles anchor to the same page", [loc.ranges[7][0], loc.ranges[8][0]], [2, 2]);
  check("the earlier one stops where the later one starts", loc.ranges[7][3], 400);
}

/* --- 5. an answer's own numbered list is not a question ---------------- */
console.log("\nQuestions are told apart from answer lists");
{
  const lines = [
    line("1. Channels where information can be accessed", 322, 51),
    line("1. Company Website", 293, 71),
    line("2. Company social media channels", 275, 71),
    line("2. Steps taken to inform consumers", 160, 51),
  ];
  const cols = A.questionColumns(lines, 1e9, -1e9);
  const taken = lines.filter((l) => A.questionOn(l, cols)).map((l) => l.text.slice(0, 12));
  check("only the left-margin lines are questions",
        taken, ["1. Channels ", "2. Steps tak"]);
}
{
  // A two-column filing puts a second run of questions across the page.
  const lines = [
    line("2. Details of fines and penalties", 767, 56.7),
    line("7. Provide details of corrective action", 250, 313.3),
  ];
  const cols = A.questionColumns(lines, 1e9, -1e9);
  check("a second column is recognised as questions too",
        lines.filter((l) => A.questionOn(l, cols)).length, 2);
}

/* --- 6. the BRSR ends where the form's structure ends ------------------ */
console.log("\nThe section stops at the end of the form");
{
  const pages = [
    page([line("Principle 9 - Businesses should engage with consumers", 700),
          line("Essential Indicators", 680),
          line("1. Describe the mechanisms in place", 660)]),
    page([line("2. Turnover of products as a percentage", 700),
          line("3. Number of consumer complaints", 500)]),
    page([line("Financial Statements", 700),
          line("STANDALONE FINANCIAL STATEMENTS: 283-382", 660)]),
    page([line("Independent Auditor's Report", 700),
          line("1. We have audited the accompanying standalone financial", 660)]),
  ];
  check("it stops before the financial statements", A.brsrEnd(pages, 1), 2);
}

/* --- 7. bulk approval only takes what was read confidently ------------- */
console.log("\nBulk approval cannot satisfy the gate on its own");
{
  const fig = (c, dropped) => ({ confidence: c, dropped: !!dropped });
  const cases = [
    ["all figures confident",        { status: "pending", figures: [fig(0.9), fig(0.9)] }, true],
    ["one uncertain figure",         { status: "pending", figures: [fig(0.9), fig(0.6)] }, false],
    ["no figures at all",            { status: "pending", figures: [] }, false],
    ["every figure dropped",         { status: "pending", figures: [fig(0.9, true)] }, false],
    ["uncertain but dropped",        { status: "pending", figures: [fig(0.9), fig(0.6, true)] }, false],
    ["already approved",             { status: "approved", figures: [fig(0.9)] }, false],
    ["already excluded",             { status: "excluded", figures: [fig(0.9)] }, false],
  ];
  cases.forEach(([label, ind, want]) => check("  " + label, A.bulkApprovable(ind), want));
}

/* --- 8. the audit trail round-trips ------------------------------------ */
console.log("\nThe audit trail is a readable CSV");
{
  const state = {
    filename: "annual-report.pdf",
    indicators: [
      { code: "P6-E1", question: 'Energy use, "total"', status: "approved",
        figures: [
          { measure: "Total energy consumed", raw: "419.18", unit: "GJ", year: "FY 2024-25",
            page: 271, source: "table", confidence: 0.9 },
          { measure: "Corrected, was wrong", raw: "5.37", unit: "", year: "FY 2024-25",
            page: 271, source: "table", confidence: 0.9, originalRaw: "5.73", edited: true },
        ] },
      { code: "P6-E2", question: "Water\nover two lines", status: "excluded",
        figures: [{ measure: "Withdrawal", raw: "1,234.5", unit: "KL", year: "FY 2023-24",
                    page: 272, source: "text", confidence: 0.6, dropped: true }] },
    ],
  };
  const csv = A.auditCsv(state);

  check("starts with a byte-order mark", csv.charCodeAt(0), 0xfeff);
  // Record separators must be CRLF. A newline *inside* a quoted field is
  // legitimate and Excel handles it, so quoted fields are removed before
  // looking for a bare one.
  const outsideQuotes = csv.slice(1).replace(/"(?:[^"]|"")*"/g, "");
  check("every record ends with CRLF", /[^\r]\n/.test(outsideQuotes), false);
  check("the file ends with a line ending", csv.slice(-2), "\r\n");

  // Parse it back the way a spreadsheet would.
  function parseCsv(text) {
    const rows = [];
    let row = [], field = "", inQ = false;
    for (let i = 0; i < text.length; i++) {
      const c = text[i];
      if (inQ) {
        if (c === '"') { if (text[i + 1] === '"') { field += '"'; i++; } else inQ = false; }
        else field += c;
      } else if (c === '"') inQ = true;
      else if (c === ",") { row.push(field); field = ""; }
      else if (c === "\r" && text[i + 1] === "\n") { row.push(field); rows.push(row); row = []; field = ""; i++; }
      else field += c;
    }
    if (field !== "" || row.length) { row.push(field); rows.push(row); }
    return rows;
  }
  const rows = parseCsv(csv.slice(1));
  check("one header plus one row per figure", rows.length, 4);
  check("every row has the same column count",
        [...new Set(rows.map((r) => r.length))], [13]);
  check("a comma inside a value does not split the row",
        rows[3][3], "1,234.5");
  check("a newline inside a question does not split the row",
        rows[3][1], "Water\nover two lines");
  check("a quote inside a question survives", rows[1][1], 'Energy use, "total"');
  check("a corrected figure shows what was read first", [rows[2][3], rows[2][9]], ["5.37", "5.73"]);
  check("an untouched figure has no original value", rows[1][9], "");
  check("a dropped figure is kept, marked dropped", rows[3][10], "dropped");
  check("an excluded indicator's status is recorded", state.indicators[1].status, "excluded");
  check("the source file is on every row",
        [...new Set(rows.slice(1).map((r) => r[11]))], ["annual-report.pdf"]);
}

/* --- done -------------------------------------------------------------- */
console.log();
if (fails.length) {
  console.log("FAILURES:");
  fails.forEach((f) => console.log("  - " + f));
  process.exit(1);
}
console.log("ALL CHECKS PASSED");
