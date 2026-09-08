"""
Turn a filed BRSR (inside an annual report PDF) into a profile page.

    python3 tools/extract_brsr.py extract  report.pdf
    python3 tools/extract_brsr.py publish  --review tools/extraction/review.json

Developer tool. Runs on the owner's machine, never in the browser; the
shipped page keeps its zero dependencies. Needs pdfplumber:

    pip3 install pdfplumber

WHY IT IS IN TWO STEPS
----------------------
`extract` reads the PDF and writes a review file. `publish` writes
data/disclosures.js. Nothing reaches the page without a human approving it
first — publish refuses to run while any figure is still unreviewed.

That is not caution for its own sake. The failure mode here is not a blank
field, it is a wrong emissions figure published under a real company's
name next to a link to their audited annual report.

WHAT IT DOES NOT DO
-------------------
It never invents a figure. A value it cannot find is marked not-disclosed
and renders empty. It never rounds and never converts units. Extraction
accuracy on real filings is UNMEASURED — see phase3-spike-brief.md.
"""
import argparse
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)

try:
    import pdfplumber
except ImportError:
    sys.exit("ERROR: pdfplumber is not installed.  Run: pip3 install pdfplumber")

# Reused rather than reimplemented, so the trend series and the
# discontinuity guard behave identically to the spreadsheet converter.
import convert as C
from brsr_indicators import GRI_BY_INDICATOR, SEBI_SOURCE

OUT_DIR = os.path.join(HERE, "extraction")

SECTION_C = re.compile(r"SECTION\s+C\b", re.I)
PRINCIPLE = re.compile(r"^\s*PRINCIPLE\s+(\d)\b", re.I | re.M)
ESSENTIAL = re.compile(r"^\s*Essential\s+Indicators?\s*$", re.I)
LEADERSHIP = re.compile(r"^\s*Leadership\s+Indicators?\s*$", re.I)
QUESTION = re.compile(r"^\s*(\d{1,2})\s*[.)]\s+(\S.*)$")

# "FY2026: 9.47 Joules" / "FY 2026 : 4,94,545.39 KL"
FY_VALUE = re.compile(r"FY\s*(\d{4})\s*:\s*([^;]+)", re.I)
# A number with Indian (4,94,545.39) or international (494,545.39) grouping.
NUMBER = re.compile(r"-?\d[\d,]*(?:\.\d+)?")
YEAR_IN_HEADER = re.compile(r"FY\s*(\d{4})", re.I)

PRINCIPLE_THEME = "BRSR Disclosures"


# --------------------------------------------------------------------------
# VALUES
# --------------------------------------------------------------------------

def parse_number(text):
    """'4,94,545.39 KL' -> (494545.39, 'KL', '4,94,545.39').

    Comma grouping is stripped because Indian and international grouping
    both appear in filed reports. The printed form is kept alongside so
    nothing is silently reformatted.
    """
    if text is None:
        return None, "", ""
    flat = " ".join(str(text).split())
    m = NUMBER.search(flat)
    if not m:
        return None, "", flat
    raw = m.group(0)
    try:
        value = float(raw.replace(",", ""))
    except ValueError:
        return None, "", flat
    unit = (flat[:m.start()] + " " + flat[m.end():]).strip(" :;,.")
    unit = " ".join(unit.split())
    return value, unit, raw


# --------------------------------------------------------------------------
# LOCATE
# --------------------------------------------------------------------------

def locate(pdf):
    """Find the BRSR section and each principle's page range.

    Returns (report, problems). `report` records what was found so the
    reliability of this step can be judged rather than assumed.
    """
    pages = []
    for i, page in enumerate(pdf.pages, start=1):
        pages.append((i, page.extract_text() or ""))

    section_c_page = next((n for n, t in pages if SECTION_C.search(t)), None)

    starts = []
    for n, text in pages:
        for m in PRINCIPLE.finditer(text):
            starts.append((int(m.group(1)), n))

    # Keep the first page each principle appears on, in page order.
    seen, ordered = set(), []
    for num, page_no in sorted(starts, key=lambda x: x[1]):
        if num not in seen:
            seen.add(num)
            ordered.append((num, page_no))

    ranges = {}
    for idx, (num, start) in enumerate(ordered):
        end = ordered[idx + 1][1] - 1 if idx + 1 < len(ordered) else len(pages)
        ranges[num] = (start, max(start, end))

    problems = []
    if section_c_page is None:
        problems.append("Could not find a 'SECTION C' heading.")
    if not ranges:
        problems.append("Could not find any 'PRINCIPLE n' headings.")

    return {
        "pages": len(pages),
        "section_c_page": section_c_page,
        "principles": {str(k): list(v) for k, v in sorted(ranges.items())},
    }, problems


