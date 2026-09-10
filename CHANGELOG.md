# Changelog

Every change to this project, newest first, in plain language.

**Why this exists:** the reasoning behind a decision is worth more than the decision itself. Several things here look like odd choices until you know what went wrong with the obvious approach — why GRI covers 149 rows and not 445, why IFC covers 49 and not 141, why a chart has a dashed line through it. If you are picking this up cold, read this before changing anything.

**Format:** each entry says what changed, and where it matters, *why*. Decisions that were reversed are kept, not deleted — a reversal is information.

---

## 10 Sep 2026 — the whole BRSR, not just the principles

**The app was reading a quarter of the form and skipping the rest.** It found
Section C and read past everything before it, so a generated profile carried
the nine principles and nothing else. The source export this project is built
on has 149 BRSR rows: 26 from Section A, 12 from Section B, 111 across the
principles.

Sections A and B are numbered the same way as the principles, so they now
share the same collector, differing only in having no Essential/Leadership
headings to restart the count. Their pages are found by working backwards
from Section C, the heading already trusted, so a contents page listing all
three cannot pull any of them forward.

**Half of Section A is not written as numbered paragraphs at all.** The
company's particulars — CIN, registered office, paid-up capital, assurance
provider — are rows of a table, numbered down its first column. Reading only
paragraphs started the section at question 16. A numbered row with a label
and a value beside it now counts as a disclosure. Tables headed "S. No" are
an answer's own tabulation and are left alone; anything else that restarts
its numbering is discarded by requiring the count to advance.

No new mapping work was needed: the GRI-SEBI linkage document already keys 18
Section A and 9 Section B mappings by exactly these codes, so the tags stay
sourced.

On the annual report: 108 disclosures becomes 145, figures 216 becomes 243,
trend series 89 becomes 98. Section A comes out complete, 26 of 26.

**Section B is partial and will stay that way for now** — 11 of 12 on one
report, 6 of 12 on the other. Its policy grid is the gap, for two different
reasons: one filing prints the question as a bare "1." with its wording
inside the grid, and the other prints the entire grid sideways. Rotated text
is deliberately ignored, because reading it inline is what put "Corporate
Overview" in the middle of sentences.

---

## 9 Sep 2026 — annual reports read correctly; the review gate made real

**Where the app lives changed.** It is in the repository as `brsr-app.html`,
generated from `app-src/brsr-app.template.html` by `tools/build_app.py`. The
loose copies — `brsrapp.html`, `brsrapp2.html`, `brsrapp3.html` — were
downloads of that built file at three points in time. Editing a built copy
loses the work at the next build, which is why the source is named
everywhere now.

**`brsrapp.html` and `brsrapp2.html` were deleted** from the project folder
and from Downloads, as `brsrapp-fix-spec.md` asked once the four changes
landed. They were the dangerous ones: they open perfectly well and silently
lack the fixes. Both were moved to the Trash rather than erased, and both
contents survive in this repository's history anyway — `brsrapp.html` is
`brsr-app.html` at 28473c8, `brsrapp2.html` is the same file at 4455672.
`brsrapp3.html` matches the current build exactly.

**Eight faults found by running a real 513-page integrated annual report
through it.** None showed on a standalone BRSR, which is why they survived.

- The last principle had nothing to stop it, so Principle 9 claimed pages
  281 to 513 and filed the auditor's report as consumer disclosures — 109
  invented rows, unflagged.
- A superscript exponent sat on its own baseline, so `4.92 x 10-7` was read
  as `-7`. A **negative emissions intensity**, under a real company's name.
  Superscripts and subscripts are pulled back onto their line, and the
  number is read whole.
- Numbered lists inside an answer were read as questions; the Principle 9
  answer listing customer channels runs 1 to 7, so seven invented indicators
  took real codes. A question must now start at the left edge of its column.
- Tables that draw only their column separators lost everything outside
  them — on the energy table, the parameter names and the entire previous
  year. Figures went from 88 to 216, and the prior year from 23 to 98.
- Sideways margin tabs and running headers were spliced into sentences
  ("However, we *Corporate Overview* ensure that…").
- Every answer swallowed the next question — two in three of them.
- Two visual faults: long titles printing over the tags beside them, and
  titles cut mid-word.

**Why the tests did not catch the exponent bug:** the answer key read
`35.42 x 10-10` as `35.42`, the same rule that caused the fault. A green run
had been endorsing a wrong number. The key now reads exponents independently.

