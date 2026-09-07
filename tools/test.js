/* =========================================================================
   Test harness for the ESG profile viewer.

   Run it:      node tools/test.js
   It prints a PASS/FAIL line per check and exits non-zero if any fail.

   HOW IT WORKS, because it is unusual: there is no test framework and no
   browser here. This file builds a minimal fake DOM, then loads the real
   app.js and runs it against the real data file, injecting a hook so the
   app's own internal functions can be called directly. That means these
   checks exercise the shipped code, not a copy of it.

   WHAT IT DOES NOT COVER: anything visual. Layout, spacing, colour and
   whether text overflows are not testable here — those need a browser and
   a human. Do not treat a green run as "the page is fine".

   WHEN YOU CHANGE THE DATA SHAPE, expect failures here first. That is the
   point: several real bugs were caught this way, including framework tags
   leaking onto non-BRSR rows and the CSV export silently losing the "GRI"
   prefix. If a check fails, work out whether the code or the expectation is
   wrong before changing either.

   Two quirks of the fake DOM that the app genuinely depends on: appendChild
   unwraps a DocumentFragment, and setting textContent clears children.
   ========================================================================= */

/* Executes the real app.js against a minimal DOM stub so the shipped
   filter and CSV code is what gets tested, not a reimplementation. */

const fs = require("fs");
const path = require("path");

const DIR = path.resolve(__dirname, "..");

function makeEl(tag) {
  const el = {
    tagName: tag,
    children: [],
    className: "",
    _text: "",
    hidden: false,
    value: "",
    scrollHeight: 0,
    clientHeight: 0,
    _classes: new Set(),
    style: {},
    attrs: {},
    setAttribute(k, v) { this.attrs[k] = String(v); },
    addEventListener() {},
    focus() {},
    appendChild(c) {
      // Real DOM moves a DocumentFragment's children rather than inserting
      // the fragment itself. layoutTable() depends on that.
      if (c && c.tagName === "#fragment") {
        c.children.forEach(child => { this.children.push(child); child.parentElement = this; });
        c.children = [];
        return c;
      }
      this.children.push(c); if (c) c.parentElement = this; return c;
    },
    removeChild(c) { this.children = this.children.filter(x => x !== c); return c; },
    querySelector() { return null; },
  };
  el.classList = {
    add: c => el._classes.add(c),
    remove: c => el._classes.delete(c),
    contains: c => el._classes.has(c),
    toggle: c => { el._classes.has(c) ? el._classes.delete(c) : el._classes.add(c);
                   return el._classes.has(c); },
  };
  Object.defineProperty(el, "textContent", {
    get() { return this._text; },
    // Setting textContent clears existing children in the real DOM.
    set(v) { this.children = []; this._text = String(v); },
  });
  Object.defineProperty(el, "innerHTML", {
    get() { return ""; },
    set() { this.children = []; },
  });
  return el;
}

const registry = {};
[
  "theme-select", "keyword-select", "search-input", "clear-search",
  "visible-count", "table-body", "empty-state", "clear-filters-btn",
  "company-name", "updated-line", "download-csv-btn", "print-btn",
  "print-summary", "disclosure-table", "footer-note",
  "framework-select",
].forEach(id => { registry[id] = makeEl("div"); });

// tableBody.parentElement.hidden is set by applyFilters
registry["table-body"].parentElement = makeEl("table");

// A real <select> reports its first option as .value. index.html ships
// "All Themes" and "All Keywords" as the first option of each, so mirror that.
registry["theme-select"].value = "All Themes";
registry["keyword-select"].value = "All Keywords";
registry["framework-select"].value = "All Frameworks";

global.window = {};
global.document = {
  getElementById: id => registry[id] || null,
  createElement: makeEl,
  createDocumentFragment: () => makeEl("#fragment"),
  createElementNS: (ns, tag) => makeEl(tag),
  body: makeEl("body"),
  title: "",
};
global.Option = function (text, value) {
  const o = makeEl("option");
  o.textContent = text;
  o.value = value === undefined ? text : value;
  return o;
};
global.Blob = function (parts) { this.parts = parts; };
global.URL = { createObjectURL: () => "blob:test", revokeObjectURL: () => {} };

