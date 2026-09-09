# Product Spec — ESG Disclosure Profile Viewer (Tier 1 MVP)

**Revision 13 — 9 Sep 2026.** Current. Phase 1 is built, demonstrated and unchanged. The BRSR extraction app is in the repository as **`brsr-app.html`**, generated from `app-src/brsr-app.template.html`. The four changes in `brsrapp-fix-spec.md` have landed, and the accuracy measurement is no longer blocked — see **Phase 3 status** below. Loose copies named `brsrapp.html`, `brsrapp2.html` and `brsrapp3.html` are earlier downloads of that same built file; `brsrapp3.html` matches the current one exactly.

**Full change history, with the reasoning behind each decision, is in `CHANGELOG.md`.** It was moved out of this file: eleven stacked revision notes had grown longer than some of the sections they described.

## Phase 3 status — the extraction app exists

`brsr-app.html` reads a BRSR or sustainability report PDF and generates a profile from it, entirely in the browser. It is **not** part of the Tier 1 build and does not change anything in this spec; the viewer it produces is the same one specified here.

What it establishes, and what it does not:

- **Established:** extraction needs no AI model, no network and no per-report cost. It is regex plus geometric layout parsing, so failures are deterministic and traceable to a pattern rather than probabilistic.
- **Established:** the review gate works as a product. Every indicator must be approved or excluded before a profile can be generated — enforced in code, not by convention.
- **Not established: accuracy.** Nobody has run it against a report with known-correct answers. Until that number exists, the review model — whether a client can check their own profile or whether Debraj must — stays open.
- **A defect recorded here previously was not real.** This spec said the app mis-located two of the nine principles on the bundled test PDF. It does not: that PDF holds exactly nine lines able to anchor a principle, on the nine correct pages, and both the current app and the older copies already produced those ranges. The weakness behind the claim was genuine — the Section C page was found and then ignored, so the first "Principle *n*" line anywhere won — and it is now fixed, which matters for annual reports where the GRI index and contents pages name principles too. **The accuracy measurement is no longer blocked by anything.**
- **All four changes in `brsrapp-fix-spec.md` have landed:** the principle search is fenced to Section C; bulk approval can only take indicators whose every figure was read with high confidence, so the review gate still means something; review state survives a closed tab; and an audit trail of every figure, with its page, confidence and status, can be downloaded.

See `brsrapp-fix-spec.md` for the changes, `phase3-spike-brief.md` for the measurement that follows, and `phase3-architecture.md` for the wider design.

## How to verify a change

```bash
node tools/test.js          # 107 checks against the real data
python3 tools/convert.py    # 9 conversion checks; refuses to write on failure
```

`tools/test.js` runs the shipped `app.js` against the shipped data file via a minimal fake DOM, so it tests the real code path. It covers filter counts, framework provenance, indicator codes, chart geometry, grouping and CSV integrity. It covers **nothing visual** — layout, spacing and overflow need a browser.

Bugs it has caught, all of which looked fine on screen: framework tags leaking onto non-BRSR rows, the CSV export losing the "GRI" prefix, two rows losing their indicator codes to non-breaking spaces, and charts min-max scaling instead of using a zero baseline.

## Overview

A single-page web view that displays one company's ESG (Environmental, Social, Governance) disclosures as a filterable table. Sustainability disclosures — the kind published in an Indian BRSR (Business Responsibility and Sustainability Report) or a GRI-style report — are normally buried in a 300-page PDF. This tool presents them as scannable rows a viewer can filter and search in seconds.

It is built as a **demo the owner presents live** to clients and colleagues. It is the viewer half of a larger idea; report upload and automatic extraction are explicitly **not** part of this build.

Reference for layout and behaviour: https://www.escortskubota.com/esg/profile

## Project Type

Single-view interactive data table with two filters and a search box. One HTML page. No routing, no tabs, no navigation.

## Audience & Access

- **Primary user:** the project owner, presenting the page on his own screen to an audience.
- **Access:** opened locally by double-clicking, or from a static host. No login.
- **Implication for UX:** a human is always narrating. Do **not** add onboarding modals, tooltips explaining what ESG is, help text, or first-run tours. The page must look finished to a professional audience and nothing more.

---

# THE SOURCE DATA — read this before anything else **[CHANGED]**

The real data lives in **`ESGReport.xls`** in the project root. It is an export from the Churchgate Partners ESG portal for Escorts Kubota Limited. It has been inspected; the facts below are measured from the file, not assumed.

## File facts

- Format: **legacy Excel (BIFF / CDFV2)**, not `.xlsx`, despite being openable in Excel. ~988 KB.
- **One sheet**, named `Profile`.
- `B3` holds the company name: `Escorts Kubota`.
- **Row 6 is the header row.** Rows 1–5 are banner/blank. **Data runs from row 7 to row 669**, giving **663 disclosure rows**. Trailing rows past the last populated row are empty and must be skipped.
- Column `B` (2) and columns 24–26 are entirely empty. Ignore them.

