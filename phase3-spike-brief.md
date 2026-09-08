# Phase 3 Feasibility Spike — Can we extract a BRSR accurately enough?

**Revision 2 — 8 Sep 2026.** The answer key is corrected. Revision 1 specified it as the metric values on the 21 Principle 6 rows; **those rows carry no metric values at all** — every structured figure in the export sits under other categories. The figures are present, but as prose inside the narrative text, so building the answer key is now an explicit first step with its own budget. Also added: the scoring note for `P6-L1`, which the portal profile omits; the caveat that the indicator schema is keyed on the portal's row titles rather than SEBI's question wording; and a worked example of a key that is itself wrong.

**Timebox: two weeks. No server, no interface, no accounts.**
The only output is a number and a failure log.

---

## The question this answers

Phase 3 is "a company uploads its report and the profile is generated". Everything about that idea rests on one unknown: **can figures be pulled out of a filed report accurately enough to put a client's name on them?**

Nothing else — not the upload flow, not the review screen, not hosting — is worth designing until that number exists. Build the answer, not the product.

## Why this is more tractable than it looks

**A BRSR is a form, not an essay.** SEBI's Annexure I (circular 2021/562) fixes a set of numbered indicators in a fixed order — 146 distinct codes are transcribed in this project — and every filing answers the same questions in the same sequence. Extraction is therefore *filling a known schema*, not open-ended document understanding.

That schema already exists in this project: `tools/brsr_indicators.py`.

**One caveat on reusing it.** `INDICATOR_CODES` maps *the portal's row titles* to SEBI codes — `"Energy Consumption" → P6-E1`. A filed report contains SEBI's actual question wording ("Details of total energy consumption (in Joules or multiples) and energy intensity"), not the portal's shorthand. The code list and its ordering are directly reusable; the lookup keys are not, and matching against the PDF needs SEBI's question text instead.

**And we already have an answer key.** `ESGReport.xls` is Churchgate's manually-curated profile for Escorts Kubota, built by an analyst from the same annual report that is public. That gives 663 known-correct rows across the whole profile. Extraction accuracy can be *measured*, not estimated.

That is an unusual position to start from. Use it.

---

## Scope: Principle 6 only

**21 indicators.** Energy, water, air emissions, GHG Scope 1 and 2, waste, ecologically sensitive areas, environmental compliance, plus the Leadership indicators covering Scope 3, water discharge and biodiversity.

Why this section and not a broader sample:

- It is the **most table-heavy** part of the report. Energy, water and waste figures sit in multi-column tables with merged cells, footnotes and two years side by side. This is where extraction projects fail.
- It carries **most of the numeric content**, so figure accuracy is measurable rather than anecdotal.
- If Principle 6 works, the narrative-heavy principles are easier. If it fails, nothing else matters.

Do not broaden the scope to make the result look better.

**One gap to score correctly.** The portal's 21 rows run `P6-E1`–`P6-E12`, then `P6-L2`–`P6-L9`, plus `P6-Core`. **`P6-L1` is absent from the profile.** Extracting the full Principle 6 from SEBI's format will therefore produce at least one indicator with no counterpart in the key. Score that as *not in key*, not as a miss — otherwise accuracy is understated by construction.

## Inputs

