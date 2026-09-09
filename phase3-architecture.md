# Phase 3 Architecture — Upload a report, get a profile

**Status: partly answered.** Written before the extraction app existed. Three of its open questions now have answers, marked below. Accuracy remains unmeasured, so everything downstream of it is still contingent.

> **Updated 9 Sep 2026 — what the prototype settled:**
> - **Cost per report: zero.** Extraction is pattern and layout analysis, not an AI model. Section 7's cost question is closed.
> - **The review gate is enforced in code, and now means something.** Generation is blocked until nothing is pending. An "Approve all" button used to satisfy that gate for every indicator in one click, which made it ceremonial; it now takes only indicators that produced figures and whose every figure was read with high confidence — 25 of 108 on the annual report tested, with the rest decided one at a time.
> - **Provenance survives extraction** — page number, table-or-narrative source, and a confidence score per figure.
>
> Still open: accuracy, layout variance across companies, and everything in section 9.

---

## 1. The honest starting point

**The viewer survives. Almost nothing else does.**

Today's build is deliberately serverless, accountless and zero-dependency, and opens by double-clicking. Upload requires a server, file storage, background processing, an account per company and a review interface. That is not an extension of Phase 1 — it is a different application that reuses the front end.

Say that plainly to anyone who assumes Phase 3 is "adding an upload button".

What genuinely carries over:

| Already built | Where |
|---|---|
| The profile viewer — filters, charts, export, print | `index.html`, `app.js`, `styles.css` |
| Figure normalisation to value + unit + year | `tools/convert.py` |
| Trend series and the discontinuity guard | `tools/convert.py` |
| BRSR indicator schema, GRI and IFC mappings | `tools/brsr_indicators.py` |
| Anonymisation | `tools/convert.py` |
| 107 automated checks | `tools/test.js` |

Roughly a third of the pipeline exists, and it is the fiddly, already-debugged third.

---

## 2. Pipeline

```
  upload ──▶ locate ──▶ split ──▶ extract ──▶ derive ──▶ REVIEW ──▶ publish
```

| Stage | What it does | State |
|---|---|---|
| **Upload** | Accept a PDF, or a URL to one. Record its hash so the same report is never processed twice. | build |
| **Locate** | Find the BRSR section inside a 300-page annual report. Standard headings make this tractable. | build |
| **Split** | Cut into the ~140 numbered indicators using SEBI's format as the map. | schema exists |
| **Extract** | Per indicator: narrative, tables, figures with unit and year, and the page each came from. | **prototype built — accuracy unmeasured** |
| **Derive** | Keywords, framework tags, trend series, discontinuity flags. | **built** |
| **Review** | A human confirms every figure against the source page before anything publishes. | **prototype built — see gaps below** |
| **Publish** | Generate the profile and host it. | build |

## 3. The review interface is the product

This is the part most likely to be underestimated.

**If review is fast, mediocre extraction is fine. If review is painful, excellent extraction does not save you.** A reviewer facing 663 undifferentiated rows will abandon it. A reviewer working through ~140 numbered indicators, each shown beside the page it came from, with figures pre-filled and highlighted, can finish a report in an afternoon.

Design requirements, in priority order:

1. **Source page beside every extracted answer.** Not a page number — the actual page image, with the extracted figure highlighted on it. Verification must be visual and immediate.
2. **Confidence-ordered queue.** Low-confidence extractions first. A reviewer who runs out of time should have spent it on the doubtful rows.
3. **Three actions only:** approve, correct, mark not-disclosed. Anything more elaborate slows it down.
4. **Nothing publishes unreviewed.** Not "flagged as unreviewed" — not published.
5. **Every keystroke recorded.** Who approved which figure, when, against which page. This is the audit trail that makes the output defensible, and it is also the training data for improving extraction.

**Against the prototype, three of these five are met.** It has editable values, page numbers, table-or-text provenance, low-confidence highlighting, per-figure drop and per-indicator approve or exclude, with generation blocked until nothing is pending. What it lacks:

