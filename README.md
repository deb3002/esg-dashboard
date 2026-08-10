# ESG Disclosure Profile Viewer

A single-page viewer for one company's ESG (Environmental, Social, Governance) disclosures, shown as a filterable, searchable table instead of a long PDF report.

## How to open it

Double-click **`index.html`**. It opens directly in your browser — no install, no server, no internet connection needed. Safe for a live demo: nothing on the page makes network calls or saves anything.

## What's on the page

- **Two dropdowns** — filter by Theme (six broad groupings) and by Keyword (recalculates its list and counts to match whichever theme is selected).
- **Search box** — filters as you type, across the disclosure name, category, keywords, metric labels, and the narrative text.
- All three combine together — a row shows only if it matches all of them.
- **Download CSV** — exports whatever rows are currently visible under your filters, as a spreadsheet file.
- **Print / PDF** — opens your browser's print dialog with a layout built for printing (unclamped text, repeating table header, one page-friendly summary line at the top showing which filters were active).

## The data: this is a real report, anonymized

The underlying content came from a real spreadsheet export (`ESGReport.xls`, 663 disclosure rows) from a real company's ESG portal. On 10 Aug 2026, the decision was made **not** to show the real company name in this demo. The conversion script (`tools/convert.py`) replaces:

- The company's name and its abbreviation, wherever they appear — including inside the narrative paragraphs, not just the header.
- All 16 real board members' names, replaced with their role instead (e.g. "an Independent Director") — since a name swap alone wouldn't anonymize a bio that also names the person's other companies, universities, or career history.
- Every document link's real URL, set to blank — so the Documents column shows plain labels instead of clickable links.

**What this does not do:** this is mechanical text substitution across free-form paragraphs, not a guarantee that every identifying detail is gone. Two things worth knowing before this goes in front of anyone outside your own team:

1. **The financial and environmental figures themselves are untouched and real** — e.g. the exact GHG emissions numbers. That's intentional (never invent or alter a real number — see the ground rules in `CLAUDE.md`), but it means someone who already knows the real company's published figures could still match this demo back to them by the numbers alone.
2. **The 16 board-member biography rows are the richest in personal detail** — they mention specific universities, other companies led or founded, and career histories that go beyond just the person's name. The script strips the names and the most obvious identifying phrases it was told about, but a thorough scrub of every biographical detail in free text isn't something that can be fully guaranteed by search-and-replace. If you plan to show the **Board of Directors** category specifically to someone outside your team, it's worth a quick read-through of those 16 rows first.

If the decision changes later and the real company name should be restored, that's a one-line flag in `tools/convert.py` (`ANONYMIZE = False`) — re-confirm the decision before flipping it, since it's a reputational call, not a technical one.

## How to re-run the conversion when a new export arrives

If you get a new `ESGReport.xls`, replace the file in this folder and run:

```bash
python3 tools/convert.py
```

This requires a small one-time tool called `xlrd` (a free Python library that reads the older Excel file format) to already be installed. If it's not, install it once with:

```bash
python3 -m pip install --user xlrd
```

This only runs on your computer to regenerate the data file — it never ships with the actual page, and the page itself still has zero installed dependencies.

The script prints a checklist as it runs — row counts, category totals, link counts, keyword counts — so you can see at a glance whether the new export converted cleanly. **If any check fails, it stops and does not overwrite the data file**, rather than silently shipping something wrong.

**Important:** the 28 real-world categories in the spreadsheet (things like "Board of Directors" or "BRSR Section C: Principle 4") are mapped to 6 broader themes inside the script. If a future export introduces a brand-new category name that isn't in that mapping, the script will **stop with an error** rather than guess — so you'll never end up with rows silently missing from the page. If that happens, the fix is adding one line to the `CATEGORY_TO_THEME` mapping near the top of `tools/convert.py`.

## Field reference (for anyone editing the converter's mapping)

`data/disclosures.js` is **generated, not written by hand** — never edit it directly, since your changes would be overwritten the next time the converter runs. If something in it looks wrong, the fix belongs in `tools/convert.py`.

| Field | What it is |
|---|---|
| `theme` | One of the six broad groupings shown in the Theme dropdown |
| `category` | The original, more specific grouping from the source file (shown as the table's section headings) |
| `subfactor` | The short name of the individual disclosure |
| `keywords` | Tags shown as pill labels and used to build the Keyword dropdown |
| `documents` | Links shown in the Documents column — `url` is blank in this anonymized build |
| `metrics` | Value + label pairs shown as stat blocks above the narrative (only on rows that have them) |
| `highlights` | The full narrative text for that disclosure |

## What this build deliberately does not do

This is a Tier 1 demo of the viewing experience only. It does not include report upload, automatic data extraction, charts, multiple companies, accounts, or any saved state — those stay out of scope by design, along with `.xlsx`/Word export and any PDF-generation library (the Print/PDF button uses the browser's own print dialog instead).

## Notes on this build

- **Accent colour:** a muted slate blue (`#2f5061`), defined once as `--accent` near the top of `styles.css` so it can be swapped for a brand colour later by changing that one line.
- **Performance:** with 663 rows, the page builds every row once when it loads and only shows/hides rows when you filter — it doesn't rebuild the table on every keystroke. Search is debounced by ~120 milliseconds so fast typing doesn't feel laggy.
- **The "Updated" date** (`17 Jul 2026`) is carried over from the reference page, since the source spreadsheet itself has no date field. Update it in `tools/convert.py` (`UPDATED_DATE`) if a more accurate date becomes available.