| | |
|---|---|
| Source report | Escorts Kubota Integrated Annual Report FY 2025-26 (public PDF, ~300 pages; the URL is in the source export's link column) |
| Answer key | The figures reported in the **narrative text** of the 21 rows under `BRSR Section C: Principle 6` in `ESGReport.xls`, transcribed by hand into a scoreable list before extraction begins — see below |
| Schema | `INDICATOR_CODES` in `tools/brsr_indicators.py`, re-keyed to SEBI's question wording |

**Two practical notes.** `ESGReport.xls` is deliberately kept out of version control, so it must be supplied from the owner's machine. And the anonymised build in `data/disclosures.js` has every document URL stripped — the annual report link is in the *real* export only.

### The answer key has to be built first

**The 21 Principle 6 rows carry no structured metric values.** Every one of the 265 structured figures in the export sits under a different category — Social 91, Governance 74, Environment 72, the rest scattered. Principle 6 has none. The GHG and water figures one would expect there are filed under **Environment**.

The figures are still present, as prose inside the narrative. There are **277 numeric tokens across the 21 narratives** — energy split by renewable and non-renewable source, water withdrawal broken out five ways, Scope 1 and Scope 2 with intensity ratios, each with two financial years. That is a richer sample than the structured metrics would have given.

So: **transcribe those figures by hand into a scoreable list, and do it before the extractor runs.** Budget half a day to a day. Doing it afterwards invites the key and the output to converge.

**The extractor must not see the answer key.** Score afterwards, separately. This is easy to violate accidentally when iterating.

---

## Method

0. **Build the answer key** by hand from the Principle 6 narratives, as above. Finish this before step 1.
1. **Locate** the BRSR section within the annual report. It has standard headings ("Section C: Principle Wise Performance Disclosure", "PRINCIPLE 6"). Record whether this was reliable.
2. **Split** into the 21 numbered indicators using the SEBI format as the map.
3. **Extract** for each indicator: the narrative answer, and every figure with its unit and financial year.
4. **Score** against the answer key.
5. **Log every failure with its cause.** The failure log is more valuable than the score.

## What to measure

**Figure accuracy — the headline number.**
For every figure in the answer key for these indicators: exact match / wrong value / correct value but wrong unit or year / missed entirely.

Exact means exact. `340602.16` and `340,602` are the same; `340602.16` and `340602` are not, because rounding a published figure is a line this product does not cross.

Note that the source narrative uses **Indian digit grouping** (`4,94,545.39`) while the structured metrics use international grouping. Normalise before comparing, or every figure will score as wrong.

**Indicator alignment.** Was content attributed to the right indicator number? Content landing under P6-E3 that belongs under P6-L2 is a different failure from getting a number wrong, and needs a different fix.

**Narrative usability.** Three-point human judgement per indicator: usable as-is / usable after editing / not usable.

**Cost and time per report.** Record it. At ₹25,000–30,000 per company per year, the unit economics need to be known before anything is promised.

**Disagreements are not automatically failures.** Where the extractor and the answer key differ, check the PDF. The key is one analyst's reading and can itself be wrong. A disagreement resolved in the extractor's favour is a finding worth recording.

> **A worked example, already in the data.** The Principle 6 energy row reads *"Total energy consumed from renewable source: FY2026: 9.47 Joules"*. Nobody's renewable consumption is nine joules. SEBI's form says "in Joules or multiples", and the multiple was dropped in transcription. An extractor reading the PDF correctly would *disagree with the key here and be right*. Expect several of these, and review disagreements by hand rather than trusting the score.

---

## What the result means

| Figure accuracy | Reading |
|---|---|
| **90%+ exact** | Strong. Client-side review becomes plausible, which is what makes the economics work. |
| **70–90%** | Workable, but every profile needs your review before a client sees it. Effort per company stays material — build the review interface before anything else. |
| **Below 70%** | The approach needs rethinking. Consider asking companies to submit the BRSR as structured data (many prepare it in a spreadsheet before it reaches the PDF), or narrow the product to the BRSR Core attributes only. |

Whatever the number, **it decides the review model**, which is currently an open question and should stay open until this runs.

Note that this measures something narrower and harder than the PRD's Phase 3 threshold of "70% of extracted rows requiring no human correction". This spike scores *individual figures* on the most table-heavy section. The two numbers are not interchangeable; report which one is being quoted.

## Kill criteria

Stop and report early if any of these become clear:

- The BRSR section cannot be reliably located across report layouts.
- Table figures come out unreliable and a week of work does not move it.
- Cost per report exceeds a few percent of the annual fee.

Stopping early with a clear reason is the second-best outcome. The worst is two months of building on an untested assumption.

---

## One scoping fact worth knowing now

The 663-row profile is **not** all BRSR. Only **149 rows** come from the BRSR section — 22% of the profile. The other 514 — board biographies, awards, ratings, memberships, policies, materiality, corporate information — are drawn from elsewhere in the annual report, the company website and third-party sources.

So even a perfect BRSR extractor generates roughly **a fifth of a full profile**. The rest needs other sources or manual entry.

That does not undermine the idea — the BRSR rows carry most of the quantitative content, and figures are the expensive part to key in by hand. But "upload your report and the profile appears" is not what Phase 3 delivers, and it should not be described that way to a client.

## Deliverable

One page:

- The four numbers above
- The failure log, with a cause against each failure
- A recommendation: proceed, proceed with a narrower scope, or stop

No prototype, no interface, no server. If the spike produces a demo, it has gone wrong.