# --------------------------------------------------------------------------
# SPLIT
# --------------------------------------------------------------------------

def page_lines(page):
    """Text lines with their vertical position, so tables can be tied to
    the question they sit under."""
    words = page.extract_words(use_text_flow=False, keep_blank_chars=False)
    rows = {}
    for w in words:
        key = round(w["top"] / 3.0)
        rows.setdefault(key, []).append(w)
    lines = []
    for key in sorted(rows):
        ws = sorted(rows[key], key=lambda w: w["x0"])
        lines.append({"top": min(w["top"] for w in ws),
                      "text": " ".join(w["text"] for w in ws)})
    return lines


def split_principle(pdf, principle, start, end):
    """Cut one principle's pages into its numbered indicators.

    BRSR questions are numbered under 'Essential Indicators' and
    'Leadership Indicators', so position gives the code (question 3 under
    Principle 6's essential indicators is P6-E3). No question wording is
    needed, which matters because SEBI's exact phrasing is not available
    in this project.
    """
    marks = []          # (page_no, top, block) question boundaries
    block = None        # "E" or "L"

    for page_no in range(start, end + 1):
        page = pdf.pages[page_no - 1]
        for line in page_lines(page):
            text = line["text"]
            if ESSENTIAL.match(text):
                block = "E"
                continue
            if LEADERSHIP.match(text):
                block = "L"
                continue
            m = QUESTION.match(text)
            if m and block:
                marks.append({
                    "n": int(m.group(1)),
                    "block": block,
                    "page": page_no,
                    "top": line["top"],
                    "stub": m.group(2).strip(),
                })

    indicators = []
    for i, mark in enumerate(marks):
        nxt = marks[i + 1] if i + 1 < len(marks) else None
        code = "P%d-%s%d" % (principle, mark["block"], mark["n"])
        indicators.append({
            "code": code,
            "principle": principle,
            "block": "Essential" if mark["block"] == "E" else "Leadership",
            "question": mark["stub"],
            "page": mark["page"],
            "start": (mark["page"], mark["top"]),
            "end": (nxt["page"], nxt["top"]) if nxt else (end, 10 ** 6),
        })
    return indicators


def within(pos, start, end):
    return start <= pos < end


def collect_content(pdf, ind):
    """Narrative text and tables belonging to one indicator."""
    (sp, st), (ep, et) = ind["start"], ind["end"]
    narrative, tables = [], []

    for page_no in range(sp, ep + 1):
        page = pdf.pages[page_no - 1]
        lo = st if page_no == sp else -1
        hi = et if page_no == ep else 10 ** 6

        # Table bands first, so their rows can be kept out of the narrative.
        bands = []
        for tbl in page.find_tables():
            top, bottom = tbl.bbox[1], tbl.bbox[3]
            bands.append((top, bottom))
            if within((page_no, top), (page_no, lo), (page_no, hi)):
                extracted = tbl.extract()
                if extracted and len(extracted) > 1:
                    tables.append({"page": page_no, "rows": extracted})

        for line in page_lines(page):
            if not within((page_no, line["top"]), (page_no, lo), (page_no, hi)):
                continue
            if line["top"] == lo:
                continue              # the question line itself
            # A table is rendered as stat blocks; repeating its rows as
            # prose underneath made every figure appear twice.
            if any(t - 2 <= line["top"] <= b + 2 for t, b in bands):
                continue
            narrative.append(line["text"])

    text = " ".join(narrative)
    text = re.sub(r"\s{2,}", " ", text).strip()
    return text, tables


# --------------------------------------------------------------------------
# FIGURES
# --------------------------------------------------------------------------

