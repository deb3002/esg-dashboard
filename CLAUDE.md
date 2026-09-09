# CLAUDE.md — ESG Dashboard

## Who you're working with

Debraj, a **sustainability consultant**. Not a developer — he does not read or write code.

This has real consequences for how you work:

- **He cannot review your code for correctness.** He can only judge what he sees on screen. The burden of verification is entirely on you: run the tests, check your own output, and don't hand back something you haven't confirmed works.
- **Never answer a question with code.** If he asks "why is the table empty?", the answer is "the factor values in your data file are spelled 'Environment' but the filter looks for 'Environmental'" — not a diff.
- **Explain in plain language, always.** If you must name a technical thing, define it in the same sentence. "A CORS restriction — browsers block pages opened directly from your hard drive from loading local data files."
- **Don't assume tooling knowledge.** He may not have used a terminal or git before. If a step needs one, spell it out.

## Who the work is for

His **clients** — companies that need their sustainability disclosures (BRSR, GRI-style reports) presented as something more usable than a 200-page PDF.

Anything he shows a client must look finished. Placeholder text, broken links and console errors are not acceptable. If something is unfinished, say so explicitly rather than letting him discover it live.

## How to work

**Explain before changing things.** One or two plain sentences on what you're about to do and why. For a multi-step change, outline the steps and get a nod first.

**Ask before adding dependencies.** No library, framework, CDN link or npm package without asking. The shipped page has **zero** dependencies and that is not negotiable. `tools/` is the one exception — see below.

**Keep commits small,** one logical change each, with a message a non-developer can read.

---

## Run this before you say you're done

```bash
node tools/test.js          # 107 checks against the real data — must all pass
python3 tools/convert.py    # regenerates the data file; prints its own checks
```

`tools/test.js` builds a fake DOM and runs the **real** `app.js` against the **real** data file, so it tests shipped code rather than a copy. It has caught genuine bugs: framework tags leaking onto non-BRSR rows, the CSV export silently losing the "GRI" prefix, indicator codes lost to non-breaking spaces.

**A green run does not mean the page looks right.** Nothing visual is covered — layout, spacing, overflow and colour all need a browser and a human. Say so rather than implying you've checked.

---

## The project

A single-page ESG disclosure profile viewer. Full requirements in **`product-spec.md`** — read it first, and work from the revision note at the top, not from memory.

```
index.html  styles.css  app.js      the shipped page — zero dependencies
data/disclosures.js                 GENERATED. Never hand-edit.
tools/convert.py                    ESGReport.xls -> data/disclosures.js
tools/brsr_indicators.py            BRSR/GRI/IFC mapping tables + their sources
tools/test.js                       the 107 checks
ESGReport.xls                       source export (gitignored — see Ground rules)

app-src/brsr-app.template.html      Phase 3 app — THE SOURCE. Edit this one.
brsr-app.html                       GENERATED from it. Never hand-edit.
tools/build_app.py                  template -> brsr-app.html
tools/test-extract.js               extraction rules, in Node. No browser, no PDF.
tools/test_app.js                   drives the app in a browser against a fixture
brsrapp-fix-spec.md                 four specified changes — all four are done
```

**`brsrapp.html`, `brsrapp2.html` and `brsrapp3.html`, if you have them
locally, are copies of the built app at three points in time — not sources.**
They are not in the repository. `brsrapp3.html` is the newest and matches
`brsr-app.html` exactly; the other two are older and lack the four changes
from `brsrapp-fix-spec.md`. Anything edited in any of them is discarded the
next time `build_app.py` runs.

**Read `CHANGELOG.md` before changing anything.** It records why decisions were made, including several that look odd until you know what went wrong with the obvious approach.

- **Stack:** plain HTML, CSS, vanilla JavaScript. No framework, no build step.
- **`tools/` is a developer-only exception.** It runs on Debraj's machine, never in the browser. Whatever it needs must never reach the shipped page.
- **It must open by double-clicking.** He demos live to clients. If a change would require running a local server, flag it first. This is why the page loads data from a script file rather than fetching it.
- **`product-spec.md` has a "Left Out of This Build" section.** That is a boundary, not a wishlist. If you think something on it is needed, raise it as a question.

## Where things stand (7 Sep 2026)

Phase 1 is **built and running**: converter, page, theme/keyword/framework filters, search, metrics, trend charts, CSV export, print stylesheet. Data is the real 663-row export, anonymised. The page has been opened in a browser and looks right.

**One thing is deliberately unbuilt: the E/S/G filter.** Debraj must sign off the classification mapping first, because a client may ask him to defend any row's classification. Rule-based classification reaches about 84%; 105 rows are genuinely none of the three. Details in `product-spec.md`.

## `brsr-app.html` — the Phase 3 app

A single self-contained file that reads a report PDF and generates a profile. **It is not part of the Tier 1 build** — do not wire it into `index.html`, and do not let its dependencies near the shipped page. PDF.js is embedded in it as base64 precisely so it stays self-contained.

Three properties that must survive any change to it:

- **The review gate.** Generate stays disabled until every indicator is approved or excluded. Never publish unreviewed output.
- **No rounding of figures.** `Math.round` appears only in layout geometry. Keep it that way.
- **No network, no AI model, no credentials.** Extraction is regex and geometry. That is what makes it free to run and safe to hand to a client.