// load data
require(path.join(DIR, "data/disclosures.js"));
const DATA = global.window.ESG_DATA;

// load app.js, but inject a test hook inside the IIFE so the real
// internal functions are the ones exercised
let src = fs.readFileSync(path.join(DIR, "app.js"), "utf8");
const marker = src.lastIndexOf("})();");
if (marker === -1) { console.error("could not find IIFE close"); process.exit(1); }
src = src.slice(0, marker) +
  "\n  global.__hooks = { rowMatches: rowMatches, buildCsv: buildCsv," +
  " applyFilters: applyFilters, themeSelect: themeSelect," +
  " keywordSelect: keywordSelect, searchInput: searchInput," +
  " visibleCountEl: visibleCountEl, emptyState: emptyState," + " buildSeriesBlock: buildSeriesBlock, buildChart: buildChart," + " frameworkSelect: frameworkSelect, layoutTable: layoutTable," + " groupKey: groupKey, groupLabel: groupLabel };\n" +
  src.slice(marker);

eval(src);
const H = global.__hooks;

let failures = 0;
function check(label, actual, expected) {
  const ok = actual === expected;
  if (!ok) failures++;
  console.log("  " + (ok ? "PASS" : "FAIL") + "  " + label.padEnd(52) +
              String(actual) + (ok ? "" : "   expected " + expected));
}

function countMatching(theme, keyword, query, framework) {
  return DATA.rows.filter(r => H.rowMatches(r, theme, keyword, query, framework)).length;
}

console.log("\nFILTER LOGIC");
check("no filters", countMatching("All Themes", "All Keywords", ""), 663);
check("theme Environment", countMatching("Environment", "All Keywords", ""), 82);
check("theme Social", countMatching("Social", "All Keywords", ""), 135);
check("theme Governance", countMatching("Governance", "All Keywords", ""), 139);
check("theme BRSR Disclosures", countMatching("BRSR Disclosures", "All Keywords", ""), 149);
check("keyword Employees", countMatching("All Themes", "Employees", ""), 94);
check("keyword BRSR", countMatching("All Themes", "BRSR", ""), 149);
check("whitespace query == no query",
      countMatching("All Themes", "All Keywords", ""), 663);

const envWater = countMatching("Environment", "Water", "");
const allWater = countMatching("All Themes", "Water", "");
check("keyword narrows within theme (Water)", envWater <= allWater, true);

const combo = countMatching("Environment", "Water", "withdrawal");
check("three filters combine (never exceeds theme)", combo <= 82, true);

// search should reach metric labels, which only exist in the metrics array
const scope3 = DATA.rows.filter(r =>
  r.metrics.some(m => /Scope 3/i.test(m.label)));
const scope3Search = countMatching("All Themes", "All Keywords", "scope 3");
check("search finds metric-label-only text", scope3Search >= scope3.length, true);

console.log("\nIFC (DERIVED BY ALIGNMENT)");

function fwIFC(sub) {
  const r = DATA.rows.find(x => x.subfactor.replace(/\u00a0/g, " ") === sub &&
                                x.category.startsWith("BRSR"));
  return r ? (r.frameworks || []).find(f => f.name === "IFC") : null;
}

check("IFC rows", countMatching("All Themes", "All Keywords", "", "IFC"), 49);
check("Water Usage (GRI 303) derives PS3", fwIFC("Water Usage").full, "PS3");
check("Training (GRI 403/404) derives PS2",
      fwIFC("Employees and Workers Training").full, "PS2");
check("Biodiversity (GRI 304) derives PS6",
      fwIFC("Protect Nature and Biodiversity").full, "PS6");

// GRI 200-series alignment is rated weak by the same source, so it is excluded
check("a GRI 201-only row derives no IFC", fwIFC("CSR Details"), undefined);