def figures_from_table(table):
    """Read a year-over-year table into figures.

    The header row must name the years; without a year a figure cannot be
    placed on a trend line, so it is recorded at low confidence rather
    than guessed at.
    """
    out = []
    rows = table["rows"]
    header = [(c or "") for c in rows[0]]
    year_cols = {}
    for idx, cell in enumerate(header):
        m = YEAR_IN_HEADER.search(cell.replace("\n", " "))
        if m:
            year_cols[idx] = m.group(1)

    for row in rows[1:]:
        if not row or not row[0]:
            continue
        label = " ".join(str(row[0]).split())
        for idx, year in year_cols.items():
            if idx >= len(row):
                continue
            value, unit, raw = parse_number(row[idx])
            if value is None:
                continue
            out.append({
                "measure": label,
                "value": value,
                "raw": raw,
                "unit": unit,
                "year": year,
                "page": table["page"],
                "source": "table",
                "confidence": 0.9,
            })
    return out


def figures_from_text(text, page):
    """Fallback for figures written into prose rather than tabulated."""
    out = []
    for m in FY_VALUE.finditer(text):
        year = m.group(1)
        value, unit, raw = parse_number(m.group(2))
        if value is None:
            continue
        before = text[max(0, m.start() - 90):m.start()]
        label = re.split(r"[;:.]", before)[-1].strip(" ()abcdefghij")
        out.append({
            "measure": " ".join(label.split())[:80] or "Reported figure",
            "value": value,
            "raw": raw,
            "unit": unit,
            "year": year,
            "page": page,
            "source": "narrative",
            "confidence": 0.75,
        })
    return out


def dedupe(figures):
    """A figure tabulated and then repeated in prose is one figure."""
    best = {}
    for f in figures:
        key = (round(f["value"], 6), f["year"], f["unit"].lower())
        if key not in best or f["confidence"] > best[key]["confidence"]:
            best[key] = f
    return sorted(best.values(), key=lambda f: (f["measure"], f["year"]))


# --------------------------------------------------------------------------
# EXTRACT
# --------------------------------------------------------------------------

def extract(pdf_path, principles):
    with pdfplumber.open(pdf_path) as pdf:
        located, problems = locate(pdf)
        if problems:
            for p in problems:
                print("  PROBLEM: " + p)

        wanted = principles or sorted(int(k) for k in located["principles"])
        indicators = []
        for num in wanted:
            rng = located["principles"].get(str(num))
            if not rng:
                print("  Principle %d not found — skipped." % num)
                continue
            found = split_principle(pdf, num, rng[0], rng[1])
            for ind in found:
                text, tables = collect_content(pdf, ind)
                figs = figures_from_table_list(tables) + figures_from_text(text, ind["page"])
                ind["narrative"] = text
                ind["figures"] = dedupe(figs)
                ind["status"] = "extracted"
                ind.pop("start", None)
                ind.pop("end", None)
                indicators.append(ind)
            print("  Principle %d: pages %d-%d, %d indicators"
                  % (num, rng[0], rng[1], len(found)))

    return {
        "source_pdf": os.path.basename(pdf_path),
        "located": located,
        "problems": problems,
        "indicators": indicators,
    }


def figures_from_table_list(tables):
    out = []
    for t in tables:
        out.extend(figures_from_table(t))
    return out


# --------------------------------------------------------------------------
# REVIEW FILE
# --------------------------------------------------------------------------

def write_review(payload, out_dir):
    os.makedirs(out_dir, exist_ok=True)
    json_path = os.path.join(out_dir, "review.json")
    with open(json_path, "w", encoding="utf-8") as fh:
        json.dump(payload, fh, indent=2, ensure_ascii=False)

    rows = []
    for ind in payload["indicators"]:
        figs = ind["figures"]
        cells = "".join(
            "<tr><td>%s</td><td class='num'>%s</td><td>%s</td><td>%s</td>"
            "<td>p.%s</td><td>%s</td><td class='conf %s'>%.2f</td></tr>"
            % (esc(f["measure"]), esc(f["raw"]), esc(f["unit"]), f["year"],
               f["page"], f["source"],
               "low" if f["confidence"] < 0.8 else "ok", f["confidence"])
            for f in figs
        ) or "<tr><td colspan='7' class='none'>No figures found.</td></tr>"
        rows.append(
            "<section><h2>%s <span class='blk'>%s · Principle %d</span></h2>"
            "<p class='q'>%s</p>"
            "<table><thead><tr><th>Measure</th><th>Value</th><th>Unit</th>"
            "<th>Year</th><th>Page</th><th>From</th><th>Conf.</th></tr></thead>"
            "<tbody>%s</tbody></table>"
            "<details><summary>Narrative (%d characters)</summary><p>%s</p></details>"
            "</section>"
            % (esc(ind["code"]), esc(ind["block"]), ind["principle"],
               esc(ind["question"]), cells, len(ind["narrative"]),
               esc(ind["narrative"][:4000]))
        )

    total_f = sum(len(i["figures"]) for i in payload["indicators"])
    low = sum(1 for i in payload["indicators"] for f in i["figures"]
              if f["confidence"] < 0.8)
    html = REVIEW_TEMPLATE % {
        "pdf": esc(payload["source_pdf"]),
        "inds": len(payload["indicators"]),
        "figs": total_f,
        "low": low,
        "body": "".join(rows),
    }
    html_path = os.path.join(out_dir, "review.html")
    with open(html_path, "w", encoding="utf-8") as fh:
        fh.write(html)
    return json_path, html_path