**The four changes specified in `brsrapp-fix-spec.md` landed.** The principle
search is fenced to Section C — it used to take the first "Principle *n*"
line anywhere, and a report names its principles in contents lists, in
Section B and in a GRI index long before the annexure answers them.
"Approve all" no longer approves everything: it takes only indicators whose
every figure was read with high confidence, 25 of 108 on the annual report,
which is what stops the review gate being ceremonial. Review state now
survives a closed tab, saved under a fingerprint of the PDF so a different
report never restores the wrong work. And an audit trail downloads as CSV —
one row per figure with its page, confidence, status, and what the extractor
first read if a person corrected it.

**A defect this changelog recorded was not real.** The entry below reports a
*"Principle 9 of the NGRBCs"* line on page 17 of the bundled BRSR
mis-anchoring two principles. It does not reproduce: that PDF holds exactly
nine lines able to anchor a principle, on the nine correct pages, and both
the current app and the older copies already produced them. The entry is
kept, because a reversal is information. The weakness behind it was real and
is fixed. Accuracy measurement is no longer blocked.

**Added `tools/test-extract.js`** — 30 checks on the extraction rules,
running in Node against the shipped code with no browser and no PDF.

Still true: no dependencies, no network, no credentials, no rounding of
figures. Accuracy remains unmeasured.

---

## 9 Sep 2026 (later) — `brsrapp2.html` reviewed; locating defect found

**Added `brsrapp2.html`**, superseding `brsrapp.html`. New: `brsrEnd` infers where the BRSR stops by watching indicator numbering go backwards without a heading to reset it; `stripRunningHeads` removes repeated page furniture by shape; principle ranges became y-aware so two principles sharing a page split correctly. All safety invariants held — no dependencies, no network, no credentials, no rounding of figures.

**Defect found and verified.** `locate()` records the Section C page and never uses it, taking the first `Principle n` line found anywhere. On the bundled BRSR PDF, page 17 (Section B) contains *"Principle 9 of the NGRBCs"*, so:

- **P9** anchors to pages 17–20 and reports Section B policy text under Principle 9 codes.
- **P8** then runs 39–43 and absorbs Principle 9's real content from page 41.
- Principles 1–7 are correct.

**Two of nine principles produce wrong output.** Verified by simulating the locating logic against the document's actual page structure. Caveat: a command-line text extractor was used, whose line reconstruction differs slightly from the app's — but the offending line is unambiguously a line start.

The same fix — fence the search to Section C — is what annual-report support requires, since a 300-page integrated report mentions "Section C" and "Principle *n*" in contents pages and governance narrative long before the BRSR annexure.

**Second concern: an "Approve all" button was added.** The review gate — nothing publishes until every indicator is approved or excluded — was the property making this defensible. One click satisfying it for ~140 indicators makes it ceremonial.

**Added `brsrapp-fix-spec.md`** specifying four changes: fence the locator, restrict "Approve all" to high-confidence indicators, save review state with a warning before leaving, and export an audit trail.

**`phase3-spike-brief.md` is blocked** until the locator is fixed. Measuring accuracy against a locator that mis-assigns two principles produces a wrong number that looks plausible.

## 9 Sep 2026 — BRSR extraction prototype

**Added `brsrapp.html`** — a single-file app that reads a BRSR or sustainability report PDF and generates a profile page from it. This is the first working piece of Phase 3, the "upload a report and the profile appears" idea.

Built by Debraj outside this working folder and reviewed here. What it does:

- Reads the PDF entirely in the browser. **PDF.js is embedded as base64**, so there is no CDN, no install and no network — it still works by double-clicking, offline.
- **No AI model is involved.** Extraction is regex plus geometric layout parsing: text is bucketed by vertical position to rebuild table rows, and column positions are found by voting on horizontal alignment. This means zero cost per report and deterministic, traceable failures.
- Every extracted figure carries a **page number, a source (table or narrative) and a confidence score** — 0.9 for a table figure with an explicit year, down to 0.65 for a bare narrative number.
- **A review gate is enforced in code.** The Generate button stays disabled until every indicator is explicitly approved or excluded. Extract → review → publish, not extract → publish.
- Falls back to looking for a GRI content index when no BRSR section is found.

**Review findings, in order of importance:**

1. **No review work is saved.** No localStorage, no session storage, no warning before closing the tab. Reviewing ~140 indicators takes about an hour; a reload or crash loses all of it. Phase 1 deliberately avoided browser storage so *filter state* would reset — that reasoning does not carry to an hour-long human task.
2. **Review runs in document order, not confidence order.** A reviewer who runs out of time has spread the effort evenly rather than concentrating on doubtful rows.
3. **No source page image** — page number and extracted text only. PDF.js can already render pages, so this is available rather than expensive.

