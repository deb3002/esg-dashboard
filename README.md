# ESG Disclosure Profile Viewer

A single-page viewer for one company's ESG (Environmental, Social, Governance) disclosures, shown as a filterable, searchable table instead of a 300-page PDF.

## How to open it

Double-click **`index.html`**. It opens in your browser — no install, no server, no internet needed. Safe for a live demo: nothing on the page makes network calls or saves anything.

## Checking it still works

Two commands, from a Terminal opened in this folder:

```bash
node tools/test.js          # 107 automated checks — should end "ALL CHECKS PASSED"
python3 tools/convert.py    # rebuilds the data file and prints its own checks
```

The first loads the real page code and the real data and checks the filters, the framework mappings, the trend charts and the CSV export all behave. It catches the kind of silent breakage you would never see by looking — rows quietly vanishing, or the export losing a column.

**It does not check how anything looks.** Layout and appearance still need you to open the page.

## What's on the page

- **Theme dropdown** — six broad groupings covering all 663 disclosures.
- **Keyword dropdown** — 84 tags. Its list and counts rebuild to match whichever theme is selected, so it only ever offers keywords that will actually return rows.
- **Search box** — filters as you type, across the disclosure name, category, keywords, metric labels and the narrative text.
- All three combine — a row shows only if it matches all of them.
- **Download CSV** — exports whatever rows are currently visible under your filters.
- **Print / PDF** — opens your browser's print dialogue with a print-specific layout: full narrative text (not truncated), table header repeated on each page, and a line at the top recording which filters were active.

Long narrative text is shortened to about four lines with a **Show more** link. Rows with reported figures show them above the text.

## The report-to-profile app

**`brsr-app.html`** — double-click it. Drop in a **BRSR or a GRI
sustainability report** PDF, check what it read, and it gives you the
profile page.

It works out which kind of report you gave it. A BRSR is recognised by its
Section C and Principle headings; a GRI report by its content index. You
don't have to say which.


Nothing is uploaded anywhere. The report is read inside the page, on your
own computer, with no internet connection needed. You can hand the file to
a client and it will work the same way on their machine.

How it goes:

1. **Drop the PDF in.** It finds the BRSR section inside the annual report,
   and reads each table from its printed gridlines — so a year heading that
   spans three columns, and rows whose label is merged from the row above,
   both come out right.
2. **Check what it read.** Every figure is listed with the page it came
   from, so you can check it against the report. Type over anything wrong,
   drop a figure, or exclude a whole indicator. Nothing is generated until
   you have been through them.

   There is a button to approve the indicators whose every figure was read
   with high confidence — it says how many that is, and it will not touch
   anything uncertain or anything with no figures. Those are the ones worth
   a person's attention, so they stay for you. On a real annual report it
   clears about a quarter of them.

   **Your review is saved as you go**, under a fingerprint of the PDF
   itself, so closing the tab does not cost you an hour. Reopen the same
   report and it offers to pick up where you left off; a different report
   never restores the wrong work. If the browser will not allow storage,
   the app says so and still warns you before you leave with work
   unchecked.
3. **Press Generate.** You get a preview, plus three downloads: the
   finished profile page as a single HTML file, the data file if you would
   rather drop it into the existing viewer, and an **audit trail** — one
   CSV row per figure with its page, what it was read from, its
   confidence, whether it was approved, excluded or dropped, and what the
   extractor first read if you corrected it. For an investor relations
   team that file is often worth more than the profile: it is what turns
   "our figures are traceable" into something you can hand over.

### Reading a GRI report

A BRSR is a form, so its questions are found by position. A GRI report has
no fixed shape, so the **GRI content index** is used instead — the table
every GRI report carries listing each disclosure and where to find it.

The index has no gridlines, but it does have columns: the disclosure code,
its title and the answer each sit at their own position on the page, often
in two panels side by side. Those positions are what the app splits on. It
does **not** carry a copy of GRI's own list of disclosure titles, which
keeps the licensing question out of the software.

Measured against one real GRI report (QTS, 2025, 37 pages): **62
disclosures across 13 GRI series**, 42 carrying narrative text, grouped
onto the existing themes — 35 Governance, 14 Environment, 13 Social.

Expect a GRI profile to be **lighter on figures than a BRSR one**. Most
GRI reports put their numbers in charts and tables in the body and use the
index only to point at them, and a report written "with reference to" the
GRI Standards rather than "in accordance with" carries fewer disclosures
to begin with.

### What you should not assume about it