**Work on `app-src/brsr-app.template.html`, then run `python3 tools/build_app.py`.** `brsr-app.html` is the 2 MB file that comes out — it is what gets double-clicked and what gets sent to Debraj, but editing it directly loses the work at the next build. The build is reproducible: rebuilding without changing the template leaves the file byte-identical.

**A correction, 9 Sep 2026.** This file previously recorded a verified defect: a *"Principle 9 of the NGRBCs"* line on page 17 of the bundled BRSR anchoring P9 to Section B, so that two of nine principles produced wrong output. **That does not reproduce.** The bundled PDF contains exactly nine lines that can anchor a principle, on pages 20, 23, 25, 30, 31, 34, 38, 39 and 41 — the correct ones — and both the current app and the older copy already produced those ranges. Nothing on page 17, or anywhere before Section C, matches. If you are told this defect exists, check it before acting on it.

The **weakness behind it was real**, and is now fixed. `locate()` did ignore the Section C page it had found, and took the first "Principle *n*" line anywhere. On the 513-page annual report the GRI index carries lines like *"Principle 6 – 3"* on page 499, and "Section C" is named on seven separate pages; the right ones won only because they happened to come first. The principle search is now fenced to Section C, choosing the last page where a Principle 1 heading and an "Essential Indicators" heading follow within a few pages, and falling back to the first Principle 1 heading — saying so in the log — when there is no Section C at all.

All four changes in `brsrapp-fix-spec.md` are done: the fence above, a bulk-approve button that can only take indicators whose every figure was read with high confidence (25 of 108 on the annual report — the rest have no figures and must each be decided), review state saved under a fingerprint of the PDF so a closed tab no longer costs an hour, and a downloadable audit trail of every figure with its page, confidence and status.

Remaining gap: review still runs in document order rather than confidence order.

**Its accuracy has still never been measured** — no report with known-correct answers has been scored against it. That is `phase3-spike-brief.md`, and nothing now blocks it: the earlier instruction to hold off until the locator was fixed rested on the defect above, which was not real.

## Three things that must not be undone

These each exist because the obvious approach produced something wrong. Reverting any of them is a regression, not a simplification.

**1. The trend-chart discontinuity guard.** Any series jumping 3× or more year on year is flagged, drawn with hollow pre-break bars and a visible caption. Without it the GHG series shows a false twelvefold rise — 2024 excludes Scope 3, 2025 and 2026 include it. Charts always use a zero baseline and always print exact values. If a change makes flagged series look tidier, that is the bug.

**2. Framework tags must stay sourced.** Indicator codes come from SEBI's BRSR format (Annexure I, circular 2021/562); GRI from the GRI–SEBI BRSR linkage document (GRI with BSE, 2022). Both transcriptions are in `tools/brsr_indicators.py` with their sources named, and tests assert them. An earlier revision tagged 445 rows by keyword guessing and had to be thrown away — **do not reintroduce keyword-guessed tags**, and do not extend GRI to non-BRSR rows.

**3. IFC is narrow on purpose — 49 rows, not 149.** It is *derived by alignment*, chained BRSR → GRI → IFC, which no published document asserts. It must stay `verified: false` with "by GRI alignment" visible on the tag. Three exclusions, each added after seeing real output: GRI 200-series, GRI 2 and 3, and principle-level GRI answers. Including them filed the company's e-mail under "Assessment and Management of E&S Risks" and CIN under "Labour and Working Conditions". Widening it back is a regression.

Also: indicator lookup is scoped to BRSR categories, because subfactor titles are **not** unique across the file — "Energy Consumption" exists under both Environment and Principle 6.

## The data

`data/disclosures.js` is **generated, not written**. Never hand-edit it. If something in it is wrong, fix the converter and re-run.

The source is `ESGReport.xls` — 663 real disclosure rows from the Churchgate Partners ESG portal. The converter runs nine checks (row count, theme totals, hyperlink count, metric rows, keyword count, and that no figure is lost between series and standalone). **Run them and show Debraj the numbers.** He cannot read the data file to spot 40 missing rows; a conversion that silently drops data will reach a client before anyone notices. The converter refuses to write when a check fails — keep that behaviour.

## Ground rules

- **Never put an API key, token or password in any file here.** Not in HTML, not in JavaScript, not in a comment.
- **The data is real, which cuts both ways.** These are genuine published figures. Never invent a figure, never fill a gap with a plausible number, never round or unit-convert on the way in. A missing value renders empty.
- **The demo is anonymised, but de-branded is not anonymous.** The figures are real and published, so they can be matched back. Director biographies are withheld entirely because they identified the company through the individuals. Don't weaken this without Debraj deciding.
- **`ESGReport.xls` is gitignored** — it carries the real company name, CIN, contact details and biographies. Don't commit it without asking.
- **Tell him when you're unsure.** A flagged uncertainty is cheap; a confident wrong answer he repeats to a client is not.
- **If something breaks, say so plainly.** Don't quietly work around it.

## Open decisions — don't guess these

Listed in full in `product-spec.md`. The live ones:

1. **E/S/G classification mapping** — needs sign-off before the filter is built.
2. **Four flagged trend series** — business travel, hazardous waste, e-waste, harassment complaints — carry a generic caption. Causes unknown; a falling harassment count is probably genuine good news rather than an artefact.
3. **GRI licensing** for commercial use in software is unresolved.
4. **The IFC handbook's Tables C.3, D.2 and E.2** could not be retrieved (only pages 1–52 of ~80 were readable). If obtained, they may replace the derived IFC mapping with a real one.
5. **Residual proper nouns** in the anonymised build — the converter prints a review list each run.