## Column map

| Col | Header | Populated | Notes |
|-----|--------|-----------|-------|
| A (1) | Category | 663 | 28 distinct values — see below |
| B (2) | *(none)* | 0 | ignore |
| C (3) | Sub Factor | 663 | the row title |
| D (4) | Keywords | 612 | comma-separated; 84 distinct tags |
| E (5) | Link1 | 663 | always present |
| F (6) | Link2 | 197 | |
| G (7) | Link3 | 52 | |
| H–J (8–10) | Link4, Link5, Link6 | 0 | empty in this export — still parse them, a future export may use them |
| K (11) | Metrics 1 | 96 | numeric value |
| L (12) | Units 1 | 96 | descriptive label for that value |
| M–V (13–22) | Metrics 2–6 / Units 2–6 | 74 / 69 / 17 / 7 / 2 | same value+label pairing |
| W (23) | Highlights | 663 | narrative text |

### Links — the critical parsing detail

**The cell text is the label; the URL is stored separately as the cell's hyperlink target.** There are **912 hyperlinked cells** across the Link columns. Reading only the cell text loses every URL.

Example, cell `E7`:
- text: `Integrated Annual Report 2026 (Page 49,52)`
- hyperlink target: `https://static.escortskubota.com/new/pdf/2026/june/EKL_Annual_Report_FY_2025-26.pdf`

A minority of link cells have text but no hyperlink target. Those must still render — as plain text, not as a dead link.

Link labels are mostly `Integrated Annual Report 2026` (554 rows), with the remainder pointing at policy PDFs, AGM notices, shareholding patterns, and company web pages.

### Metrics — value + unit pairs

Each of the six slots is a **number in the Metrics column and a descriptive label in the matching Units column**. The label is not a bare unit — it carries the year and the measure:

| Sub Factor | Pairs |
|---|---|
| Amount of GHG Emissions | `14629136.19` / `GHG Emission 2026 (tCO2e)`; `13125143.81` / `GHG Emission 2025 (tCO2e)`; `1072290.39` / `GHG Emission 2024 (tCO2e)` |
| GHG Emission Scope Breakdown | six pairs — Scope 1/2/3 for 2026 and 2025 |
| Amount of Water Usage | `340602.16` / `Water Consumption 2026 (KL)` + 2025, 2024 |
| GHG Reduction Target | `25` / `By 2030 (%)` |
| Dedicated Executive ESG Role | `6` / `Dedicated ESG Executives (No.)` |

96 of 663 rows carry at least one metric. Values range from single digits to ~14.6 million and include decimals. **Do not round, reformat, or unit-convert.** Add thousands separators for display only; keep the source value intact in the data file.

Some Unit labels have trailing spaces (e.g. `Dedicated ESG Executives (No.) `). Trim on extraction.

### Highlights

Median 423 characters, mean 556, max **3,676**. 113 rows exceed 1,000 characters and 12 exceed 2,000. The shortest is 3 characters. This is why the clamp-and-expand behaviour below is mandatory — without it, single rows run several screens tall.

### The 28 categories, in file order

Each category appears as **one contiguous block** — the file is already sorted, so grouping requires no re-sorting.

| Category | Rows | Theme |
|---|---|---|
| Management Approach | 3 | Overview & Approach |
| Company Overview | 15 | Overview & Approach |
| Board of Directors | 16 | Governance |
| Environment | 82 | Environment |
| Social | 135 | Social |
| Governance | 112 | Governance |
| Resilience | 11 | Governance |
| Materiality Assessment | 30 | Assurance & Recognition |
| Awards and Recognitions | 6 | Assurance & Recognition |
| Verification and Assurances | 14 | Assurance & Recognition |
| Ratings and Indices | 11 | Assurance & Recognition |
| ISO and Certifications | 5 | Assurance & Recognition |
| Memberships | 4 | Assurance & Recognition |
| Partnerships | 2 | Assurance & Recognition |
| ESG Videos and News | 1 | Assurance & Recognition |
| Corporate Information | 19 | Overview & Approach |
| Profile Sources | 48 | Assurance & Recognition |
| BRSR Section A: General Disclosures | 26 | BRSR Disclosures |
| BRSR Section B: Management And Process Disclosures | 12 | BRSR Disclosures |
| BRSR Section C: Principle 1 | 11 | BRSR Disclosures |
| BRSR Section C: Principle 2 | 9 | BRSR Disclosures |
| BRSR Section C: Principle 3 | 23 | BRSR Disclosures |
| BRSR Section C: Principle 4 | 5 | BRSR Disclosures |
| BRSR Section C: Principle 5 | 17 | BRSR Disclosures |
| BRSR Section C: Principle 6 | 21 | BRSR Disclosures |
| BRSR Section C: Principle 7 | 3 | BRSR Disclosures |
| BRSR Section C: Principle 8 | 11 | BRSR Disclosures |
| BRSR Section C: Principle 9 | 11 | BRSR Disclosures |

