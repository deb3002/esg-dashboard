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

tools/extract_brsr.py               stale CLI extractor — see below
tools/make_test_brsr.py             builds the fixture PDF that CLI's test uses
tools/test_extract.py               that CLI's checks
```

**Read `CHANGELOG.md` before changing anything.** It records why decisions were made, including several that look odd until you know what went wrong with the obvious approach.

- **Stack:** plain HTML, CSS, vanilla JavaScript. No framework, no build step.
- **`tools/` is a developer-only exception.** It runs on Debraj's machine, never in the browser. Whatever it needs must never reach the shipped page.
- **It must open by double-clicking.** He demos live to clients. If a change would require running a local server, flag it first. This is why the page loads data from a script file rather than fetching it.
- **`product-spec.md` has a "Left Out of This Build" section.** That is a boundary, not a wishlist. If you think something on it is needed, raise it as a question.

## Where things stand (7 Sep 2026)

Phase 1 is **built and running**: converter, page, theme/keyword/framework filters, search, metrics, trend charts, CSV export, print stylesheet. Data is the real 663-row export, anonymised. The page has been opened in a browser and looks right.

**One thing is deliberately unbuilt: the E/S/G filter.** Debraj must sign off the classification mapping first, because a client may ask him to defend any row's classification. Rule-based classification reaches about 84%; 105 rows are genuinely none of the three. Details in `product-spec.md`.

## The extraction app now lives in its own repository

`brsrapp` — <https://github.com/deb3002/brsrapp>, private — is the app that
reads a company's report PDF and generates a profile from it. It was built
here and moved out on 10 Sep 2026. Everything about it, including why rotated
text is ignored and why an emissions intensity was once read as a negative
number, is in that repository's `CLAUDE.md` and `CHANGELOG.md`.

**Four files live in both repositories** and cannot be deduplicated across
them:

- `index.html`, `styles.css`, `app.js` — the profile that app generates *is*
  this viewer; its build inlines this page's code.
- `tools/brsr_indicators.py` — both projects tag disclosures from the same
  sourced mapping tables.

**If you change any of those four here, say plainly that `brsrapp` needs the
same change.** That repository has `tools/compare_with_dashboard.sh`, which
reports when they have drifted.

**`tools/extract_brsr.py` stayed here** because it imports `tools/convert.py`
and writes `data/disclosures.js`. It is stale — never updated when the table
reading was rewritten, it finds 6 figures where `brsrapp` finds 204 on the
same file. **Do not use it to judge what extraction can do**, and do not
treat its passing tests as evidence about the app. Whether to delete it is
Debraj's call; it has been raised and not yet decided.

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