**Verified in review:** figures are never rounded (`Math.round` appears only in layout geometry and the progress bar); the Phase 1 safeguards survived the port, including the discontinuity captions and IFC's `verified: false` marking; no credentials, no network calls, no external dependencies.

**Not verified:** extraction accuracy. Nobody has yet run it against a report with known-correct answers. That measurement is still the open question and still decides the economics.

**Added `phase3-spike-brief.md` and `phase3-architecture.md`** — the feasibility test and the provisional design for the full upload product. The spike brief is now much cheaper to execute than when written, because `brsrapp.html` is the instrument rather than something to be built.

---

## 7 Sep 2026 — Handoff preparation

- **Moved the test harness into the project** as `tools/test.js`. It had been living in a scratch folder, which meant a fresh session had no way to check its own work — a real gap on a project where the owner cannot review code.
- **Rewrote `CLAUDE.md`.** It had grown by patching, including a paragraph beginning "Older note, still current", and still claimed the page had never been seen in a browser. It now leads with the commands to run before claiming anything is done, and a section on the three things that must not be undone.
- **`README.md`** gained a file-by-file table and the test commands.
- **PRD raised to version 3.0**, adding a section on why the framework mapping is narrower than it could be, and "provenance" as a competitive differentiator.
- **Added `push-to-github.command`** so committing and pushing is one double-click. The sandbox has no network route to GitHub, so this could not be automated.
- **Added `.gitignore`**, excluding `ESGReport.xls` — it carries the real company name, CIN, contact details and director biographies, and the repository's visibility was not established.

## 7 Sep 2026 — IFC narrowed from 141 rows to 49

Cut twice, both times after looking at the rendered page rather than reasoning about it.

**First cut:** GRI 2 and GRI 3 no longer map to IFC PS1. They align with PS1's management-system requirements in the abstract, but in practice this filed the company's **e-mail address, telephone number and registered office** under "Assessment and Management of Environmental and Social Risks" — 26 admin rows in a 74-row bucket.

**Second cut:** IFC is no longer derived from principle-level GRI answers. A principle-level answer is the union of every standard linked to a whole BRSR section, so Section A's union includes GRI 401 and 405 — which put **"CIN" and "Paid-up Capital" under Labour and Working Conditions.** IFC is now derived only where the GRI answer is indicator-precise.

Also: the `?` was dropped from IFC tags (the label already reads "by GRI alignment"), duplicate keyword pills hidden, and the tag column widened from 15% to 19%.

**Why this matters:** 49 of 149 is the honest number for a mapping built by chaining. Widening it back is a regression.

## 7 Sep 2026 — Table regroups by framework

Selecting IFC reorganises the table's section headings under Performance Standards PS1–PS8, the way IFC itself presents them; any other selection groups by source category. Headings gained a code chip, full name and disclosure count.

Row elements are reused across layouts rather than rebuilt, so expanded text stays expanded and filtering behaves identically after a regroup.

## 7 Sep 2026 — IFC added, derived by alignment (141 rows)

No published BRSR-to-IFC mapping exists. IFC's January 2025 benchmarking rates GRI-to-Performance-Standard alignment at series level, so the link is **chained**: BRSR indicator → GRI disclosure → IFC. No single document asserts that composition.

IFC tags were therefore marked `verified: false`, rendered hollow, and labelled "by GRI alignment". GRI 200-series excluded — the same source rates its alignment as weak.

*Note:* IFC's handbook contains detailed tables (C.3, D.2, E.2) that could not be retrieved — only pages 1–52 of about 80 were readable. A better mapping may exist.

## 7 Sep 2026 — BRSR indicator numbers added

All 149 BRSR rows now carry their indicator number from SEBI's own format — `P6-E1`, `A18`, `P5-E3` — because the portal's row titles follow SEBI's numbered questions in the same order.

With indicators known, GRI mapping sharpened from principle level to **indicator level for 114 rows**; 35 keep the principle-level fallback where the 2022 linkage document has no entry.

Indicator codes and GRI numbers moved onto the page itself, out of hover tooltips. Tooltips are never seen during a live demonstration.

**Two bugs caught by the tests here**, both invisible on screen: subfactor titles are not unique across the file, so an unscoped lookup tagged 7 non-BRSR rows; and two rows silently lost their codes to non-breaking spaces in the source titles.

## 7 Sep 2026 — GRI rebuilt on the published linkage document

**Superseded the previous revision, which tagged 445 GRI and 324 IFC rows by keyword matching.** Any row mentioning water received GRI 303 whether or not that was correct. Those numbers looked better and meant nothing.