**Theme totals — use these to verify the conversion:** Overview & Approach 37 · Environment 82 · Social 135 · Governance 139 · BRSR Disclosures 149 · Assurance & Recognition 121 · **total 663**.

**There is no Environmental/Social/Governance column in this file.** The first version of this spec assumed one. Environment, Social and Governance are three of the 28 categories and together cover only 329 of 663 rows. Any filter built on a per-row E/S/G value will hide half the report. Use the theme mapping above instead.

### Keywords

84 distinct tags across 612 rows, comma-separated in one cell. Most frequent: BRSR (149), Metrics (120), Employees (94), Board of Directors (70), SEBI: Essential (63), Policies (61), Risk Control (46), SEBI: Leadership (42), Initiatives (37), Diversity and Equality (29), Human Rights (25), Reporting (22), Waste Management (21). Split on comma, trim each, drop empties.

---

## Data Conversion — one-time build step **[CHANGED]**

Convert `ESGReport.xls` into `data/disclosures.js` **once, at build time**, and commit the result. The page must never read the `.xls` at runtime.

Practical notes for whoever writes the converter:

- The file is legacy BIFF. `openpyxl` **cannot** read it. Either convert to `.xlsx` first (LibreOffice headless: `soffice --headless --convert-to xlsx`) and then read with `openpyxl`, or read the original with `xlrd`. If `xlrd` is used, note it does not expose hyperlink targets in all versions — the LibreOffice-then-openpyxl route is the verified one and preserves all 912 hyperlinks.
- **This converter is a one-off developer tool, not a project dependency.** Nothing it needs may end up in the shipped page. The shipped page still has **zero** dependencies. Flag to the owner before installing anything, per `CLAUDE.md`.
- Keep the converter script in the repo (`tools/convert.py`) so the owner can re-run it when a new export arrives, and document the command in the README in plain language.

**Verification the converter must pass before the data file is committed** — print these and check them:

1. Row count is exactly **663**.
2. Every row has a non-empty `subfactor`, `category`, `theme` and `highlights`.
3. Every `category` maps to a theme; **zero** rows fall through to a default.
4. Theme counts match the table above exactly.
5. Total document links parsed is **912 with URLs**, plus any label-only links counted separately.
6. Rows with at least one metric is **96**.
7. Every metric has a matching non-empty unit label, and every unit label a value — no orphans in either direction.
8. Distinct keyword count is **84**.

If any check fails, stop and report it rather than shipping a data file that quietly drops rows.

### Output shape — `data/disclosures.js`

