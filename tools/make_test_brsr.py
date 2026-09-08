"""
Builds a TEST BRSR PDF from the real Principle 6 disclosure text.

Developer tool only. This exists so tools/extract_brsr.py can be tested
without a real annual report to hand. It is a FRIENDLY fixture: clean
digital text, regular tables, predictable headings. Passing against it
proves the extractor's plumbing works. It proves nothing about real
filings, which carry merged cells, footnotes, rotated tables and scans.

Usage:  python3 tools/make_test_brsr.py
Writes: tools/fixtures/test-brsr.pdf
"""
import json, os, re, subprocess, sys, html

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
CHROME = "/opt/pw-browsers/chromium-1194/chrome-linux/chrome"

# SEBI Principle 6 question wording, Annexure I to circular 2021/562.
# Indexed by the position the question occupies in the filed form; the
# portal's row titles are used where the full SEBI text is not carried in
# the source data.
ESSENTIAL_STUBS = {
    1: "Details of total energy consumption (in Joules or multiples) and energy intensity",
    2: "Does the entity have any sites / facilities identified as designated consumers (DCs) "
       "under the Performance, Achieve and Trade (PAT) Scheme of the Government of India?",
    3: "Provide details of the following disclosures related to water",
    4: "Has the entity implemented a mechanism for Zero Liquid Discharge?",
    5: "Please provide details of air emissions (other than GHG emissions) by the entity",
    6: "Provide details of greenhouse gas emissions (Scope 1 and Scope 2 emissions) and its intensity",
    7: "Does the entity have any project related to reducing Green House Gas emission?",
    8: "Provide details related to waste management by the entity",
    9: "Briefly describe the waste management practices adopted in your establishments",
    10: "Provide details of any operations/offices in/around ecologically sensitive areas",
    11: "Details of environmental impact assessments of projects undertaken by the entity",
    12: "Is the entity compliant with the applicable environmental law/ regulations/ guidelines in India",
}
LEADERSHIP_STUBS = {
    2: "Please provide details of total Scope 3 emissions and its intensity",
    3: "With respect to the ecologically sensitive areas reported at Question 10 of Essential "
       "Indicators above, provide details of significant direct and indirect impact of the entity",
    4: "Please provide details of total Scope 3 emissions and its intensity",
    5: "Provide details of any initiatives taken to protect and restore biodiversity",
    6: "Details of initiatives undertaken towards resource efficiency and innovation",
    7: "Does the entity have a business continuity and disaster management plan?",
    8: "Disclose any significant adverse impact to the environment arising from the value chain",
    9: "Percentage of value chain partners screened using environmental impact assessments",
}

# "(a) Label: (i) FY2026: 1,234 KL; (ii) FY2025: 900 KL"  ->  a real table.
# Labels run long in a filed BRSR ("Energy intensity per rupee of turnover
# adjusted for Purchasing Power Parity (...)"), so the cap is generous.
SEGMENT = re.compile(r"\(([a-z])\)\s*([^:]{3,220}?):", re.I)
FY_VALUE = re.compile(r"FY\s*(\d{4})\s*:\s*([^;]+)", re.I)


def load_rows():
    src = open(os.path.join(ROOT, "data", "disclosures.js"), encoding="utf8").read()
    blob = src[src.index("{", src.index("window.ESG_DATA")):].rstrip().rstrip(";")
    return json.loads(blob)["rows"]


def as_table(narrative):
    """Turn the '(a) label: (i) FY2026 ... (ii) FY2025 ...' runs into an HTML table.

    Parsed in two stages rather than one regex: a single pattern kept
    truncating values at the decimal point (4.79 became 4).
    """
    # "(i) FY2026" also matches the segment pattern; drop those so a
    # segment is a real parameter label rather than a year marker.
    marks = [m for m in SEGMENT.finditer(narrative)
             if not re.match(r"\s*FY\s*\d{4}\s*$", m.group(2), re.I)]
    if len(marks) < 2:
        return None, narrative
    rows, years, consumed = [], [], []
    for i, m in enumerate(marks):
        end = marks[i + 1].start() if i + 1 < len(marks) else len(narrative)
        chunk = narrative[m.end():end]
        vals = [(y, v.strip().rstrip(". ").strip()) for y, v in FY_VALUE.findall(chunk)]
        if len(vals) < 2:
            continue
        label = re.sub(r"^\(?[ivx]+\)?\s*", "", m.group(2).strip())
        rows.append((label, vals[0][1], vals[1][1]))
        years = [vals[0][0], vals[1][0]]
        consumed.append((m.start(), end))
    if len(rows) < 2:
        return None, narrative
    out = [f"<table><thead><tr><th>Parameter</th><th>FY {years[0]}</th>"
           f"<th>FY {years[1]}</th></tr></thead><tbody>"]
    for label, v1, v2 in rows:
        out.append(
            f"<tr><td>{html.escape(label)}</td>"
            f"<td>{html.escape(v1)}</td><td>{html.escape(v2)}</td></tr>"
        )
    out.append("</tbody></table>")
    keep, prev = [], 0
    for a, b in consumed:
        keep.append(narrative[prev:a])
        prev = b
    keep.append(narrative[prev:])
    leftover = re.sub(r"\s{2,}", " ", "".join(keep)).strip(" ;:.")
    return "\n".join(out), leftover


