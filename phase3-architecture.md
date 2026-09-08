# Phase 3 Architecture — Upload a report, get a profile

**Revision 2 — 8 Sep 2026.** The reuse claims are corrected. Revision 1 marked the **Derive** stage as built; about half of it is not, and the half that is not depends on metadata a PDF does not contain. Keywords, the BRSR tag and the BRSR Core tag are all copied from the portal's Keywords column — Churchgate's analysts applied them by hand — so extraction produces none of them, and the keyword filter has nothing to populate it. GRI, IFC and the discontinuity guard do genuinely carry over. "Roughly a third of the pipeline exists" is revised down accordingly, and the indicator schema's key direction is noted.

**Status: provisional.** Written alongside the feasibility spike, not after it. Every extraction decision here is contingent on `phase3-spike-brief.md` producing a usable accuracy number. If extraction turns out to be poor, most of this document changes; the parts that would survive are marked.

---

## 1. The honest starting point

**The viewer survives. Rather less behind it does.**

Today's build is deliberately serverless, accountless and zero-dependency, and opens by double-clicking. Upload requires a server, file storage, background processing, an account per company and a review interface. That is not an extension of Phase 1 — it is a different application that reuses the front end.

Say that plainly to anyone who assumes Phase 3 is "adding an upload button".

What genuinely carries over:

| Already built | Where | Carries over? |
|---|---|---|
| The profile viewer — filters, charts, export, print | `index.html`, `app.js`, `styles.css` | **Yes**, unchanged |
| Figure normalisation to value + unit + year | `tools/convert.py` | **Yes**, logic survives; input shape changes |
| Trend series and the discontinuity guard | `tools/convert.py` | **Yes** — the guard is pure logic on a series |
| GRI and IFC mappings | `tools/brsr_indicators.py` | **Yes** — both derive from the indicator code |
| BRSR indicator schema | `tools/brsr_indicators.py` | **Partly** — see below |
| Keywords, BRSR tag, BRSR Core tag | `tools/convert.py` | **No** — see below |
| Anonymisation | `tools/convert.py` | Demo tooling only; client profiles are not anonymised |
| 107 automated checks | `tools/test.js` | **Yes**, for the viewer; extraction needs its own |

**The schema is keyed the wrong way round for extraction.** `INDICATOR_CODES` maps *the portal's row titles* to SEBI codes — `"Energy Consumption" → P6-E1`. A filed report carries SEBI's question wording, not the portal's shorthand. The code list and ordering are reusable; the lookup keys need rebuilding against SEBI's text.

**Keywords and the BRSR tags were never derived.** All 84 keywords come from a column in the portal's export, applied by Churchgate's analysts. The BRSR tag reads the `BRSR` keyword; BRSR Core reads `SEBI: Essential Core`; the Essential / Leadership / Core distinction reads the same column. The converter copies them across — it does not work them out. Extract from a raw PDF and none of them exist.

Roughly a quarter of the pipeline exists, and it is the fiddly, already-debugged quarter. That is still worth having — the discontinuity guard and the framework mappings were the hard parts — but it is less than a third.

---

## 2. Pipeline

```
  upload ──▶ locate ──▶ split ──▶ extract ──▶ derive ──▶ REVIEW ──▶ publish
```

| Stage | What it does | State |
|---|---|---|
| **Upload** | Accept a PDF, or a URL to one. Record its hash so the same report is never processed twice. | build |
| **Locate** | Find the BRSR section inside a 300-page annual report. Standard headings make this tractable. | build |
| **Split** | Cut into the numbered indicators using SEBI's format as the map. | schema exists, needs re-keying |
| **Extract** | Per indicator: narrative, tables, figures with unit and year, and the page each came from. | **build — the risk** |
| **Derive** | GRI and IFC tags, trend series, discontinuity flags. | **built** |
| **Derive** | Keywords, BRSR and BRSR Core tags. | **build — no longer supplied** |
| **Review** | A human confirms every figure against the source page before anything publishes. | **build — the product** |
| **Publish** | Generate the profile and host it. | build |

### The keyword gap needs a decision

The keyword dropdown is one of the four filters on the page and one of the more useful ones in a demo. After extraction it has nothing behind it. Three options, none of them settled:

