# Spec — four changes to `brsrapp2.html`

**For Claude Code.** Read `CLAUDE.md` and `CHANGELOG.md` first. This spec covers one file: `brsrapp2.html`, the BRSR extraction prototype. It does not touch the Tier 1 viewer (`index.html`, `app.js`, `styles.css`, `tools/`).

**Two files exist:** `brsrapp.html` (older) and `brsrapp2.html` (current — has `brsrEnd`, `stripRunningHeads`, y-aware principle ranges). **Work on `brsrapp2.html`.** Once these changes land and are verified, Debraj should delete the older file; ask him rather than doing it.

## Constraints that override everything

Break any of these and the change is wrong regardless of what it fixes:

- **No external dependencies.** No CDN, no npm, no `<script src>`. PDF.js is embedded as base64 on purpose.
- **No network calls.** No `fetch`, no `XMLHttpRequest`. The app must work with the machine offline.
- **No AI model, no API keys.** Extraction is regex and geometry. This is what makes it free to run.
- **Never round or alter a figure.** `Math.round` is permitted only for layout geometry and progress display. Published precision is preserved exactly.
- **Nothing publishes unreviewed.** See change 2 — this is currently weaker than it looks.

---

## Change 1 — Fence the principle search to Section C

### The problem, with evidence

`locate()` records the page where `SECTION C` first appears, then never uses it. It finds each principle by taking the **first** line anywhere in the document matching `/^\s*PRINCIPLE\s*[-–]?\s*(\d)\b/i`.

In `BusinessResponsibilityandSustainabilityReport.pdf` (in this folder), **page 17 sits in Section B** and contains a line beginning *"Principle 9 of the NGRBCs"*. Section C begins on page 20. The result:

| Principle | Range assigned now | What is actually there | Correct start |
|---|---|---|---|
| P9 | pages 17–20 | Section B policy narrative | page 41 |
| P8 | pages 39–43 | absorbs P9's real content | page 39 |
| P1–P7 | correct | | |

**Two of nine principles produce wrong content.** P9 reports someone else's text under P9 codes; P8 over-claims three pages that belong to P9.

This also blocks annual-report support: in a 300-page integrated report, "Section C" and "Principle *n*" will appear in contents pages, governance narrative and financial notes long before the BRSR annexure.

### What to do

Ignore principle headings that appear **before** the Section C page.

Two details that matter:

1. **Prefer the last plausible `SECTION C`, not the first.** An annual report may mention it in a contents list before the real annexure. A reasonable rule: choose the occurrence that is followed by at least one `PRINCIPLE 1` heading and by an `Essential Indicators` heading within the next few pages. If several qualify, take the last.
2. **Fall back safely.** If no `SECTION C` is found at all — some standalone filings omit it — fall back to the first page carrying a `PRINCIPLE 1` heading, and record that this happened so it appears in the log the user sees.

Do not delete the existing `brsrEnd` logic; it handles the *end* of the BRSR and is separate from this.

### Acceptance criteria

- On the bundled BRSR PDF: all nine principles anchor to pages 20, 23, 25, 30, 31, 34, 38, 39, 41 respectively.
- P8's range ends at page 40 or earlier; P9's range begins at page 41.
- The existing behaviour for two principles sharing a page (the y-coordinate handling) still works.
- When the fallback fires, the user-visible log says so in plain language.

---

## Change 2 — "Approve all" must not be able to approve everything

### The problem

There is an `approve-all` button. The review gate — generation blocked until every indicator is approved or excluded — is the property that makes this product defensible. A single button that satisfies the gate for ~140 indicators makes it ceremonial. A rushed user ships unreviewed figures under a client's name, and the software has recorded an approval.

### What to do

Restrict it to indicators where **every** figure has confidence ≥ 0.8, and which have at least one figure. Anything with a low-confidence figure, or with no figures at all, stays pending and must be handled individually.

Relabel it accordingly — for example *"Approve the N high-confidence indicators"* — with N computed live, and disable it when N is zero.

### Acceptance criteria