A plain assignment to a global. **Not** `fetch()`, **not** JSON loaded over HTTP — the page must work when opened by double-clicking, and browsers block local file requests (a CORS restriction: pages opened from your hard drive aren't allowed to load other local files).

```js
window.ESG_DATA = {
  "company": "Escorts Kubota Limited",
  "updated": "17 Jul 2026",
  "themes": ["Overview & Approach", "Environment", "Social", "Governance", "BRSR Disclosures", "Assurance & Recognition"],
  "rows": [
    {
      "theme": "Overview & Approach",
      "category": "Management Approach",
      "subfactor": "Message from Managing Director",
      "keywords": ["Board of Directors", "Managing Director"],
      "documents": [
        { "label": "Integrated Annual Report 2026 (Page 49,52)", "url": "https://static.escortskubota.com/new/pdf/2026/june/EKL_Annual_Report_FY_2025-26.pdf" }
      ],
      "metrics": [],
      "highlights": "Nikhil Nanda (Chairman & Managing Director) and Akira Kato…"
    },
    {
      "theme": "Environment",
      "category": "Environment",
      "subfactor": "Amount of GHG Emissions",
      "keywords": ["GHG Emissions", "Metrics", "Climate"],
      "documents": [{ "label": "Integrated Annual Report 2026 (Page 281)", "url": "https://…" }],
      "metrics": [
        { "value": 14629136.19, "label": "GHG Emission 2026 (tCO2e)" },
        { "value": 13125143.81, "label": "GHG Emission 2025 (tCO2e)" },
        { "value": 1072290.39,  "label": "GHG Emission 2024 (tCO2e)" }
      ],
      "highlights": "…"
    }
  ]
};
```

Notes on the shape:

- **Flat `rows` array, not nested sections.** Rows stay in source file order; the theme and category are properties. Grouping happens at render time. This is a change from revision 1 — nesting made filtering across 28 categories awkward.
- `documents` entries with no hyperlink target get `"url": null`.
- `metrics` is always an array, empty when the row has none.
- `keywords` is always an array, empty when the cell was blank.
- A document link URL that is not `http://` or `https://` must be dropped rather than rendered.

---

## Functionality **[CHANGED]**

1. On load, read `window.ESG_DATA` and render all 663 rows, grouped under **category** heading rows, in source file order.
2. **Theme dropdown** — `All Themes` plus the six themes. Default `All Themes`.
3. **Keyword dropdown** — `All Keywords` plus the tags, alphabetical, each showing its count, e.g. `Employees (94)`. Default `All Keywords`.
   - When the theme changes, **rebuild the keyword list from the rows in that theme only**, with counts recalculated for that theme. If the currently selected keyword still exists in the new list, keep it selected; otherwise reset to `All Keywords`.
4. **Search box** — filters live on every keystroke. No button, no Enter.
5. The three filters combine with AND. A row shows only if it passes all three.
6. Category heading rows appear only when at least one row beneath them is visible; otherwise the heading is hidden too.
7. The count line updates: `Showing 82 of 663 disclosures`.
8. When nothing matches, the table is replaced by an empty state with a `Clear filters` button that resets all three controls.
9. **Download CSV** exports the rows currently visible under the active filters.
10. **Print / Save as PDF** opens the browser print dialogue against a print stylesheet, again reflecting the active filters.

Both exports respect the filters — exporting the filtered slice is the entire point of having them, since the unfiltered data already exists as `ESGReport.xls`. See the Export section below.

**Search scope:** `subfactor` + `category` + all `keywords` + all metric `label`s + `highlights`. Case-insensitive substring match. Document labels are **not** searched — 554 rows share the same label and would swamp results.

**Performance.** 663 rows × a long text cell each is enough DOM that naive full re-rendering on every keystroke will feel sluggish. Build each row once at startup, then toggle visibility on filter — do not rebuild rows. Debounce the search input by ~120 ms. Verify by typing quickly in the search box and confirming no visible lag.

---

## Screen & Content Structure **[CHANGED]**

Single column, max width ~1200px, centred.

**1. Header band** — company name (from `data.company`), subtitle `ESG Profile`, small meta line `Updated: {data.updated}`.

**2. Filter row** — sticky to the top on scroll. Theme dropdown, keyword dropdown, search input with a clear (×) affordance. Two export buttons sit at the right end of the row, visually secondary to the filters: `Download CSV` and `Print / PDF`. Count line below, left-aligned, muted.

**3. Table** — sticky header row.

| Column | Width | Content |
|--------|-------|---------|
| Sub Factor | 20% | row title |
| Keywords | 15% | small pill labels, wrapped |
| Documents | 12% | one link per line, label text as the link; plain text when no URL. Real links — `target="_blank"` with `rel="noopener noreferrer"`. **Do not suppress clicks.** Revision 1 called for `preventDefault` because sample URLs were placeholders; these URLs are real and must work. |
| Highlights | 53% | metrics block (when present) then narrative text |

**Category heading rows** — full-width, spanning all columns, accent background, white bold text, carrying the category name.

**Metrics block.** Renders at the top of the Highlights cell, above the narrative, only when the row has metrics. A horizontal wrapped row of small stat blocks: the value large and prominent with thousands separators, the label small and muted beneath it. Six blocks must wrap cleanly without overflowing the cell. Metrics live inside the Highlights cell rather than in their own column because only 96 of 663 rows have them — a dedicated column would be 85% empty.

**Long-text handling.** Clamp each narrative to ~4 lines with a fade-out, plus a `Show more` / `Show less` **real `<button>`** below it. The metrics block is never clamped. Rows collapse back to clamped state whenever filters change.

**4. Empty state** — centred, `No disclosures match your filters.` and a `Clear filters` text button.

**5. Footer** — one quiet line. Nothing else.

## Logic

Filtering only. No scoring, no calculation, no derived metrics beyond display formatting.

**Inputs:** selected theme (string), selected keyword (string), search query (string).

```
visible = themeMatch AND keywordMatch AND searchMatch

themeMatch   = (theme === "All Themes") OR (row.theme === theme)
keywordMatch = (keyword === "All Keywords") OR (row.keywords includes keyword)
searchMatch  = (query is empty after trimming)
               OR query, lowercased, is a substring of the lowercased concatenation of
                  row.subfactor + row.category + row.keywords + row.metrics[].label + row.highlights
```

A category heading is visible if and only if at least one of its rows is visible.

**Edge cases:**

- Whitespace-only query is treated as empty.
- Empty `keywords`, `documents` or `metrics` arrays are valid and must render (empty cell, no dash, no placeholder).
- A 3-character highlight must render without a `Show more` button — only show the toggle when the text actually overflows the clamp.
- Filtering must never mutate the source array.

## Export **[NEW in revision 3]**

Two export routes, both **zero dependency** and both working on a page opened by double-clicking. Both act on **the rows currently visible under the active filters**, not the full 663.

### 1. Download CSV

A `Download CSV` button builds a CSV in the browser and triggers a download. CSV is a plain text table Excel opens natively.

- **Filename:** `esg-profile-{company-slug}-{YYYY-MM-DD}.csv`.
- **Columns, in this order:** Theme, Category, Sub Factor, Keywords, Documents, Metrics, Highlights.
  - Keywords: joined with `; ` (semicolon, **not** comma).
  - Documents: each as `Label (URL)`, joined with `; `. Label-only links render as `Label` with no parentheses.
  - Metrics: each as `label: value`, joined with `; `.
- **Escaping — this is where CSV exports usually break.** Highlights text contains commas, double quotes and line breaks, all of which corrupt a naive CSV. Every field must be wrapped in double quotes with any internal double quote doubled (`"` → `""`). Do not strip the line breaks — quoted fields may legally contain them and Excel handles it.
- **Encoding:** UTF-8 **with a byte-order mark (BOM)** at the start of the file. Without it Excel on Windows mangles accented characters and the ₹ symbol.
- **Line endings:** CRLF.

**Verification before this is called done:** export with no filters, open the result in Excel, and confirm the row count is 663 plus a header row and that no row has spilled across lines. Then export with a filter applied and confirm the count matches the on-screen count line. A CSV that looks fine in a text editor and breaks in Excel is the standard failure here — it must be opened in Excel to count as tested.

### 2. Print / Save as PDF

A `Print / PDF` button calls the browser's print dialogue. The user then chooses "Save as PDF". No PDF library.

A `@media print` stylesheet must:

- Hide the filter row, both export buttons, the clear affordances and the footer.
- **Unclamp every Highlights cell** and hide all `Show more` buttons — the clamp is a screen affordance and would truncate the PDF.
- Repeat the table header on every page (`thead { display: table-header-group }`).
- Avoid breaking a row across pages (`tr { break-inside: avoid }`) and avoid orphaning a category heading at the foot of a page (`break-after: avoid`).
- Print the company name, `ESG Profile`, the updated date, and a line stating the active filters and row count — e.g. `Environment · All keywords · 82 of 663 disclosures` — so a printed copy is self-describing.
- Use black text on white, remove background fills except a light tint on category headings, and print document links as their label followed by the URL in smaller text, since a printed link cannot be clicked.

**Note for the owner:** unfiltered, this runs to well over a hundred pages — median 423 characters of narrative per row and some over 3,600. Filtering before printing is the intended use.

### Explicitly not built

- **No real `.xlsx` file.** An `.xlsx` is a zip archive of XML; producing one means either a CDN library — which breaks the offline double-click demo — or a hand-written zip encoder, which is a large amount of fragile code for a formatting gain. CSV instead.
- **No Word export.** The HTML-file-named-`.doc` technique works but can trigger a "file format doesn't match extension" warning in Word, which is not acceptable in front of a client. Revisit only on a specific client request.
- **No PDF library** (jsPDF, pdfmake or similar). The print stylesheet produces better-paginated output at zero cost.

## Reporting Frameworks **[revised in revision 7]**

A fourth filter, alongside Theme and Keyword. **Frameworks are tags, not a partition** — a row can carry several, which is why they are not additional themes. Themes must continue to partition the 663 rows exactly.

| Framework | Rows | Provenance |
|---|---|---|
| BRSR | 149 | `BRSR` keyword in the source export |
| BRSR Core | 14 | `SEBI: Essential Core` keyword; maps cleanly onto SEBI's nine BRSR Core attributes |
| GRI | 149 | Published GRI–SEBI BRSR linkage document — 114 at indicator level, 35 at principle level |
| IFC | 49 | **Derived by alignment**, chained via GRI — not a published mapping |

### IFC — the weakest link in the filter, deliberately marked

Source: IFC, *Elevating ESG Reporting in Emerging Markets* (January 2025) and its companion benchmarking analysis. That work **rates alignment** between IFC Performance Standards and GRI at series level; it is not a crosswalk. The BRSR-to-IFC connection is **chained** — BRSR indicator → GRI disclosure → IFC PS — and no published document asserts the composition.

Consequently IFC tags carry `verified: false` and `level: "alignment"`, render with the hollow dashed styling, and state their derivation in the visible label. Tests assert that no IFC tag claims to be verified, that all 141 declare themselves alignment-derived, and that IFC never appears without a GRI tag to chain from.

`IFC_BY_GRI_SERIES` in `tools/brsr_indicators.py` holds the mapping with the caveats written above it. Three exclusions, each added after seeing the output rather than from theory:

1. **GRI 200-series** — the same source rates its IFC alignment as weak.
2. **GRI 2 and 3** — align with PS1 in the abstract, but in practice put e-mail, telephone and registered office under a risk-management standard.
3. **Principle-level GRI answers** — the union of a whole section's standards, which chained to nonsense (Section A includes GRI 401/405, so "CIN" became Labour and Working Conditions).

Tests assert that named admin rows carry no IFC tag and that no IFC tag is derived from a principle-level GRI answer.

**Known gap:** the IFC handbook's Tables C.3, D.2 and E.2 (GRI ↔ IFC PS, pages 65/71/75) could not be retrieved; only pages 1–52 were readable. If those contain a finer mapping, this should be replaced with it and promoted to verified.

### BRSR indicator codes

`tools/brsr_indicators.py` holds two transcriptions, deliberately kept apart:

- `INDICATOR_CODES` — subfactor title to BRSR indicator, from **SEBI's BRSR format, Annexure I to circular SEBI/HO/CFD/CMD-2/P/CIR/2021/562 (10 May 2021)**. The portal's titles follow SEBI's numbered questions in order, so matching is by title and position. All 149 rows are coded.
- `GRI_BY_INDICATOR` — indicator to GRI disclosures, from the linkage document's summary table.

Nine rows carry `-Core` codes (`P6-Core`, `P5-Core`, `P8-Core`): BRSR Core attributes from SEBI's 2023 circular, postdating the 2021 numbering and the 2022 linkage document.

**Indicator lookup is scoped to BRSR categories.** Subfactor titles are not unique — "Energy Consumption" appears under both Environment and Principle 6 — and an unscoped lookup silently tagged non-BRSR rows. A test asserts no framework tag appears outside the BRSR sections.

Titles containing non-breaking spaces must be normalised before lookup; two rows were silently missing their codes until that was handled.

### The GRI mapping

Source: **"Linking the GRI Standards and the SEBI BRSR Framework"**, GRI with the Bombay Stock Exchange, 2022 — https://www.globalreporting.org/media/ioqnxtmx/sebi_brsb_gri_linkage_doc.pdf

The document maps BRSR requirements to GRI disclosures at **indicator** level (P6-E3 → GRI 303-3, 303-5). The export carries only the principle and whether a row is an Essential or Leadership indicator — not the indicator number. The mapping is therefore applied at **principle level**, the finest granularity the data supports, and each tag carries the GRI standards for that BRSR section plus a `source` field naming the document.

`BRSR_GRI_LINKAGE` in the converter holds the transcription, one entry per BRSR category. Tests assert several entries against the document — Principle 6 must include GRI 302/303/305/306, Principle 9 must include GRI 418 and must not include GRI 305 — so a transcription error fails the build rather than reaching a client.

**No GRI tag is applied outside the BRSR sections.** The linkage document does not cover them.

### Why the provisional marking is gone

Revision 6 tagged 445 GRI and 324 IFC rows by keyword matching and marked them provisional on screen. That marking existed because the mapping was guesswork. Rebuilding on the linkage document removed the guesswork, so the marking, the dropdown suffix and the warning banner were all removed. **The `verified` flag remains in the data**: a future reviewed mapping could reintroduce unverified tags, and the hollow pill styling is still there to render them.

### Refining further

Two routes, both narrowing the mapping rather than broadening it:

1. **Indicator-level precision.** Match each of the 149 BRSR rows to its specific BRSR indicator number, then read the GRI disclosure straight off the linkage document. Judgment moves to identifying the indicator, which is far more constrained than judging GRI relevance.
2. **Beyond BRSR.** The other 514 rows need mapping by hand. `ESG-Framework-Mapping.xlsx` is the worksheet; returning it as `framework-mapping.csv` overrides the linkage-derived tags.

**Unresolved:** GRI licensing for commercial use in software, and whether IFC Performance Standards are meaningful for a company with no IFC financing.

## Trend Charts **[NEW in revision 5 — 7 Sep 2026]**

Metric labels carry the measure, the year and the unit (`GHG Emission 2026 (tCO2e)`). The converter splits them and groups them into series. **45 series exist: 32 with three or more years, 13 with two.**

**Series are built in the converter, not the browser.** Parsing belongs where it can be verified and reported on; the page only draws what it is handed. Each row gains `series` (multi-year) and `standalone` (single values, targets, counts). `metrics` is left untouched so the CSV export is unaffected.

**Rules:**

- **Three or more years → a column chart.** Columns, not a line: three annual disclosures are three separate figures, and a line implies values between them that were never reported.
- **Two years → a change statement**, e.g. "33.3% in 2026, down from 85.71% in 2025". Two points carry no more information than the two numbers.
- **The baseline is always zero.** A truncated axis exaggerates change; this is the most common way a chart misleads.
- **Exact values are printed beneath every chart.** Nothing is readable by eye alone, and no precision is lost.
- Rendering is hand-drawn inline SVG. **No charting library** — a CDN link would break the offline double-click demo.

### Discontinuity flagging — the part that matters

Any year-on-year ratio of **3× or more** marks a series as discontinuous. A jump that large is usually a change in what was counted, not in what happened.

**Five series are currently flagged**, and one is the reason this rule exists:

> **Amount of GHG Emissions** — 2024: 1,072,290.39 · 2025: 13,125,143.81 · 2026: 14,629,136.19 tCO2e.
> Charted naively this reads as a twelvefold rise in emissions. It is not. The 2026 and 2025 totals reconcile **exactly** to Scope 1 + 2 + 3; 2024 has **no scope breakdown disclosed at all** and almost certainly excludes Scope 3, which alone was 13,076,508.88 in 2025. The boundary widened; the emissions did not.

Flagged series are still charted — the owner's decision on 7 Sep 2026 — but the marking is deliberately hard to miss:

- bars before the break are drawn **hollow with a dashed outline**, so they read as not comparable;
- a **dashed vertical rule** marks the break;
- a **caption sits under the chart**, not in a tooltip, because tooltips are never seen in a live demo;
- the whole block switches to a warning colour.

`SERIES_NOTES` in the converter holds specific captions where the cause is established; everything else gets a generic "reporting basis may differ" caption and appears on the review list printed on every run. **Four of the five flagged series still have the generic caption and need investigating.**

## Anonymisation **[NEW in revision 4 — decision settled 7 Sep 2026]**

The demo does **not** carry the real company name. `tools/convert.py` produces an anonymised build by default; `--real` produces the unmodified one.

**What is replaced:** company name and abbreviation throughout all narrative text; the 16 board members' names, mapped to stable placeholders `Director A` … `Director P`; every document link's destination URL; CIN, registered address, telephone numbers, email and social handles; named third-party organisations appearing in biographies; sector-identifying terms.

**What is withheld entirely:** the narrative text of all 16 `Board of Directors` rows, replaced with a short note. Those biographies name previous employers, universities, other board seats and industry bodies — a combination that identifies the individual in a single search, and through them the company. Pattern replacement cannot reliably catch it, so the text is removed rather than filtered.

**What is deliberately untouched:** every reported figure. Emissions, water, energy and headcount values are exactly as published. Altering them would breach the project's ground rule against modifying real reported data.

**Residual risk — state this plainly to anyone who asks.** The build is *de-branded, not anonymous*:

- the figures are real and published, so they can be matched back to the filed report;
- the sector remains legible from the narrative;
- the converter prints a **residual review list** of proper nouns it was never told about (award names, industry bodies, subsidiaries) on every run, and that list requires human review.

Anyone extending the converter must keep two behaviours: **nothing is written when a check fails or the leak scan finds something**, and the residual list is printed every run.

## Data Source

| Element | Source | Format | Access | Update Frequency |
|---------|--------|--------|--------|-----------------|
| Disclosure rows | `ESGReport.xls` in the project root, converted once at build time | `data/disclosures.js` (global assignment) | Ready | Static; re-run the converter when a new export arrives |

No API. No network calls. No credentials.

## Brand & Visual Direction

Clean neutral default — professional and restrained.

- **Palette:** near-white page, white table, dark neutral text (#1a1a1a), muted grey secondary. One accent used sparingly for category headings, focus states and links, defined once as `--accent`.
- **Type:** one system font stack. No web fonts.
- **Density:** generous row padding, subtle borders. Presented on a projector — 16px minimum base text, strong contrast.
- **Motion:** hover and focus transitions only.
- **Responsive:** desktop-first; must not break below 900px. Mobile-optimised layout not required.

**Accessibility:** real `<label>` elements on both dropdowns and the search input (visually hidden if needed), `<th scope="col">` on the header row, `aria-live="polite"` on the count line, and a real keyboard-reachable `<button>` for Show more.

## Stack

- **Framework:** none. Plain HTML, CSS, vanilla JavaScript.
- **Build step:** none for the page. The data converter is a separate one-off script.
- **Runtime dependencies:** zero. No CDN links, no charting library, no CSS framework.

## API & Credentials

None. This build makes no external requests and requires no key, token, or credential. If a future extension needs one, it goes in a separate environment file and never into HTML or JavaScript.

## Suggested File Structure

```
esg-dashboard/
├── index.html
├── styles.css
├── app.js
├── data/
│   └── disclosures.js      # generated — do not hand-edit
├── tools/
│   └── convert.py          # one-off: ESGReport.xls -> data/disclosures.js
├── ESGReport.xls           # source export
├── product-spec.md
├── CLAUDE.md
└── README.md
```

The README must explain, in plain language: how to open the page, how to re-run the converter when a new export arrives, what the theme mapping is, and the warning that a category not present in the mapping will fail the conversion check rather than silently vanish.

## Left Out of This Build — Tier 1 Only

Do not build any of the following, even if it looks like an obvious improvement:

- **Report upload of any kind.** No file input, no drag-and-drop, not even disabled.
- **Automatic extraction** from PDFs or reports. No parsing at runtime, no server.
- **Reading the `.xls` in the browser.** Conversion is offline; no spreadsheet library ships with the page.
- **The remaining reference-page dropdowns:** asset manager, global framework, ESG ratings, industry lens, BRSR filter.
- **`.xlsx`, `.doc` or `.docx` file generation, and any PDF library.** CSV download and print-to-PDF are now in scope — see the Export section. Nothing beyond those two.
- **Profile / DocuLink / Factsheet view toggles.**
- ~~Charts or trend graphs from the metrics.~~ **Moved into scope 7 Sep 2026 — see Trend Charts below.**
- **Multiple companies** or any company selector.
- **View counters, chat widgets, feedback forms.**
- **Accounts, logins, roles, payments, databases, server-side logic.**
- **Multi-page navigation or routing.**
- **localStorage or any persistence.** Filter state resets on reload.

## Requested but not built **[NEW in revision 4]**

Raised in the GTM meeting of 21 Aug 2026. Recorded so nothing is lost and nothing is built by accident.

| Request | Position |
|---|---|
| Trend lines across indicators | **Data is ready — 40 rows already carry the same measure across two or three years.** Charts remain on the Left Out list; building them is a scope decision, not a data problem. Hand-drawn SVG would keep the zero-dependency rule intact. The "24 indicators" referred to in the meeting have not been identified — the file has 96 rows carrying figures. |
| Company screener (share price, market cap, listings) | **Mostly already present.** The `Corporate Information` category carries listing stock exchange, paid-up capital, employee count, incorporation year, financial year end, address and business activities. Missing: market cap and share price. **Live share price is out** — it needs an API, credentials and a server, and breaks the double-click demo. Under the agreed annual update cadence a share price would be stale and misleading; market cap as a dated annual snapshot is acceptable. |
| ESG ratings (CRISIL, EcoVadis and others) | **Eleven already present** in the `Ratings and Indices` category — CRISIL ESG, CRISIL Credit, Sustainalytics, S&P Global, LSEG, CSR Hub, NSE, ICRA, ESGRisk.ai, SES, IiAS. These are safe because the company disclosed them itself. **EcoVadis is different**: scorecards are confidential by default, shared only with authorised partners, and public sharing depends on subscription tier and a 12-month validity window. Displayable only with the company's active permission and an in-date scorecard. |
| Framework tagging (CDP, GRI, EU Taxonomy, IFC) | **Technically trivial, commercially not.** The filter mechanism is identical to the existing keyword filter. The work is mapping 663 rows to each framework — professional judgment, not build effort. **GRI licensing must be settled first**: reproduction for preparing a report is permitted, but commercial use of GRI content in software and tools goes through GRI's licensing programme. CDP, EU Taxonomy and IFC terms have not been checked. |
| Annual update cadence | **Already how the system works.** The converter runs when a new export arrives; nothing fetches live data. No work required. |
| Both hosting options | **Already true.** The folder opens by double-click and also works on any static host unchanged. No work required. |

## Open Questions

1. **The E/S/G filter mapping needs the owner's sign-off.** The source file has no Environmental/Social/Governance column. A rule-based classification reaches 84% coverage — 356 rows from the category name, 111 from BRSR principle mapping, 38 from BRSR Sections A and B, 53 from keywords — giving roughly E 120 / S 212 / G 226, with **105 rows that are genuinely none of the three** (Profile Sources, Corporate Information, Materiality Assessment, Verification, Ratings, Awards, Memberships, ISO certificates). Two decisions: how those 105 are presented, and whether the owner accepts the judgment calls, notably BRSR Principle 2 under Environmental and Supply Chain under Social. **Do not build this filter until the mapping is signed off** — a client may ask the owner to defend any given row's classification.
2. **Residual proper nouns.** The converter's review list currently holds around 30 entries. The owner should mark which are identifying; they then go into `THIRD_PARTY_ORGS` or `LITERALS`.
3. **`updated` date** is `17 Jul 2026`, carried from the reference page because the export has no date field. Replace when a better source exists.
4. **Number grouping** currently uses international thousands separators (14,629,136.19). If the audience is primarily domestic, Indian grouping (1,46,29,136.19) may read better. One-line change.
5. **Visual verification is outstanding.** Filter logic, search and CSV export are tested against the real 663 rows. The rendered page has not been checked in a browser. The sticky filter bar's offset above the sticky table header is the most likely thing to be wrong.

If any instruction here conflicts with something the owner says, **the owner wins** — but flag the conflict against the Left Out list first, since that list is the scope boundary.