def esc(text):
    return (str(text).replace("&", "&amp;").replace("<", "&lt;")
            .replace(">", "&gt;"))


REVIEW_TEMPLATE = """<!doctype html>
<meta charset="utf-8"><title>BRSR extraction review</title>
<style>
 body{font:15px/1.55 -apple-system,BlinkMacSystemFont,"Segoe UI",Arial,sans-serif;
      margin:0;background:#f7f8f9;color:#1a1a1a}
 header{background:#0f4c5c;color:#fff;padding:22px 28px}
 header h1{margin:0 0 4px;font-size:20px}
 header p{margin:0;opacity:.85;font-size:14px}
 .warn{background:#fff4e5;border-left:4px solid #b26a00;padding:12px 16px;
       margin:20px 28px;font-size:14px}
 main{padding:0 28px 40px;max-width:1100px}
 section{background:#fff;border:1px solid #e2e5e8;border-radius:6px;
         padding:16px 18px;margin:16px 0}
 h2{font-size:16px;margin:0 0 4px}
 .blk{font-weight:400;color:#667;font-size:13px}
 .q{margin:0 0 10px;color:#445;font-size:14px}
 table{border-collapse:collapse;width:100%%;font-size:13.5px}
 th,td{border-bottom:1px solid #eceff1;padding:6px 8px;text-align:left}
 th{background:#f2f4f5;font-size:12px;text-transform:uppercase;letter-spacing:.03em}
 .num{font-variant-numeric:tabular-nums;font-weight:600}
 .conf.low{color:#b26a00;font-weight:700}
 .none{color:#889;font-style:italic}
 details{margin-top:10px;font-size:13.5px;color:#445}
 summary{cursor:pointer;color:#0f4c5c}
</style>
<header>
 <h1>BRSR extraction — review before publishing</h1>
 <p>%(pdf)s · %(inds)s indicators · %(figs)s figures · %(low)s below 0.80 confidence</p>
</header>
<div class="warn">
 <strong>Nothing here has been published.</strong> Check every figure against
 the page number given, then mark each indicator's <code>status</code> in
 <code>review.json</code> as <code>approved</code>, <code>corrected</code> or
 <code>not_disclosed</code>. <code>publish</code> refuses to run while any
 indicator is still <code>extracted</code>.
</div>
<main>%(body)s</main>
"""


# --------------------------------------------------------------------------
# PUBLISH
# --------------------------------------------------------------------------

APPROVED = {"approved", "corrected", "not_disclosed"}


def build_rows(payload):
    """Approved indicators -> rows in the shape data/disclosures.js uses."""
    rows = []
    for ind in payload["indicators"]:
        if ind["status"] == "not_disclosed":
            continue

        category = "BRSR Section C: Principle %d" % ind["principle"]
        metrics = [
            # The label carries measure, year and unit because that is what
            # build_series() parses. Values are untouched.
            {"value": f["value"],
             "label": "%s %s (%s)" % (f["measure"], f["year"], f["unit"]) if f["unit"]
                      else "%s %s" % (f["measure"], f["year"])}
            for f in ind["figures"]
        ]

        C.CURRENT_SUBFACTOR[0] = ind["question"][:80]
        series, standalone = C.build_series(metrics)

        frameworks = [{
            "name": "BRSR",
            "detail": "%s · Principle %d · %s" % (ind["code"], ind["principle"], ind["block"]),
            "indicator": ind["code"],
            "verified": True,
            "source": SEBI_SOURCE,
        }]
        # GRI_BY_INDICATOR holds a preformatted string ("GRI 302-1-a, ..."),
        # not a list. Joining it character by character is what produced
        # "G, R, I, , 3, 0, 2" on the page.
        exact = GRI_BY_INDICATOR.get(ind["code"])
        if exact:
            frameworks.append({
                "name": "GRI",
                "detail": exact.replace("GRI ", ""),
                "full": exact,
                "level": "indicator",
                "verified": True,
                "source": C.LINKAGE_SOURCE,
            })
            C.add_ifc(frameworks, exact)

        rows.append({
            "theme": PRINCIPLE_THEME,
            "category": category,
            "subfactor": ind["question"][:120],
            # Structural facts from the form only — no keyword guessing.
            "keywords": ["BRSR", "Principle %d" % ind["principle"], ind["block"]],
            "documents": [{"label": "%s (Page %d)" % (payload["source_pdf"], ind["page"]),
                           "url": None}],
            "metrics": metrics,
            "frameworks": frameworks,
            "series": series,
            "standalone": standalone,
            "highlights": ind["narrative"],
        })
    return rows