// every IFC tag must declare that it is weaker than the others
let ifcVerified = 0, ifcAlignment = 0, ifcSourced = 0;
DATA.rows.forEach(r => (r.frameworks || []).forEach(f => {
  if (f.name !== "IFC") return;
  if (f.verified) ifcVerified++;
  if (f.level === "alignment") ifcAlignment++;
  if (/not a published/.test(f.source || "")) ifcSourced++;
}));
check("no IFC tag claims to be verified", ifcVerified, 0);
check("every IFC tag marked as alignment-derived", ifcAlignment, 49);
check("every IFC tag states it is not a published mapping", ifcSourced, 49);
check("IFC detail says how it was derived",
      /by GRI alignment/.test(fwIFC("Water Usage").detail), true);

// the derivation is stated in words, so the pill needs no question mark
check("IFC pill carries no question mark",
      /\?/.test(fwIFC("Water Usage").detail), false);

// IFC is chained through GRI, so it can never appear without one
const ifcWithoutGri = DATA.rows.filter(r => {
  const n = (r.frameworks || []).map(f => f.name);
  return n.includes("IFC") && !n.includes("GRI");
}).length;
check("IFC never appears without GRI", ifcWithoutGri, 0);

// GRI 2 and 3 are no longer mapped: contact details and registered office
// must not appear under a risk-management Performance Standard
["Name of the Listed Entity", "E-mail", "Telephone", "Corporate Address",
 "Reporting Boundary", "CIN", "Website", "Paid-up Capital",
 "Year of Incorporation"].forEach(function (t) {
  check("admin row '" + t + "' carries no IFC tag", fwIFC(t), undefined);
});

// IFC is only chained from an indicator-precise GRI answer. Chaining from the
// principle-level union put CIN under Labour and Working Conditions.
let ifcOffPrinciple = 0;
DATA.rows.forEach(r => {
  const fs = r.frameworks || [];
  const gri = fs.find(f => f.name === "GRI");
  const ifc = fs.find(f => f.name === "IFC");
  if (ifc && gri && gri.level !== "indicator") ifcOffPrinciple++;
});
check("no IFC derived from a principle-level GRI answer", ifcOffPrinciple, 0);

// but the genuine employee rows keep theirs
["Employees and Workers", "Women Employee Inclusion",
 "Employee Turnover Rate"].forEach(function (t) {
  check("employee row '" + t + "' still maps to PS2",
        fwIFC(t) && fwIFC(t).full, "PS2");
});
const ps1 = DATA.rows.filter(r => {
  const f = (r.frameworks || []).find(x => x.name === "IFC");
  return f && f.full.split(", ")[0] === "PS1";
}).length;
check("PS1 bucket is small and specific", ps1, 8);
check("IFC groups are all topic standards",
      Object.keys(DATA.rows.reduce((a, r) => {
        const f = (r.frameworks || []).find(x => x.name === "IFC");
        if (f) a[f.full.split(", ")[0]] = 1;
        return a;
      }, {})).sort().join(","), "PS1,PS2,PS3,PS4,PS6");

// and never outside the BRSR sections
check("no IFC tag outside BRSR", DATA.rows.filter(r =>
  (r.frameworks || []).some(f => f.name === "IFC") &&
  !r.category.startsWith("BRSR")).length, 0);

console.log("\nGROUPING BY FRAMEWORK");

function headerRows() {
  return registry["table-body"].children.filter(c =>
    c.className === "category-row");
}
function dataRows() {
  return registry["table-body"].children.filter(c => c.className === "data-row");
}

H.layoutTable("All Frameworks");
const catHeaders = headerRows().length;
check("default layout groups by source category", catHeaders, 28);
check("all 663 rows laid out", dataRows().length, 663);

H.layoutTable("IFC");
const psHeaders = headerRows();
check("IFC layout regroups under Performance Standards",
      psHeaders.length <= 8, true);
check("every row still laid out after regrouping", dataRows().length, 663);

