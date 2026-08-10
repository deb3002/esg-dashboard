# CLAUDE.md — ESG Dashboard

## Who you're working with

Debraj, a **sustainability consultant**. Not a developer — he does not read or write code.

This has real consequences for how you work:

- **He cannot review your code for correctness.** He can only judge what he sees on screen. So the burden of verification is entirely on you: test your own work, open the page and check it renders, and don't hand back something you haven't confirmed works.
- **Never answer a question with code.** If he asks "why is the table empty?", the answer is "the factor values in your data file are spelled 'Environment' but the filter looks for 'Environmental'" — not a diff.
- **Explain in plain language, always.** If you must name a technical thing, define it in the same sentence. "A CORS restriction — browsers block pages opened directly from your hard drive from loading local data files."
- **Don't assume tooling knowledge.** He may not have used a terminal, a local server, or git before. If a step needs one, spell it out.

## Who the work is for

His **clients** — companies that need to present their sustainability disclosures (BRSR, GRI-style reports) in something more usable than a 200-page PDF.

That means anything Debraj shows a client must look finished. Placeholder text, lorem ipsum, broken links, and console errors are not acceptable in anything he might put on screen in front of someone. If something is unfinished, say so explicitly rather than leaving him to discover it live.

## How to work

**Explain before changing things.**
Before you edit or create files, say in one or two plain sentences what you're about to do and why. Not a lecture — just enough that he isn't surprised by what changed. For a multi-step change, outline the steps first and get a nod before starting.

**Ask before adding dependencies.**
Do not add a library, framework, CDN link, or npm package without asking first. Explain what it does, why the alternative is worse, and what it costs (another thing that can break, another thing to keep updated). The current build is specced to have **zero** dependencies — assume that's the intended state and that adding one needs a real justification.

**Keep commits small.**
One logical change per commit, with a message a non-developer can read — "add search box to filter row", not "refactor filter state". This keeps changes reversible: if something breaks, undoing one small commit is easy, undoing a large one isn't.

## The project

A single-page ESG disclosure profile viewer. Full requirements are in **`product-spec.md`** in this folder — read it before doing anything.

Key points, so you don't have to reconstruct them:

- **Stack:** plain HTML, CSS, vanilla JavaScript. No framework. **The shipped page has zero dependencies** and that is not negotiable.
- **One exception, and it is only an exception:** `tools/convert.py` turns the source spreadsheet into the page's data file. It runs once on Debraj's machine, never in the browser, and whatever it needs must never end up in the shipped page. Adding a library to the *page* is a different conversation from adding one to the *converter*.
- **Scope:** deliberately minimal. `product-spec.md` has a "Left Out of This Build" section that is a hard boundary, not a wishlist. Do not build anything on that list, even if it seems like an obvious improvement. If you think something on it is genuinely needed, raise it as a question rather than building it. **The spec is revised — check the revision note at the top and work from the current one.**
- **Data:** one bundled local file, generated from `ESGReport.xls`. No API calls, no server, no credentials.
- **It must open by double-clicking.** He demos this live to clients. If a change would require running a local server to view the page, flag it before making it. This is also why the page loads its data from a script file rather than fetching it — browsers block a locally-opened page from loading local files.

## The data

`data/disclosures.js` is **generated, not written**. Never hand-edit it. If something in it is wrong, fix the converter and re-run.

The source is `ESGReport.xls` — 663 real disclosure rows exported from the Churchgate Partners ESG portal. The spec lists eight checks the conversion must pass (row count, theme totals, hyperlink count, metric rows, keyword count). **Run them and show Debraj the numbers.** He cannot read the data file to spot 40 missing rows; a conversion that silently drops data will reach a client before anyone notices.

## Ground rules

- **Never put an API key, token, or password in any file in this project.** Not in HTML, not in JavaScript, not in a comment. If something ever needs one, stop and explain the safe way to handle it.
- **The data is real, which cuts both ways.** These are Escorts Kubota's genuine published figures — emissions, water, board composition — under their own name, with links to their actual annual report. So: never invent a figure, never fill a gap with a plausible-looking number, and never round or unit-convert a value on its way into the data file. If a row's data is missing, it renders empty. An invented number attributed to a named company is a reputational problem for a consultant showing this to clients.
- **Whether the demo stays under the real company name is undecided.** Don't assume either way — it's flagged in the spec's Open Questions and Debraj needs to answer it.
- **Tell him when you're unsure.** A flagged uncertainty is cheap; a confident wrong answer he repeats to a client is not.
- **If something breaks, say so plainly** and explain what you'll try. Don't quietly work around it.
