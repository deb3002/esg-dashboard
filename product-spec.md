# Product Spec — ESG Disclosure Profile Viewer (Tier 1 MVP)

**Revision 3 — 10 Aug 2026.** Adds filtered CSV download and print-to-PDF (see **Export**). These were on the "Left Out" list in revisions 1–2; the owner has moved them into scope. `.xlsx`, Word and PDF-library generation remain out.

**Revision 2 — 10 Aug 2026.** Superseded the original spec, which was written before the real source data was available and assumed ~25 hand-authored sample rows. The real export (`ESGReport.xls`) is far richer and does not have the shape the first version assumed. Sections that changed are marked **[CHANGED]**.

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
- **Charts or trend graphs from the metrics.** The numbers display as values only. Several rows carry three years of the same measure and are begging to be charted — that is a deliberate later decision, not this build.
- **Multiple companies** or any company selector.
- **View counters, chat widgets, feedback forms.**
- **Accounts, logins, roles, payments, databases, server-side logic.**
- **Multi-page navigation or routing.**
- **localStorage or any persistence.** Filter state resets on reload.

## Open Questions for Claude Code

1. **Real company data — confirm before building.** This export is Escorts Kubota's genuine published data under their own name, including real emissions figures and links to their annual report PDFs. Ask the owner whether the demo should carry the real company name and links, or be anonymised to a placeholder name with links stripped. **Do not assume.** If anonymising, the converter needs a flag for it and the highlights text also names individuals and the company throughout — a name swap alone will not anonymise it.
2. **`updated` date.** The reference site shows `17 Jul 2026`; the export itself carries no date field. Confirm the value or read it from the file's modification date, and note the choice in the README.
3. **Theme names** are proposed, not fixed. If the owner prefers different labels or a different split, that is a one-line change in the converter's mapping — but the six-theme structure and the row counts must still reconcile to 663.
4. **Accent colour** is unspecified. Pick a sensible default, define it as `--accent`, note the choice in the README rather than asking.
5. If any instruction here conflicts with something the owner says mid-build, **the owner wins** — but flag the conflict against the Left Out list first, since that list is the scope boundary.