- Pressing it never moves an indicator containing a sub-0.8 figure to approved.
- Pressing it never moves a zero-figure indicator to approved.
- After pressing it, the Generate button is still disabled if anything remains pending.
- The label states how many indicators it will act on.

---

## Change 3 — Do not lose the reviewer's work

### The problem

There is no storage of any kind and no warning before leaving. Reviewing ~140 indicators takes roughly an hour. A reload, a crash, or a closed tab loses all of it, and the user must re-upload and re-extract from nothing.

Note: the Tier 1 viewer deliberately avoids browser storage so filter state resets on reload. **That reasoning does not transfer** — this is a long human task, not a transient view.

### What to do

Two parts, in this order:

1. **Warn before leaving.** A `beforeunload` handler, active only once extraction has produced indicators and while anything is still pending. Five minutes of work, removes the worst outcome.
2. **Save and restore review state** in `localStorage`, keyed by a hash or fingerprint of the source PDF so two different reports do not overwrite each other. Save the review state — statuses, edited values, dropped figures — not the whole extraction. On load, if saved state matches the PDF just opened, offer to resume; make resuming a choice, not automatic.

Storage can be unavailable or full — private browsing, quota limits. Wrap reads and writes in `try/catch` and degrade to the warning-only behaviour rather than breaking.

### Acceptance criteria

- Closing or reloading with pending indicators prompts a confirmation.
- Reopening the same PDF offers to restore prior review state; declining starts clean.
- Opening a *different* PDF never restores the previous report's state.
- With storage disabled, the app still works end to end.

---

## Change 4 — Export the audit trail

### Why this one is worth doing

For an investor relations team, the record of *where each number came from and who approved it* is worth more than the profile page. It converts "our mappings are traceable" from a claim into a file that can be handed to a client or an auditor. The data already exists in the app; it simply never leaves.

### What to do

A third download button beside the existing two, producing a CSV with one row per extracted figure:

| Column | Content |
|---|---|
| `indicator` | e.g. `P6-E3` |
| `question` | the indicator's question text |
| `measure`, `value`, `unit`, `year` | as approved |
| `page` | source page in the PDF |
| `read_from` | `table` or `text` |
| `confidence` | as extracted |
| `original_value` | what the extractor produced, if a human changed it — otherwise blank |
| `status` | `approved`, `excluded`, or `dropped` |
| `source_file` | the PDF's filename |
| `generated_at` | ISO timestamp |

Follow the CSV rules already proven in the Tier 1 viewer: every field quoted, internal quotes doubled, CRLF line endings, and a UTF-8 byte-order mark so Excel does not mangle characters. Excluded and dropped rows are **included**, with their status — a reviewer's decision to reject a figure is part of the record.

### Acceptance criteria

- Opens in Excel with no mangled characters and no rows split across lines.
- Every figure the reviewer saw appears exactly once, whatever its status.
- A corrected figure shows both the original and the corrected value.

---

## How to verify

**There is currently no test harness for this app.** `tools/test.js` covers the Tier 1 viewer only.

Add `tools/test-extract.js`, following the pattern of `tools/test.js`: load `brsrapp2.html`, pull out the pure functions (`locate`, `brsrEnd`, `questionOn` and the CSV builder), and run them against synthetic page/line data in Node. No browser needed for those; they are ordinary JavaScript over arrays of `{text, y}` lines.

At minimum it should assert:

- The scenario from change 1: a "Principle 9 of the" line on a page before Section C does not anchor P9 there.
- Principles sharing a page still split correctly.
- `approve-all` selects only high-confidence indicators.
- The audit CSV round-trips: parse it back and confirm the row count and column count.

Then run the app by hand on the bundled PDF and confirm the nine principle ranges. **Say plainly which parts you verified automatically and which by eye** — nothing here checks appearance.

## What success looks like

After these four changes: the locator is correct on the one document we can check, the review gate means what it says, an hour of review survives a reload, and every figure can be traced to a page and a person.

**None of this measures accuracy.** That is `phase3-spike-brief.md`, and it should be run *after* change 1 — measuring against a broken locator would produce a number that is wrong in a way nobody would notice.