- **Its accuracy on real filings is only partly measured.** It has been run
  against two real filings. A standalone filed BRSR (42 pages): all nine
  principles found, 88 indicators, 204 figures with their years, units and
  page numbers. A BRSR filed inside a 513-page integrated annual report
  (Escorts Kubota, FY 2024-25): 108 indicators, 216 figures, 89 trend
  series, in under four seconds. Tables checked against the printed page —
  energy, water, waste, air emissions, Scope 1, 2 and 3 — came out as
  published. That is two reports, not a measured accuracy rate;
  `phase3-spike-brief.md` still describes the proper measurement.
- **Some tables still yield nothing.** Tables whose layout it cannot read
  are skipped rather than guessed at, so the risk is a missing figure, not
  a wrong one.
- **One measure can still hold two values for a year.** Where a table
  repeats a row label under different sub-headings and the sub-heading is
  not picked up, two different figures can end up under one name — six of
  the annual report's 216 figures. The values and their pages are right;
  the name does not tell them apart. The review step shows both.
- **The Highlights text is uneven.** Where an answer is a table, the table
  is written out as readable prose. Where the report lays a question and
  its answer out inside a table, the text can still come through as
  fragments. Figures are unaffected — this is about the narrative column.
- **It reads digital text only.** A scanned report contains pictures of
  words, and no text can be pulled from it at all. The app says so rather
  than producing an empty profile.
- **It covers the BRSR section only** — roughly a fifth of a full profile.
  Board biographies, awards, ratings, memberships and corporate information
  are not in the BRSR and are not extracted.
- **The keyword filter will be thin.** Extracted profiles carry structural
  tags only (`BRSR`, `Principle 6`, `Essential`), because guessing keywords
  from wording is the mistake that produced 445 bad GRI tags once already.

### Rebuilding it

`brsr-app.html` is generated. To rebuild after changing the page or the
mappings:

```bash
python3 tools/build_app.py     # writes brsr-app.html
python3 tools/test_app.py      # drives it in a browser and checks the result
```

It bundles pdf.js, which is the only way to read a PDF in a browser. That
library is embedded in this one file and never reaches the shipped viewer —
`index.html` still has zero dependencies.

## The command-line version

If you would rather script it, the same extraction runs from a Terminal.

## Turning a report into a profile (new, and not yet proven)

There is now a second converter. `tools/convert.py` turns the portal's
spreadsheet export into a profile; `tools/extract_brsr.py` turns a **filed
BRSR inside an annual report PDF** into one.

It works in two steps, and the second one will not run until you have done
the first.

```bash
pip3 install pdfplumber                                  # once
python3 tools/extract_brsr.py extract annual-report.pdf  # 1. read the PDF
python3 tools/extract_brsr.py publish --data data/extracted.js   # 2. write it
```

`publish` will not overwrite an existing profile unless you pass
`--replace`. Your 663-row demo lives in `data/disclosures.js`; an extracted
profile covers the BRSR section only, so publishing over it would replace a
full profile with a fifth of one.

**Step 1** finds the BRSR section, splits it into SEBI's numbered
indicators, and pulls out every figure with its unit, its year and the page
it came from. It writes `tools/extraction/review.html`.

**Step 2 refuses to run** until you have opened that review file, checked
each figure against the page number shown, and marked every indicator as
`approved`, `corrected` or `not_disclosed` in `tools/extraction/review.json`.
This is deliberate. A missing figure is recoverable; a wrong emissions
figure published under a client's name, next to a link to their audited
annual report, is not.

### Reading a GRI report

A BRSR is a form, so its questions are found by position. A GRI report has
no fixed shape, so the **GRI content index** is used instead — the table
every GRI report carries listing each disclosure and where to find it.

The index has no gridlines, but it does have columns: the disclosure code,
its title and the answer each sit at their own position on the page, often
in two panels side by side. Those positions are what the app splits on. It
does **not** carry a copy of GRI's own list of disclosure titles, which
keeps the licensing question out of the software.

Measured against one real GRI report (QTS, 2025, 37 pages): **62
disclosures across 13 GRI series**, 42 carrying narrative text, grouped
onto the existing themes — 35 Governance, 14 Environment, 13 Social.

Expect a GRI profile to be **lighter on figures than a BRSR one**. Most
GRI reports put their numbers in charts and tables in the body and use the
index only to point at them, and a report written "with reference to" the
GRI Standards rather than "in accordance with" carries fewer disclosures
to begin with.

### What you should not assume about it

- **Its accuracy on real filings is unmeasured.** It has been tested only
  against a report generated from data we already had — that proves the
  machinery works, not that it reads real reports well. Measuring it
  properly is what `phase3-spike-brief.md` describes.