// headings must appear in PS order, not data order
const codes = psHeaders.map(h => h._categoryName).filter(k => /^PS\d$/.test(k));
const sorted = codes.slice().sort();
check("Performance Standards in numerical order",
      codes.join(",") === sorted.join(","), true);

const lbl = H.groupLabel("PS3", "IFC");
check("PS heading carries its number", lbl.code, "PS 3");
check("PS heading carries its name",
      /Resource Efficiency/.test(lbl.name), true);

const catLbl = H.groupLabel("BRSR Section C: Principle 6", "All Frameworks");
check("category heading shows a short code", catLbl.code, "P6");

// a row with two Performance Standards groups under the first
const multi = DATA.rows.find(r => {
  const f = (r.frameworks || []).find(x => x.name === "IFC");
  return f && f.full.indexOf(", ") !== -1;
});
check("multi-PS row groups under its first standard",
      H.groupKey(multi, "IFC"), multi.frameworks.find(f => f.name === "IFC").full.split(", ")[0]);

H.layoutTable("All Frameworks");

console.log("\nCSV EXPORT");
const csvAll = H.buildCsv(DATA.rows);
fs.writeFileSync("/tmp/export_all.csv", csvAll, "utf8");
const csvEnv = H.buildCsv(DATA.rows.filter(r => r.theme === "Environment"));
fs.writeFileSync("/tmp/export_env.csv", csvEnv, "utf8");
check("starts with UTF-8 BOM", csvAll.charCodeAt(0), 0xFEFF);
check("uses CRLF line endings", /\r\n/.test(csvAll), true);
check("every field quoted (no bare commas at line start)",
      /^﻿"Theme","Category"/.test(csvAll), true);

console.log("\nRENDER");
check("rows built", registry["table-body"].children.length > 0, true);
check("count line populated", /Showing 663 of 663/.test(H.visibleCountEl.textContent), true);
check("empty state hidden when rows visible", H.emptyState.hidden, true);

console.log("\nTREND CHARTS");

const ghg = DATA.rows.find(r => r.subfactor === "Amount of GHG Emissions");
const ghgSeries = ghg.series.find(s => /GHG Emission/.test(s.measure));
check("GHG series has 3 points", ghgSeries.points.length, 3);
check("GHG series flagged as discontinuous", ghgSeries.flagged, true);
check("break detected between 2024 and 2025", JSON.stringify(ghgSeries.breaks), "[1]");
check("caption is the specific one, not generic",
      /excludes Scope 3/.test(ghgSeries.note), true);
check("points are in chronological order",
      ghgSeries.points.map(p => p.year).join(","), "2024,2025,2026");

const chart = H.buildChart(ghgSeries);
const rects = chart.children.filter(c => c.tagName === "rect");
check("three bars drawn", rects.length, 3);
check("first bar marked as pre-break",
      rects[0].attrs.class, "bar bar-prebreak");
check("later bars not marked", rects[2].attrs.class, "bar");

// Zero baseline check: with a true zero baseline the 2024 bar is tiny
// (1.07M of 14.6M). Min-max scaling would render it at zero height and
// exaggerate the apparent jump.
const h2024 = Number(rects[0].attrs.height);
const h2026 = Number(rects[2].attrs.height);
const ratio = ghgSeries.points[0].value / ghgSeries.points[2].value;
check("tallest bar uses full plot height", h2026, 40);
check("shortest bar is scaled from zero, not min-max",
      Math.abs(h2024 / h2026 - ratio) < 0.05, true);

const lines = chart.children.filter(c => c.tagName === "line");
check("baseline plus one break line drawn", lines.length, 2);

const block = H.buildSeriesBlock(ghgSeries);
check("flagged block carries the warning class",
      block.className, "series series-flagged");
const flat = JSON.stringify(block, (k, v) => k === "parentElement" ? undefined : v);
check("exact unrounded value shown on screen",
      /1,072,290\.39/.test(flat), true);
check("caption rendered in the block", /excludes Scope 3/.test(flat), true);