Rebuilt on *"Linking the GRI Standards and the SEBI BRSR Framework"* (GRI with the Bombay Stock Exchange, 2022). GRI dropped from 445 rows to 149 — **the smaller number is the point**, because every one of them can be traced to a published source. IFC was withdrawn entirely at this stage.

The provisional warning banner was removed, because nothing was being guessed any more.

## 7 Sep 2026 — Framework filter added (keyword-based — later replaced)

Added a fourth filter for BRSR, BRSR Core, GRI and IFC. BRSR and BRSR Core came from keywords already in the source export. GRI and IFC were derived by keyword matching and marked provisional on screen.

**Retained here because it was wrong and the reason matters:** keyword guessing produced high coverage and low truth. It was replaced within the same day once the published linkage document was found.

## 7 Sep 2026 — Trend charts

45 year-over-year series were derived from the metric labels: 32 with three or more years are charted as columns, 13 with two years show a change statement instead, because two points are not a trend.

**The discontinuity guard is the substantive part.** Any series jumping 3× or more between consecutive years is flagged, drawn with hollow pre-break bars, a dashed break line and a visible caption.

It exists because the GHG emissions series would otherwise have shown a **false twelvefold rise**: 1,072,290 tCO2e in 2024 against 13,125,144 in 2025. The 2025 and 2026 totals reconcile exactly to Scope 1 + 2 + 3; 2024 has no scope breakdown disclosed at all and almost certainly excludes Scope 3. The boundary widened; the emissions did not.

Charts always use a zero baseline and always print exact values. Four of the five flagged series still carry a generic caption and need investigating.

## 7 Sep 2026 — Phase 1 built; anonymisation settled

The converter, page, filters, metrics, CSV export and print stylesheet were implemented against the real 663-row export.

**Anonymisation decision:** the demo does not carry the real company name. Company and personal names, contact details, identifiers, document links and third-party organisations are replaced. **The sixteen director biographies are withheld entirely** — the combination of previous employers, universities and other board seats identifies an individual in a single search, and pattern replacement cannot reliably catch that.

**Stated plainly then and now: this is de-branded, not anonymous.** The reported figures are real and published, so they can be matched back to the filed report. The sector remains legible from the narrative.

## 10 Aug 2026 — CSV download and print-to-PDF

Both had been on the "Left Out" list; moved into scope. `.xlsx`, Word and PDF-library generation stayed out — a real `.xlsx` needs either a CDN library, which breaks the offline demo, or a hand-written zip encoder.

The CSV specification includes the quote-escaping and UTF-8 marker Excel needs, and requires the result to be **opened in Excel** before it counts as tested. A CSV that reads fine in a text editor and shreds in Excel is the usual failure.

## 10 Aug 2026 — Real source data replaces the sample

The original spec assumed roughly 25 hand-authored sample rows. The real export turned out to be **663 disclosures across 28 categories**, with 96 rows carrying figures, 84 keyword tags and 912 hyperlinks.

Four things this broke in the build that existed:

1. **There is no Environmental/Social/Governance column.** The factor dropdown read a field that does not exist; Environment, Social and Governance are 3 of 28 categories covering 329 of 663 rows.
2. **Metrics had nowhere to go** — 96 rows carry numbers with units across multiple years.
3. **Links are real and clickable** — the build was suppressing clicks because the sample URLs were placeholders.
4. **Keywords became free** — 84 tags already existed, so the keyword filter cost almost nothing.

Themes were introduced to group the 28 categories into six, because frameworks are tags but themes must partition the rows exactly.

## 10 Aug 2026 — Project start

`product-spec.md` written for a Tier 1 MVP: a single-page, zero-dependency viewer for one company's ESG disclosures, opened by double-clicking, for live demonstration to clients.

`CLAUDE.md` written to record that the owner is a sustainability consultant who does not read code, that the work goes in front of clients, and that the burden of verification therefore sits entirely with the assistant.

---

## Things that have never changed

Carried unbroken since the start, and not up for renegotiation without a decision:

- **The shipped page has zero dependencies.** `tools/` is a developer-only exception that never reaches the browser.
- **It opens by double-clicking.** No server, no build step.
- **Never invent a figure.** No estimation, no filling gaps with plausible numbers, no rounding or unit conversion on the way in. A missing value renders empty.
- **Provenance stays visible.** Every mapping traceable to a named public document; anything weaker marked as derived rather than sourced.
- **Nothing publishes unreviewed** — the rule Phase 1 stated and `brsr-app.html` now enforces in code, with a bulk-approve button that cannot satisfy the gate on its own.