def build_html(rows):
    p6 = [r for r in rows if r["category"] == "BRSR Section C: Principle 6"]
    by_code = {}
    for r in p6:
        tag = next((f for f in r.get("frameworks", []) if f["name"] == "BRSR"), None)
        if tag:
            by_code[tag["detail"].split(" · ")[0].strip()] = r

    parts = [
        "<style>",
        "body{font-family:Georgia,serif;font-size:11pt;line-height:1.5;margin:0}",
        ".pg{page-break-after:always;padding:26mm 20mm}",
        "h1{font-size:17pt;margin:0 0 14pt} h2{font-size:13pt;margin:18pt 0 8pt}",
        "h3{font-size:11.5pt;margin:14pt 0 6pt}",
        ".q{font-weight:bold;margin:12pt 0 4pt}",
        "table{border-collapse:collapse;width:100%;margin:8pt 0;font-size:10pt}",
        "th,td{border:1px solid #444;padding:4pt 6pt;text-align:left;vertical-align:top}",
        "th{background:#eee}",
        "</style>",
    ]

    # Filler front matter, so LOCATE has to do real work.
    parts.append("<div class='pg'><h1>Integrated Annual Report 2025-26</h1>"
                 "<p>Demonstration fixture. The pages that follow stand in for the "
                 "front half of an annual report.</p></div>")
    for n in range(2, 19):
        parts.append(
            f"<div class='pg'><h2>Management Discussion and Analysis</h2>"
            f"<p>Filler page {n}. Operational review, financial commentary and "
            f"directors' report content would appear here in a filed report. "
            f"This text exists so the BRSR section must be located rather than "
            f"assumed to start at page one.</p></div>"
        )

    parts.append("<div class='pg'><h1>BUSINESS RESPONSIBILITY AND SUSTAINABILITY REPORT</h1>"
                 "<h2>SECTION A: GENERAL DISCLOSURES</h2>"
                 "<p>Corporate identity and general disclosures appear in this section.</p></div>")
    parts.append("<div class='pg'><h2>SECTION B: MANAGEMENT AND PROCESS DISCLOSURES</h2>"
                 "<p>Policy and management process disclosures appear in this section.</p></div>")

    body = ["<div class='pg'>",
            "<h2>SECTION C: PRINCIPLE WISE PERFORMANCE DISCLOSURE</h2>",
            "<h2>PRINCIPLE 6</h2>",
            "<p>Businesses should respect and make efforts to protect and restore the environment.</p>",
            "<h3>Essential Indicators</h3>"]

    order_e = ["P6-E%d" % i for i in range(1, 13)]
    order_l = ["P6-L%d" % i for i in range(2, 10)]

    for i, code in enumerate(order_e, start=1):
        row = by_code.get(code)
        if not row:
            continue
        stub = ESSENTIAL_STUBS.get(i, row["subfactor"])
        body.append(f"<div class='q'>{i}. {html.escape(stub)}</div>")
        table, rest = as_table(row["highlights"])
        if table:
            body.append(table)
            if rest:
                body.append(f"<p>{html.escape(rest)}</p>")
        else:
            body.append(f"<p>{html.escape(row['highlights'])}</p>")
        if i in (4, 8):
            body.append("</div><div class='pg'>")

    body.append("<h3>Leadership Indicators</h3>")
    for code in order_l:
        row = by_code.get(code)
        if not row:
            continue
        i = int(code.split("-L")[1])
        stub = LEADERSHIP_STUBS.get(i, row["subfactor"])
        body.append(f"<div class='q'>{i}. {html.escape(stub)}</div>")
        table, rest = as_table(row["highlights"])
        if table:
            body.append(table)
            if rest:
                body.append(f"<p>{html.escape(rest)}</p>")
        else:
            body.append(f"<p>{html.escape(row['highlights'])}</p>")
        if i == 5:
            body.append("</div><div class='pg'>")
    body.append("</div>")

    parts.extend(body)
    parts.append("<div class='pg'><h2>PRINCIPLE 7</h2>"
                 "<p>Businesses, when engaging in influencing public and regulatory policy, "
                 "should do so in a manner that is responsible and transparent.</p>"
                 "<h3>Essential Indicators</h3><div class='q'>1. a. Number of affiliations with "
                 "trade and industry chambers/ associations.</div>"
                 "<p>The Company is a member of 8 trade and industry chambers.</p></div>")
    return "\n".join(parts)


def main():
    rows = load_rows()
    html_path = os.path.join(HERE, "fixtures", "test-brsr.html")
    pdf_path = os.path.join(HERE, "fixtures", "test-brsr.pdf")
    os.makedirs(os.path.dirname(html_path), exist_ok=True)
    open(html_path, "w", encoding="utf8").write(build_html(rows))
    subprocess.run(
        [CHROME, "--headless", "--no-sandbox", "--disable-gpu",
         "--no-pdf-header-footer", f"--print-to-pdf={pdf_path}",
         "--virtual-time-budget=5000", "file://" + html_path],
        check=True, capture_output=True,
    )
    print("wrote", pdf_path, os.path.getsize(pdf_path), "bytes")


if __name__ == "__main__":
    main()