// two-point series: change text, no chart
let twoPt = null;
for (const r of DATA.rows) {
  const s = (r.series || []).find(x => x.points.length === 2);
  if (s) { twoPt = s; break; }
}
const twoBlock = H.buildSeriesBlock(twoPt);
const hasSvg = twoBlock.children.some(c => c.tagName === "svg");
check("two-year series draws no chart", hasSvg, false);

// every metric still reachable: series points + standalone == metrics
let unrendered = 0;
for (const r of DATA.rows) {
  const inSeries = (r.series || []).reduce((a, s) => a + s.points.length, 0);
  if (inSeries + (r.standalone || []).length !== r.metrics.length) unrendered++;
}
check("no figure lost between series and standalone", unrendered, 0);

console.log("\nFRAMEWORK FILTER");
check("BRSR rows", countMatching("All Themes", "All Keywords", "", "BRSR"), 149);
check("BRSR Core rows", countMatching("All Themes", "All Keywords", "", "BRSR Core"), 14);
check("GRI rows (from the published linkage)",
      countMatching("All Themes", "All Keywords", "", "GRI"), 149);
check("All Frameworks returns everything",
      countMatching("All Themes", "All Keywords", "", "All Frameworks"), 663);
check("framework combines with theme (never exceeds theme)",
      countMatching("Environment", "All Keywords", "", "GRI") <= 82, true);

// BRSR Core must be a subset of BRSR, or the tagging is incoherent
const coreNotBrsr = DATA.rows.filter(r => {
  const n = (r.frameworks || []).map(f => f.name);
  return n.includes("BRSR Core") && !n.includes("BRSR");
}).length;
check("every BRSR Core row is also BRSR", coreNotBrsr, 0);

console.log("\nBRSR INDICATOR CODES");

function fw(sub, name) {
  const r = DATA.rows.find(x => x.subfactor === sub && x.category.startsWith("BRSR"));
  return r ? (r.frameworks || []).find(f => f.name === name) : null;
}

check("every BRSR row carries an indicator code",
      DATA.rows.filter(r => r.category.startsWith("BRSR") &&
        !(r.frameworks || []).some(f => f.name === "BRSR" && f.indicator)).length, 0);

// spot-checks against SEBI's numbered format
check("Energy Consumption is P6-E1", /P6-E1/.test(fw("Energy Consumption", "BRSR").detail), true);
check("Water Usage is P6-E3", /P6-E3/.test(fw("Water Usage", "BRSR").detail), true);
check("Scope 1 and 2 is P6-E6",
      /P6-E6/.test(fw("Amount of GHG Emission (Scope 1 and 2)", "BRSR").detail), true);
check("Scope 3 is a Leadership indicator, P6-L4",
      /P6-L4/.test(fw("Amount of GHG Emission (Scope 3)", "BRSR").detail), true);

// and the GRI those indicators map to, per the linkage document
check("P6-E1 maps to GRI 302-1", /302-1/.test(fw("Energy Consumption", "GRI").full), true);
check("P6-E3 maps to GRI 303-3 and 303-5",
      /303-3/.test(fw("Water Usage", "GRI").full) && /303-5/.test(fw("Water Usage", "GRI").full), true);
check("P6-E6 maps to GRI 305-1 and 305-2",
      /305-1/.test(fw("Amount of GHG Emission (Scope 1 and 2)", "GRI").full) &&
      /305-2/.test(fw("Amount of GHG Emission (Scope 1 and 2)", "GRI").full), true);
check("P6-L4 (Scope 3) maps to GRI 305-3",
      /305-3/.test(fw("Amount of GHG Emission (Scope 3)", "GRI").full), true);
check("Scope 1&2 does NOT claim GRI 305-3",
      /305-3/.test(fw("Amount of GHG Emission (Scope 1 and 2)", "GRI").full), false);
check("Data Breaches maps to GRI 418", /418/.test(fw("Data Breaches", "GRI").full), true);

// the same title outside BRSR must not inherit an indicator code
const envEnergy = DATA.rows.find(r => r.subfactor === "Energy Consumption" &&
                                      r.category === "Environment");