def publish(review_path, data_path, company, replace=False):
    payload = json.load(open(review_path, encoding="utf-8"))

    pending = [i["code"] for i in payload["indicators"]
               if i.get("status") not in APPROVED]
    if pending:
        print("REFUSING TO PUBLISH — %d indicator(s) not reviewed:" % len(pending))
        for code in pending[:20]:
            print("   " + code)
        if len(pending) > 20:
            print("   ... and %d more" % (len(pending) - 20))
        print("\nOpen tools/extraction/review.html, check each figure against")
        print("its page, then set status in review.json and run this again.")
        return 1

    rows = build_rows(payload)
    if not rows:
        print("REFUSING TO PUBLISH — every indicator was marked not_disclosed.")
        return 1

    # An extracted profile covers the BRSR section only. Writing it over an
    # existing profile would silently replace a full one — the demo build is
    # 663 rows — with a fifth of a profile, which is the last thing anyone
    # wants to discover in front of a client.
    if os.path.exists(data_path) and not replace:
        existing = "an existing profile"
        try:
            text = open(data_path, encoding="utf-8").read()
            existing = "%d rows" % text.count('"subfactor"')
        except OSError:
            pass
        print("REFUSING TO PUBLISH — %s already has %s."
              % (os.path.relpath(data_path, ROOT), existing))
        print("This extraction has %d rows and covers the BRSR section only."
              % len(rows))
        print("\nWriting it here would replace that profile. Either:")
        print("  - keep both, by publishing elsewhere:")
        print("      --data data/extracted.js")
        print("  - or replace it deliberately:")
        print("      --replace")
        return 1

    figures = sum(len(r["metrics"]) for r in rows)
    print("Publishing %d rows, %d figures." % (len(rows), figures))
    C.emit(rows, data_path, company, anonymised=False)
    print("\nThis profile covers the BRSR section only. A full profile also")
    print("carries board, awards, ratings and corporate-information rows,")
    print("which do not come from the BRSR and are not extracted here.")
    return 0


# --------------------------------------------------------------------------

def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)

    e = sub.add_parser("extract", help="read a PDF and write a review file")
    e.add_argument("pdf")
    e.add_argument("--principle", type=int, action="append",
                   help="limit to one principle (repeatable); default all found")
    e.add_argument("--out", default=OUT_DIR)

    p = sub.add_parser("publish", help="write data/disclosures.js from an approved review")
    p.add_argument("--review", default=os.path.join(OUT_DIR, "review.json"))
    p.add_argument("--data", default=os.path.join(ROOT, "data", "disclosures.js"))
    p.add_argument("--company", default="Company Name")
    p.add_argument("--replace", action="store_true",
                   help="overwrite an existing profile instead of refusing")

    args = ap.parse_args()

    if args.cmd == "extract":
        if not os.path.exists(args.pdf):
            sys.exit("ERROR: no such file: %s" % args.pdf)
        print("Reading %s" % args.pdf)
        payload = extract(args.pdf, args.principle)
        j, h = write_review(payload, args.out)
        total = sum(len(i["figures"]) for i in payload["indicators"])
        print("\n%d indicators, %d figures." % (len(payload["indicators"]), total))
        print("Review file: %s" % h)
        print("Open it, check every figure against its page, then set each")
        print("indicator's status in %s and run publish." % j)
        return 0

    return publish(args.review, args.data, args.company, args.replace)


if __name__ == "__main__":
    sys.exit(main())