1. **Drop the keyword filter** for extracted profiles. Theme, framework and search remain. Simplest, and search already covers most of what keywords are used for.
2. **Derive keywords from the indicator**, not from the text. Each SEBI indicator maps to a stable, defensible set of tags. Small, sourced, and consistent with how framework tagging already works.
3. **Derive keywords from the narrative** by keyword matching. **Do not do this.** It is the approach that produced 445 guessed GRI tags in revision 6 and was thrown away. The same objection applies here.

Option 2 is the one to cost during the spike.

## 3. The review interface is the product

This is the part most likely to be underestimated.

**If review is fast, mediocre extraction is fine. If review is painful, excellent extraction does not save you.** A reviewer facing 663 undifferentiated rows will abandon it. A reviewer working through the numbered indicators, each shown beside the page it came from, with figures pre-filled and highlighted, can finish a report in an afternoon.

Design requirements, in priority order:

1. **Source page beside every extracted answer.** Not a page number — the actual page image, with the extracted figure highlighted on it. Verification must be visual and immediate.
2. **Confidence-ordered queue.** Low-confidence extractions first. A reviewer who runs out of time should have spent it on the doubtful rows.
3. **Three actions only:** approve, correct, mark not-disclosed. Anything more elaborate slows it down.
4. **Nothing publishes unreviewed.** Not "flagged as unreviewed" — not published.
5. **Every keystroke recorded.** Who approved which figure, when, against which page. This is the audit trail that makes the output defensible, and it is also the training data for improving extraction.

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

This model is better than what the converter produces today, which packs the measure, year and unit into one label string (`"GHG Emission 2026 (tCO2e)"`) and then splits it again. Separate fields from the start. The series builder will need adapting to the new shape — a change of input, not a rewrite.

Watch unit notation: the same figure appears as `MT CO2e` in the BRSR narrative and `tCO2e` in the structured metrics. Same unit, two spellings. Normalise on the way in, without converting the value.

## 5. What must not change

These carry forward from Phase 1 unchanged, and are not negotiable.

- **Extract → review → publish. Never extract → publish.** A missing row is recoverable. A wrong emissions figure under a client's name, beside a link to their audited annual report, is not.
- **Never invent a figure.** No estimation, no interpolation, no "plausible" values. A figure that could not be found is marked not-disclosed and renders empty.
- **Never round or unit-convert on the way in.** Store the published precision exactly.
- **Provenance stays visible.** Every framework mapping traceable to a named public document; anything derived rather than sourced marked as such.
- **The discontinuity guard survives.** Any series jumping 3× or more year on year is flagged with a visible caption. Auto-extraction makes this *more* important, not less — a boundary change that a human analyst would notice is exactly what a machine misses.
- **No keyword-guessed tagging**, of frameworks or of keywords. Settled in Phase 1; it applies to anything the extractor produces too.

## 6. Scope reality

**A perfect BRSR extractor produces about a fifth of a full profile.** Only 149 of the 663 rows come from the BRSR section — 22%. The rest — board biographies, awards, ratings, memberships, policies, materiality, corporate information — come from elsewhere in the annual report, the company website and third parties.

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
2. **Review interface, against fixture data.** Build it before the pipeline. If reviewing the indicator list is not pleasant, discover it now.
3. **Extraction for one report end to end**, with a human review producing a publishable profile.
4. **Second and third reports, different companies.** One report proves the extractor works on one layout. Layout variance is the second-biggest risk after tables.
5. **Upload, accounts, hosting.** Last. These are well-understood problems; do them once the risky parts are known to work.

Resist the temptation to reverse steps 2 and 5. Upload and login feel like the start of the product and are actually the least informative parts to build.

## 9. Open questions

1. **Extraction accuracy.** Everything depends on it. The spike answers it.
2. **Who reviews** — you, or the client. Decide after the spike; high accuracy makes client review viable, patchy accuracy does not.
3. **What replaces the keyword filter**, per section 2. Option 2 is the likely answer but has not been costed.
4. **Layout variance between companies.** One report is not a sample. Budget for at least three before believing any accuracy figure.
5. **Liability.** If a published profile misstates a figure and an investor relies on it, where does responsibility sit? Worth advice before the first paying client, not after.
6. **Data rights.** A company's own published data presented on its behalf is straightforward. Retaining extracted data to improve the extractor across clients is not — settle it in the contract.
7. **GRI licensing** for commercial use in software, still unresolved from Phase 1.
