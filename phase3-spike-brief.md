# Phase 3 Feasibility Spike — Can we extract a BRSR accurately enough?

**Timebox: was two weeks. Now roughly a day.**
The only output is a number and a failure log.

> **BLOCKED — 9 Sep 2026. Do not run this yet.** The extractor mis-locates two of the nine principles on the very file this spike uses: a "Principle 9 of the" line on page 17 (Section B) anchors P9 there, which also lets P8 absorb P9's real content. Measuring now would produce a number that is wrong in a way nobody would notice. **Fix change 1 in `brsrapp-fix-spec.md` first, then run this.**
>
> **Updated 9 Sep 2026.** `brsr-app.html` now does the extracting. This brief was written when the extractor had to be built first; it does not. **The spike is now a measurement exercise, not a build.** Run the app on the report below, compare its output against the answer key, count. Everything else here still applies — especially what to measure and what the result means.
>
> **Nothing blocks this any more.** An earlier note held the measurement back until a locating defect was fixed. That defect did not reproduce — see `CHANGELOG.md` — and the weakness behind it has been fixed regardless.

---

## The question this answers

Phase 3 is "a company uploads its report and the profile is generated". Everything about that idea rests on one unknown: **can figures be pulled out of a filed report accurately enough to put a client's name on them?**

Nothing else — not the upload flow, not the review screen, not hosting — is worth designing until that number exists. Build the answer, not the product.

## Why this is more tractable than it looks

**A BRSR is a form, not an essay.** SEBI's Annexure I (circular 2021/562) fixes ~140 numbered indicators in a fixed order, and every filing answers the same questions in the same sequence. Extraction is therefore *filling a known schema*, not open-ended document understanding.

That schema already exists in this project: `tools/brsr_indicators.py`.

**And we already have an answer key.** `ESGReport.xls` is Churchgate's manually-curated profile for Escorts Kubota, built by an analyst from the same annual report that is public. That gives 663 known-correct rows, 96 of them carrying exact figures. Extraction accuracy can be *measured*, not estimated.

That is an unusual position to start from. Use it.

---

## Scope: Principle 6 only

**21 indicators.** Energy, water, air emissions, GHG Scope 1 and 2, waste, ecologically sensitive areas, environmental compliance, plus the Leadership indicators covering Scope 3, water discharge and biodiversity.

Why this section and not a broader sample:

- It is the **most table-heavy** part of the report. Energy, water and waste figures sit in multi-column tables with merged cells, footnotes and two years side by side. This is where extraction projects fail.
- It carries **most of the numeric content**, so figure accuracy is measurable rather than anecdotal.
- If Principle 6 works, the narrative-heavy principles are easier. If it fails, nothing else matters.

Do not broaden the scope to make the result look better.

## Inputs

| | |
|---|---|
| Source report | `BusinessResponsibilityandSustainabilityReport.pdf`, now in this folder |
| Answer key | The 21 rows under `BRSR Section C: Principle 6` in `ESGReport.xls`, plus their metric values |
| Schema | `INDICATOR_CODES` in `tools/brsr_indicators.py` |

**The extractor must not see the answer key.** Score afterwards, separately. This is easy to violate accidentally when iterating.

---

## Method

1. **Open `brsr-app.html`** and drop in the report PDF. Steps 1 to 3 below are what it already does — record whether each worked rather than building them.
2. Confirm it **located** the BRSR section and **split** it into the numbered indicators. Check the principle page ranges explicitly — they should be 20, 23, 25, 30, 31, 34, 38, 39, 41. If they are not, stop; the locator is still wrong and the score would be meaningless.
3. Read off what it **extracted** per indicator: narrative, figures, units, years, page numbers, confidence.
4. **Score** against the answer key. Do this outside the app, in a spreadsheet or a script.
5. **Log every failure with its cause.** The failure log is more valuable than the score.

Do not fix the extractor while measuring it. Get the baseline number first; a moving target cannot be scored.

## What to measure

**Figure accuracy — the headline number.**
For every figure in the answer key for these indicators: exact match / wrong value / correct value but wrong unit or year / missed entirely.

Exact means exact. `340602.16` and `340,602` are the same; `340602.16` and `340602` are not, because rounding a published figure is a line this product does not cross.

**Indicator alignment.** Was content attributed to the right indicator number? Content landing under P6-E3 that belongs under P6-L2 is a different failure from getting a number wrong, and needs a different fix.

**Narrative usability.** Three-point human judgement per indicator: usable as-is / usable after editing / not usable.

**Cost and time per report.** Record it. At ₹25,000–30,000 per company per year, the unit economics need to be known before anything is promised.

**Disagreements are not automatically failures.** Where the extractor and the answer key differ, check the PDF. The key is one analyst's reading and can itself be wrong. A disagreement resolved in the extractor's favour is a finding worth recording.

---

## What the result means

| Figure accuracy | Reading |
|---|---|
| **90%+ exact** | Strong. Client-side review becomes plausible, which is what makes the economics work. |
| **70–90%** | Workable, but every profile needs your review before a client sees it. Effort per company stays material — build the review interface before anything else. |
| **Below 70%** | The approach needs rethinking. Consider asking companies to submit the BRSR as structured data (many prepare it in a spreadsheet before it reaches the PDF), or narrow the product to the BRSR Core attributes only. |

Whatever the number, **it decides the review model**, which is currently an open question and should stay open until this runs.

## Kill criteria

Stop and report early if any of these become clear:

- The BRSR section cannot be reliably located across report layouts.
- Table figures come out unreliable and a week of work does not move it.
- Cost per report exceeds a few percent of the annual fee.

Stopping early with a clear reason is the second-best outcome. The worst is two months of building on an untested assumption.

---

## One scoping fact worth knowing now

The 663-row profile is **not** all BRSR. Only **149 rows** come from the BRSR section. The other 514 — board biographies, awards, ratings, memberships, policies, materiality, corporate information — are drawn from elsewhere in the annual report, the company website and third-party sources.

So even a perfect BRSR extractor generates roughly **a fifth of a full profile**. The rest needs other sources or manual entry.

That does not undermine the idea — the BRSR rows carry most of the quantitative content, and figures are the expensive part to key in by hand. But "upload your report and the profile appears" is not what Phase 3 delivers, and it should not be described that way to a client.

## Deliverable

One page:

- The four numbers above
- The failure log, with a cause against each failure
- A recommendation: proceed, proceed with a narrower scope, or stop

No new code. If the spike turns into a session of improving the extractor, it has gone wrong — fix things afterwards, against a baseline you can compare to.