- **It covers the BRSR section only** — roughly a fifth of a full profile.
  Board biographies, awards, ratings, memberships and corporate information
  come from elsewhere and are not extracted.
- **It produces no keywords from the text.** The keyword tags on an
  extracted profile are structural facts from the form (`BRSR`,
  `Principle 6`, `Essential`) and nothing else. Guessing keywords from
  wording is the mistake that produced 445 bad GRI tags once already.

Check it with:

```bash
python3 tools/test_extract.py
```

## The Framework filter

A fourth dropdown filters by reporting framework. Three of the four are sourced directly. IFC is derived, and marked as such.

| Framework | Rows | Where it comes from |
|---|---|---|
| BRSR | 149 | Tagged in the source export by the ESG portal |
| BRSR Core | 14 | The portal's `SEBI: Essential Core` keyword |
| GRI | 149 | The published GRI–SEBI BRSR linkage document |
| IFC | 49 | **Derived by alignment** via GRI — weaker than the rest, see below |

### BRSR indicator numbers

Every BRSR row now carries its **indicator number** from SEBI's official format — `P6-E1`, `P5-E3`, `A18` — shown on the page beside the tag, along with the principle and whether it is an Essential or Leadership indicator. A Principle 6 energy row reads:

> **BRSR**  P6-E1 · Principle 6 · Essential (Core)
> **GRI**  302-1-a, 302-1-b, 302-1-c-i, 302-1-e, 302-3-a

Source: SEBI's BRSR format, Annexure I to circular SEBI/HO/CFD/CMD-2/P/CIR/2021/562 (10 May 2021). Your portal's row titles follow SEBI's numbered questions in the same order, so each row was matched to its indicator by title and position. **All 149 BRSR rows are coded.**

Nine rows carry a `-Core` code instead (`P6-Core`, `P5-Core`). These are the BRSR Core attributes introduced by SEBI's 2023 circular, which came after the numbering in the 2021 format.

### How the GRI mapping works

It comes from **"Linking the GRI Standards and the SEBI BRSR Framework"** (GRI with the Bombay Stock Exchange, 2022) — the official cross-reference between the two frameworks.

That document maps at **indicator** level, so now that every row has an indicator number, most rows get a precise GRI answer:

| Mapping level | Rows | What you see |
|---|---|---|
| Indicator | 114 | The exact GRI disclosures for that indicator, e.g. `303-3-a-i-v, 303-5-a` for water usage |
| Principle | 35 | All GRI standards linked to that BRSR principle |

The 35 principle-level rows are ones the 2022 linkage document has no entry for — mostly the BRSR Core attributes added in 2023, and a few indicators it marks "no direct linkage". They keep the coarser answer rather than being given a precise-looking guess. Each tag shows which level it used.

### IFC — read this before quoting it

IFC tags are **weaker than the BRSR and GRI ones**, and the page shows that: they render hollow with a dashed outline, and each one reads `PS3 · by GRI alignment` rather than just `PS3`.

Three things you should be able to say if a client asks:

1. **There is no published BRSR-to-IFC mapping.** What exists is IFC's January 2025 benchmarking work, which *rates alignment* between the IFC Performance Standards and GRI at series level — "IFC PSs have strong alignment with some Environment (GRI 300s) and Social (GRI 400s) topics". It is an assessment, not a crosswalk.
2. **The link is chained.** BRSR indicator → GRI disclosure → IFC Performance Standard. The first hop is official, the second is an alignment rating, and the join between them is our inference. No single document asserts that a given BRSR indicator maps to a given Performance Standard.
3. **It is deliberately narrow — 49 rows of 149.** Three exclusions, each because including them produced results that read as nonsense:
   - **GRI 200-series (economic performance)** — the same IFC source rates its alignment as weak.
   - **GRI 2 and 3 (general disclosures, material topics)** — mapping these to PS1 filed the company's e-mail address, telephone number and registered office under "Assessment and Management of Environmental and Social Risks". 26 admin rows in a 74-row bucket.
   - **Rows whose GRI answer is principle-level rather than indicator-level** — a principle-level answer is the union of every standard linked to that whole BRSR section, so chaining it put "CIN" and "Paid-up Capital" under Labour and Working Conditions.

What it does map: GRI 301/302/303/305/306 → **PS3** (Resource Efficiency and Pollution Prevention) · GRI 304 → **PS6** (Biodiversity) · GRI 401–409 → **PS2** (Labor and Working Conditions) · GRI 410 and 413 → **PS4** (Community Health, Safety and Security) · GRI 411 → **PS7** (Indigenous Peoples) · GRI 308 and 414 → **PS1** (supplier assessment, genuinely risk management).