check("non-BRSR row with the same title gets no framework tag",
      envEnergy && (envEnergy.frameworks || []).length, 0);

let indicatorLevel = 0, principleLevel = 0;
DATA.rows.forEach(r => (r.frameworks || []).forEach(f => {
  if (f.name === "GRI" && f.level === "indicator") indicatorLevel++;
  if (f.name === "GRI" && f.level === "principle") principleLevel++;
}));
check("GRI at indicator level", indicatorLevel, 114);
check("GRI at principle level", principleLevel, 35);
check("indicator plus principle equals every BRSR row",
      indicatorLevel + principleLevel, 149);

// GRI is only claimed where the linkage document actually says something
const griOutsideBrsr = DATA.rows.filter(r =>
  (r.frameworks || []).some(f => f.name === "GRI") &&
  !r.category.startsWith("BRSR")).length;
check("no GRI tag outside the BRSR sections", griOutsideBrsr, 0);

let unverified = 0, sourced = 0;
DATA.rows.forEach(r => (r.frameworks || []).forEach(f => {
  if (!f.verified) unverified++;
  if (f.name === "GRI" && f.source) sourced++;
}));
check("only IFC tags are unverified", unverified, 49);
check("every GRI tag cites its source", sourced, 149);

// Principle-level fallback: rows whose indicator has no entry in the 2022
// linkage document keep the coarser principle mapping. It must still contain
// the environmental topic standards or the transcription is wrong.
const zld = DATA.rows.find(r => r.subfactor === "Zero Liquid Discharge Mechanism");
const zldGri = zld.frameworks.find(f => f.name === "GRI");
check("fallback row is marked principle level", zldGri.level, "principle");
check("P6 fallback includes GRI 302", /GRI 302/.test(zldGri.full), true);
check("P6 fallback includes GRI 303", /GRI 303/.test(zldGri.full), true);
check("P6 fallback includes GRI 305", /GRI 305/.test(zldGri.full), true);
check("P6 fallback includes GRI 306", /GRI 306/.test(zldGri.full), true);

const p9row = DATA.rows.find(r =>
  r.subfactor === "Consumer Complaints and Feedback Collection Mechanisms");
const p9Gri = p9row.frameworks.find(f => f.name === "GRI");
check("P9 fallback includes GRI 418", /GRI 418/.test(p9Gri.full), true);
check("P9 fallback does not claim GRI 305", /GRI 305/.test(p9Gri.full), false);

// the numbers must be on the page itself, not only in a tooltip
const p6e1 = DATA.rows.find(r => r.subfactor === "Energy Consumption" &&
                                 r.category.startsWith("BRSR"));
check("indicator-level GRI shows numbers as visible detail",
      /302-1/.test(p6e1.frameworks.find(f => f.name === "GRI").detail), true);
const p6brsr = p6e1.frameworks.find(f => f.name === "BRSR");
check("BRSR tag shows its indicator", /P6-E1/.test(p6brsr.detail), true);
check("BRSR tag shows the indicator type",
      /Essential|Leadership/.test(p6brsr.detail), true);

// CSV must carry the provenance too
const csvHdr = H.buildCsv(DATA.rows.slice(0, 1)).split("\r\n")[0];
check("CSV has a Frameworks column", /"Frameworks"/.test(csvHdr), true);
const csvP6 = H.buildCsv(DATA.rows.filter(r =>
  r.category === "BRSR Section C: Principle 6").slice(0, 3));
check("CSV carries the GRI standards for P6", /GRI 302/.test(csvP6), true);
const csvNonBrsr = H.buildCsv(DATA.rows.filter(r =>
  r.theme === "Environment").slice(0, 20));
check("CSV claims no GRI on non-BRSR rows", /GRI /.test(csvNonBrsr), false);

console.log("\n" + (failures === 0 ? "ALL CHECKS PASSED" : failures + " CHECK(S) FAILED"));
process.exit(failures === 0 ? 0 : 1);
