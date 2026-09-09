/**
 * Drives brsr-app.html in a real browser against the test fixture.
 *
 *     npm install --no-save playwright-core
 *     node tools/test_app.js
 *
 * Opens the built app, feeds the fixture PDF through the actual file
 * input, approves everything, presses Generate, and checks the profile
 * that comes out.
 *
 * WHAT THIS PROVES: the app works end to end in a browser — pdf.js loads
 * from the copy embedded in the file, the BRSR section is found,
 * indicators are split correctly, figures are read with their page, and
 * the generated page carries the right values.
 *
 * WHAT IT DOES NOT PROVE: accuracy on a real filed report. The fixture is
 * clean digital text with regular tables.
 *
 * Driven with playwright-core rather than `chrome --dump-dom`, because
 * pdf.js runs in a Web Worker and Chrome's virtual-time clock stalls
 * against one — the page simply never finished.
 */
"use strict";

const fs = require("fs");
const path = require("path");
const { execFileSync } = require("child_process");
const { chromium } = require("playwright-core");

const ROOT = path.join(__dirname, "..");
const APP = path.join(ROOT, "brsr-app.html");
const FIXTURE = path.join(__dirname, "fixtures", "test-brsr.pdf");
// Chrome's path differs between the build sandbox and a laptop, so it is
// looked up rather than fixed. CHROME=/path/to/chrome overrides.
const EXEC = [
  process.env.CHROME,
  "/opt/pw-browsers/chromium-1194/chrome-linux/chrome",
  "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
  "/Applications/Chromium.app/Contents/MacOS/Chromium",
].find((c) => c && fs.existsSync(c));
if (!EXEC) {
  console.error("No Chrome found. Install Google Chrome, or set CHROME=/path/to/chrome");
  process.exit(1);
}

const fails = [];
function check(label, got, want) {
  const ok = JSON.stringify(got) === JSON.stringify(want);
  console.log(`  ${ok ? "PASS" : "FAIL"}  ${label.padEnd(50)} ${JSON.stringify(got)}`);
  if (!ok) fails.push(`${label}: got ${JSON.stringify(got)}, wanted ${JSON.stringify(want)}`);
}

// The answer key: figures written into the Principle 6 narratives.
// Read independently of the app, from the printed form. A BRSR writes
// small intensities as "35.42 x 10-10"; that is one number, and a key that
// stopped at the mantissa asserted the very bug this suite is meant to
// catch — an emissions intensity ten orders of magnitude too large, or
// negative once the exponent was read as the value.
function keyFigures(narrative) {
  const out = new Map();
  const re = /FY\s*(\d{4})\s*:\s*([^;]+)/gi;
  let m;
  while ((m = re.exec(narrative)) !== null) {
    const n = /-?\d[\d,]*(?:\.\d+)?/.exec(m[2]);
    if (!n) continue;
    let v = parseFloat(n[0].replace(/,/g, ""));
    if (isNaN(v)) continue;
    const rest = m[2].slice(n.index + n[0].length);
    const sci = /^\s*[x\u00d7*]\s*10\s*(?:\^\s*([+-]?\d{1,3})|([+-]\d{1,3}))/.exec(rest);
    if (sci) v *= Math.pow(10, parseInt(sci[1] || sci[2], 10));
    // Keyed on the value, carrying the printed mantissa so the caller can
    // still tell whether the figure appears in the fixture at all.
    out.set(`${m[1]}|${v.toExponential(6)}`, n[0].replace(/,/g, ""));
  }
  return out;
}