Current spread: PS1 8 · PS2 17 · PS3 17 · PS4 5 · PS6 2.

Still worth settling: the IFC Performance Standards apply to IFC-financed projects, so if a client has no IFC involvement the tag may not mean much to them.

### Choosing a framework regroups the table

Select **IFC** and the table's section headings change from the source spreadsheet's categories to the **IFC Performance Standards** — PS1 through PS8 — the way IFC itself organises them. Select anything else and it groups by the original category.

Each heading carries three things: a code chip (`PS 3`, or `P6` for a BRSR principle), the full name, and a count of disclosures in that group.

Nine rows map to more than one Performance Standard. They're grouped under the first, and the row's own tag still shows the full list, so nothing is hidden by the grouping.

### Adding your own mappings

Fill in `ESG-Framework-Mapping.xlsx`, save the Mapping sheet as **`framework-mapping.csv`** in this folder with columns `Sub Factor`, `GRI`, `IFC`, and re-run the converter. Your answers override the linkage-derived ones. Write `None` for a row that maps to nothing.

**Still unresolved:** GRI licensing for commercial use in software goes through GRI's licensing programme. Referencing the linkage document is one thing; shipping it inside a product you charge for is another. Settle it before you sell this.

## Trend charts

Where a figure was reported for **three or more years**, a small column chart appears with the exact values printed underneath. Where only **two years** exist, you get a change statement instead — "33.3% in 2026, down from 85.71% in 2025" — because two points aren't a trend.

Columns rather than a line: three annual disclosures are three separate figures, and a line would imply values in between that were never reported. The baseline is always zero, so nothing is visually exaggerated.

### The orange warning on some charts

Some charts have an orange border, a dashed vertical line, hollow bars on the left, and a caption. That means a figure jumped by 3× or more between two years — which usually means **the basis of reporting changed, not the underlying number.**

The clearest example is GHG emissions: 1,072,290 in 2024, then 13,125,144 in 2025. That looks like emissions exploded. They didn't — the 2025 and 2026 totals include Scope 3 emissions and the 2024 figure doesn't. Scope 3 alone was over 13 million tonnes. The company started counting more, it didn't start emitting more.

**Five series are currently flagged. Only one has a verified explanation.** The other four — business travel, hazardous waste, e-waste, harassment complaints — carry a generic caption and need checking against the source report. Some are probably genuine changes; a falling harassment complaint count is good news, not an artefact. Once you know the cause, add the explanation to `SERIES_NOTES` near the top of `tools/convert.py` and it appears under that chart.

The converter lists every flagged series each time it runs, so this can't quietly drift.

## The data: real report, anonymised

The content comes from `ESGReport.xls` — 663 disclosure rows exported from a real company's ESG portal. On 10 Aug 2026 you decided this demo should **not** carry the real company name.

`tools/convert.py` replaces:

- The company name and its abbreviation everywhere they appear, including inside narrative paragraphs — not just the header.
- The 16 board members' names, with neutral placeholders (**Director A** through **Director P**), applied consistently so the same person is the same placeholder throughout.
- **The entire biography text for the Board of Directors rows.** Those 16 rows are replaced with a short note saying the biography is withheld in this build. See below for why.
- Every document link's destination URL, so the Documents column shows plain labels rather than links.
- Contact details, the CIN, the registered address, phone numbers and social media handles.
- Other companies named in director biographies, and sector-specific terms that would identify the business.

### What this does not do — read before showing anyone outside your team

This is **de-branded, not anonymous.** Three specific limits:

1. **The figures are real and unchanged.** The exact GHG emissions, water and energy numbers are untouched — deliberately, because inventing or altering a real reported figure is a line this project doesn't cross. But those figures are published in the company's filed report, so anyone who has them can match this demo back to the source.
2. **Director biographies were the biggest leak, which is why they're removed entirely.** A bio that names previous employers, universities, other board seats and industry bodies identifies the person in one search, and the person identifies the company. Search-and-replace cannot reliably catch that combination, so the text is withheld rather than filtered.
3. **The sector still shows through.** The narrative refers to farmers, machinery and construction equipment. The obvious phrases are genericised, but the kind of business is legible.

Every time the converter runs it prints a **residual review list** — proper nouns it found but was never told to replace, such as award names, industry associations and subsidiaries. Read that list. Anything on it that you consider identifying should be added to `THIRD_PARTY_ORGS` or `LITERALS` near the top of `tools/convert.py`.