- **Requirement 1 — the source page image.** It shows the page number and the text it read, not the rendered page. Cheaper than specified and probably sufficient for narrative; weaker for a figure buried in a merged-cell table.
- **Requirement 2 — the confidence-ordered queue.** Review runs in document order. A low-confidence count is already displayed, so filtering to it is a small change.
- **Nothing is saved.** Not in the original five, and it should have been. No storage of any kind and no warning before closing. An hour of review is lost to a reload.
- **Requirement 4 is undermined by "Approve all"** — the gate exists but can be satisfied without reading anything.

All three are specified in `brsrapp-fix-spec.md`.

## 4. Data model

Each extracted row carries its provenance:

```
indicator      P6-E3
value          340602.16
unit           KL
year           2026
source_page    281
confidence     0.94
status         extracted | corrected | approved | not_disclosed
approved_by    user id
approved_at    timestamp
original       what the extractor produced, if a human changed it
```

Keeping `original` alongside the correction is what lets you measure whether extraction is improving, and lets you show a client exactly what was changed and by whom.

## 5. What must not change

These carry forward from Phase 1 unchanged, and are not negotiable.

- **Extract → review → publish. Never extract → publish.** A missing row is recoverable. A wrong emissions figure under a client's name, beside a link to their audited annual report, is not.
- **Never invent a figure.** No estimation, no interpolation, no "plausible" values. A figure that could not be found is marked not-disclosed and renders empty.
- **Never round or unit-convert on the way in.** Store the published precision exactly.
- **Provenance stays visible.** Every framework mapping traceable to a named public document; anything derived rather than sourced marked as such.
- **The discontinuity guard survives.** Any series jumping 3× or more year on year is flagged with a visible caption. Auto-extraction makes this *more* important, not less — a boundary change that a human analyst would notice is exactly what a machine misses.

## 6. Scope reality

**A perfect BRSR extractor produces about a fifth of a full profile.** Only 149 of the 663 rows come from the BRSR section. The rest — board biographies, awards, ratings, memberships, policies, materiality, corporate information — come from elsewhere in the annual report, the company website and third parties.

Three ways to close that gap, in increasing order of effort:

1. **Ship the BRSR portion only**, and be explicit that it is a BRSR profile rather than a full ESG profile. Honest, and it is where the quantitative value is.
2. **Add a short structured intake form** for the company-information rows — address, listings, subsidiaries, ratings. Twenty fields, five minutes, no extraction risk.
3. **Extend extraction to the rest of the annual report.** Much harder; the content has no fixed schema. Not for the first version.

Option 1 plus option 2 is the sensible first product.

## 7. Cost and hosting

- **Processing is bursty**, not continuous: a handful of reports around each reporting season. Background jobs on modest infrastructure, not anything always-on and expensive.
- **Extraction cost per report must be measured in the spike.** At ₹25,000–30,000 per company per year, inference cost should be a small single-digit percentage. If it is not, the price or the approach has to change.
- **Published profiles are static.** Once generated, a profile is the same self-contained page as today — cheap to host, fast, and it still works if the pipeline is down.
- **Store the source PDF** against the profile. Re-extraction after an improvement should not require asking the client for the file again.

## 8. Sequencing

1. **Feasibility spike** — `phase3-spike-brief.md`. Two weeks. Decides everything below.
2. **Review interface, against fixture data.** Build it before the pipeline. If reviewing 140 indicators is not pleasant, discover it now.
3. **Extraction for one report end to end**, with a human review producing a publishable profile.
4. **Second and third reports, different companies.** One report proves the extractor works on one layout. Layout variance is the second-biggest risk after tables.
5. **Upload, accounts, hosting.** Last. These are well-understood problems; do them once the risky parts are known to work.

Resist the temptation to reverse steps 2 and 5. Upload and login feel like the start of the product and are actually the least informative parts to build.

## 9. Open questions

1. **Extraction accuracy.** Everything depends on it. The spike answers it.
2. **Who reviews** — you, or the client. Decide after the spike; high accuracy makes client review viable, patchy accuracy does not.
3. **Layout variance between companies.** One report is not a sample. Budget for at least three before believing any accuracy figure.
4. **Liability.** If a published profile misstates a figure and an investor relies on it, where does responsibility sit? Worth advice before the first paying client, not after.
5. **Data rights.** A company's own published data presented on its behalf is straightforward. Retaining extracted data to improve the extractor across clients is not — settle it in the contract.
6. **GRI licensing** for commercial use in software, still unresolved from Phase 1.