(async () => {
  if (!fs.existsSync(APP)) {
    console.error("ERROR: brsr-app.html not built. Run: python3 tools/build_app.py");
    process.exit(1);
  }
  console.log("Building fixture...");
  execFileSync("python3", [path.join(__dirname, "make_test_brsr.py")], { stdio: "pipe" });

  console.log("Driving the app in a browser...");
  const browser = await chromium.launch({ executablePath: EXEC, args: ["--no-sandbox"] });
  const page = await browser.newPage();
  const errors = [];
  page.on("pageerror", (e) => errors.push(String(e)));
  await page.goto("file://" + APP);

  await page.setInputFiles("#file", FIXTURE);
  await page.waitForSelector("#step-review.on", { timeout: 120000 });

  const seen = await page.evaluate(() => ({
    indicators: Number(document.getElementById("s-ind").textContent),
    figures: Number(document.getElementById("s-fig").textContent),
    left: Number(document.getElementById("s-left").textContent),
    generateDisabled: document.getElementById("generate").disabled,
  }));

  // The fixture carries Principle 6 in full plus a one-question Principle 7
  // stub, so a correct run finds 21 indicators, not 20.
  console.log("\nThe review step holds the gate");
  check("indicators found across both principles", seen.indicators, 21);
  check("figures found", seen.figures > 50, true);
  check("all start unchecked", seen.left, 21);
  check("Generate is disabled until reviewed", seen.generateDisabled, true);

  await page.click("#approve-all");
  const afterApprove = await page.evaluate(() => ({
    left: Number(document.getElementById("s-left").textContent),
    generateDisabled: document.getElementById("generate").disabled,
  }));
  check("nothing left to check after Approve all", afterApprove.left, 0);
  check("Generate is enabled once reviewed", afterApprove.generateDisabled, false);

  await page.click("#generate");
  await page.waitForSelector("#step-done.on", { timeout: 60000 });

  const out = await page.evaluate(() => {
    // Rebuild the payload the same way the download button does.
    const js = window.BRSR_INTERNALS.state().dataJs;
    const obj = JSON.parse(js.slice(js.indexOf("{"), js.lastIndexOf(";")));
    return {
      rows: obj.rows.length,
      figures: obj.rows.reduce((a, r) => a + r.metrics.length, 0),
      codes: obj.rows.map((r) => r.frameworks[0].indicator),
      docs: obj.rows.map((r) => r.documents[0].label),
      gri: obj.rows.map((r) => {
        const g = r.frameworks.filter((f) => f.name === "GRI")[0];
        return g ? g.detail : null;
      }),
      ifc: obj.rows.some((r) => r.frameworks.some(
        (f) => f.name === "IFC" && f.verified === false)),
      pairs: obj.rows.reduce((a, r) => a.concat(
        r.metrics.map((m) => [r.frameworks[0].indicator, m.label, m.value])), []),
      previewHasRows: (document.getElementById("preview").srcdoc || "").includes("ESG_DATA"),
    };
  });

  console.log("\nWhat came out");
  check("rows generated", out.rows, 21);
  check("Principle 6 rows", out.codes.filter((c) => c.startsWith("P6-")).length, 20);
  check("Principle 7 picked up too", out.codes.filter((c) => c.startsWith("P7-")).length, 1);
  check("Principle 6 essential codes run E1-E12",
    out.codes.filter((c) => c.startsWith("P6-E"))
      .map((c) => Number(c.split("-E")[1])).sort((a, b) => a - b),
    [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12]);
  check("P6-L1 absent, as in the source profile", out.codes.includes("P6-L1"), false);
  check("every row cites the PDF and a page",
    out.docs.every((d) => /^test-brsr\.pdf \(Page \d+\)$/.test(d)), true);
  check("GRI tag is not split into letters",
    out.gri.some((g) => g && g.startsWith("302-1-a")), true);
  check("IFC tags stay unverified", out.ifc, true);
  check("preview page carries the data", out.previewHasRows, true);
  check("no JavaScript errors", errors, []);

  console.log("\nFigures survive the round trip");
  const src = fs.readFileSync(path.join(ROOT, "data", "disclosures.js"), "utf8");
  const data = JSON.parse(src.slice(src.indexOf("{", src.indexOf("window.ESG_DATA")), src.lastIndexOf(";")));
  const fixtureHtml = fs.readFileSync(path.join(__dirname, "fixtures", "test-brsr.html"), "utf8").replace(/,/g, "");

  const byCode = {};
  data.rows.filter((r) => r.category === "BRSR Section C: Principle 6").forEach((r) => {
    const t = (r.frameworks || []).find((f) => f.name === "BRSR");
    if (t) byCode[t.detail.split(" · ")[0].trim()] = r;
  });

  const got = {};
  out.pairs.forEach(([code, label, value]) => {
    const y = /\b(\d{4})\b/.exec(label);
    if (y) (got[code] = got[code] || new Set()).add(`${y[1]}|${value.toExponential(6)}`);
  });

  let total = 0, matched = 0;
  const missing = [];
  Object.keys(byCode).sort().forEach((code) => {
    keyFigures(byCode[code].highlights).forEach((printed, k) => {
      const mant = parseFloat(printed);
      if (!fixtureHtml.includes(printed) && !fixtureHtml.includes(mant.toFixed(2))) return;
      total++;
      if (got[code] && got[code].has(k)) matched++;
      else missing.push(`${code} ${k}`);
    });
  });
  check("figures present in the PDF", total > 50, true);
  check("recovered exactly", matched, total);
  missing.slice(0, 12).forEach((m) => console.log("       missed " + m));

  await browser.close();
  console.log();
  if (fails.length) {
    console.log("FAILURES:");
    fails.forEach((f) => console.log("  - " + f));
    process.exit(1);
  }
  console.log(`ALL CHECKS PASSED  (${matched}/${total} figures recovered exactly)`);
})().catch((e) => {
  console.error("ERROR: " + (e && e.message ? e.message : e));
  process.exit(1);
});