### To use the real company name instead

```bash
python3 tools/convert.py --real
```

This restores the real name, the people and the working document links. It's a reputational decision, not a technical one — re-confirm it before running.

## Re-running the conversion when a new export arrives

Replace `ESGReport.xls` in this folder and run:

```bash
python3 tools/convert.py
```

**What it needs:** `openpyxl` (a free Python library that reads Excel files) and **LibreOffice**. LibreOffice is needed because `.xls` is the older Excel format, and it's also the only route that preserves the 912 document hyperlinks — the web addresses live separately from the visible text in the cell, and the simpler libraries drop them.

If `openpyxl` isn't installed:

```bash
python3 -m pip install --user openpyxl
```

Both run only on your computer to regenerate the data file. Neither ships with the page — the page itself still has **zero** dependencies.

### What it prints, and what to look for

The script runs eight checks — row count, missing fields, unmapped categories, theme totals, link count, rows carrying figures, orphaned metrics, keyword count — and prints each with the expected number beside it.

**If any check fails, it stops and leaves the existing data file untouched.** That's deliberate: a data file that's quietly missing forty rows looks completely normal on screen, and you would have no way to spot it. A conversion that refuses to finish is a problem you can see; one that silently drops rows is a problem a client finds.

The same applies to anonymisation — if the leak scan finds something, nothing is written.

### If a new export adds a category

The 28 categories in the spreadsheet (things like "Board of Directors" or "BRSR Section C: Principle 4") map to 6 broader themes inside the script. If a future export introduces a category name the script doesn't recognise, it **stops with an error** rather than guessing, so rows can never silently vanish from the page. The fix is one line added to `THEME_MAP` near the top of `tools/convert.py`.

## Field reference

`data/disclosures.js` is **generated, never edited by hand** — anything you change there is overwritten next time the converter runs. If something in it looks wrong, fix `tools/convert.py` and re-run.

| Field | What it is |
|---|---|
| `theme` | One of the six broad groupings in the Theme dropdown |
| `category` | The original, more specific grouping from the source file — shown as the table's section headings |
| `subfactor` | The short name of the individual disclosure |
| `keywords` | Tags shown as pill labels, and the source of the Keyword dropdown |
| `documents` | Links in the Documents column. `url` is blank in the anonymised build |
| `metrics` | Value and label pairs shown as blocks above the narrative, on the 96 rows that have them |
| `highlights` | The full narrative text |

## What each file is

| File | What it is |
|---|---|
| `index.html`, `styles.css`, `app.js` | The page itself. No libraries, nothing to install. |
| `data/disclosures.js` | **Generated.** Never edit by hand — fix the converter and re-run. |
| `tools/convert.py` | Turns `ESGReport.xls` into the data file. Runs on your machine only. |
| `tools/brsr_indicators.py` | The BRSR, GRI and IFC mapping tables, each with its source named. |
| `tools/test.js` | The 107 checks. |
| `ESGReport.xls` | The source export. Deliberately **not** in version control — it carries the real company name, CIN, contact details and director biographies. |
| `product-spec.md` | What was built and why, with every decision recorded. |
| `push-to-github.command` | Double-click to commit and push. |

## What this build deliberately does not do

A Tier 1 demo of the viewing experience only. No report upload, no automatic extraction, no multiple companies, no accounts, no saved state. No `.xlsx` or Word export and no PDF library — the Print / PDF button uses your browser's own print dialogue, and the charts are drawn by hand rather than by a charting library.

One thing discussed but not built, waiting on a decision rather than on effort:

- **An Environmental / Social / Governance filter.** The source file has no E/S/G column, so each disclosure has to be classified. Rule-based classification covers about 84% of rows; 105 are genuinely none of the three. That mapping is a professional judgment you need to sign off, not something to guess at.

## Notes on this build

- **Accent colour:** `#0f4c5c`, defined once as `--accent` at the top of `styles.css`. Change that one line to swap it for a brand colour.
- **Performance:** every row is built once when the page loads, then shown or hidden as you filter — the table is never rebuilt on a keystroke. Search is delayed by 120 milliseconds so fast typing doesn't stutter.
- **Number formatting:** thousands separators are added for display only. The stored values keep their exact source precision, including decimals — nothing is rounded or converted.
- **The "Updated" date** (`17 Jul 2026`) comes from the reference page, since the spreadsheet has no date field. Change `UPDATED` in `tools/convert.py` if a better date becomes available.
- **Tested:** filter counts, search behaviour and the CSV export are verified against the real 663 rows. The visual rendering has not been checked in a browser — see the note in the conversation history.
