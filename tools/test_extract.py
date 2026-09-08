"""
Round-trip check for tools/extract_brsr.py.

Builds a BRSR PDF from the real Principle 6 disclosure text, extracts it
again, and checks every figure survives the round trip exactly.

WHAT THIS PROVES:  the machinery works — locate, split by indicator,
read tables, parse Indian and international digit grouping, keep the
published precision, hold the page number.

WHAT IT DOES NOT PROVE:  anything about a real filing. The fixture is
clean digital text with regular tables. Real reports carry merged cells,
footnotes, rotated tables and scans. Accuracy on real filings is
unmeasured — that is what phase3-spike-brief.md is for.

    python3 tools/test_extract.py
"""
import json, os, re, subprocess, sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)
import make_test_brsr as M

FY = re.compile(r"FY\s*(\d{4})\s*:\s*([^;]+)", re.I)
NUM = re.compile(r"-?\d[\d,]*(?:\.\d+)?")
FIXTURE = os.path.join(HERE, "fixtures", "test-brsr.pdf")
REVIEW = os.path.join(HERE, "extraction", "review.json")

fails = []


def check(label, got, want):
    ok = got == want
    print("  %s  %-52s %s" % ("PASS" if ok else "FAIL", label, got))
    if not ok:
        fails.append("%s: got %r, wanted %r" % (label, got, want))


def key_figures(narrative):
    out = set()
    for year, tail in FY.findall(narrative):
        m = NUM.search(tail)
        if m:
            try:
                out.add((year, float(m.group(0).replace(",", ""))))
            except ValueError:
                pass
    return out


def main():
    print("Building fixture and extracting...")
    subprocess.run([sys.executable, os.path.join(HERE, "make_test_brsr.py")],
                   check=True, capture_output=True)
    subprocess.run([sys.executable, os.path.join(HERE, "extract_brsr.py"),
                    "extract", FIXTURE, "--principle", "6"],
                   check=True, capture_output=True)

    data = json.load(open(REVIEW, encoding="utf-8"))
    inds = {i["code"]: i for i in data["indicators"]}
    got = {c: {(f["year"], round(f["value"], 6)) for f in i["figures"]}
           for c, i in inds.items()}

    print("\nStructure")
    check("BRSR section located", data["located"]["section_c_page"] is not None, True)
    check("no locate problems", data["problems"], [])
    check("indicators found", len(inds), 20)
    check("essential run E1-E12", sorted(
        int(c.split("-E")[1]) for c in inds if "-E" in c), list(range(1, 13)))
    check("P6-L1 absent, as in the source profile", "P6-L1" in inds, False)

    print("\nFigures survive the round trip")
    rows = M.load_rows()
    p6 = [r for r in rows if r["category"] == "BRSR Section C: Principle 6"]
    by_code = {}
    for r in p6:
        t = next((f for f in r.get("frameworks", []) if f["name"] == "BRSR"), None)
        if t:
            by_code[t["detail"].split(" · ")[0].strip()] = r

    fixture_html = open(os.path.join(HERE, "fixtures", "test-brsr.html"),
                        encoding="utf8").read()
    flat = fixture_html.replace(",", "")

    total = matched = 0
    missing = []
    for code, row in sorted(by_code.items()):
        for year, value in key_figures(row["highlights"]):
            # Only score figures the fixture actually put into the PDF.
            printed = ("%g" % value) in flat or ("%.2f" % value) in flat
            if not printed:
                continue
            total += 1
            if (year, round(value, 6)) in got.get(code, set()):
                matched += 1
            else:
                missing.append((code, year, value))
    check("figures present in the PDF", total > 50, True)
    check("recovered exactly", matched, total)
    if missing:
        for c, y, v in missing[:15]:
            print("       missed %s %s %s" % (c, y, v))

    print("\nValues are not altered")
    e3 = inds.get("P6-E3", {})
    water = {(f["measure"], f["year"]): f for f in e3.get("figures", [])}
    gw = next((f for (m, y), f in water.items()
               if "ground water" in m.lower() and y == "2026"), None)
    check("ground water 2026 value", gw and gw["value"], 494545.39)
    check("printed form kept as published", gw and gw["raw"], "4,94,545.39")
    check("unit kept as published", gw and gw["unit"], "KL")
    check("page number recorded", bool(gw and gw["page"]), True)

    print("\nProvenance and safety")
    check("every figure carries a page", all(
        f.get("page") for i in inds.values() for f in i["figures"]), True)
    check("nothing pre-approved", {i["status"] for i in inds.values()}, {"extracted"})

    print()
    if fails:
        print("FAILURES:")
        for f in fails:
            print("  - " + f)
        return 1
    print("ALL CHECKS PASSED  (%d/%d figures recovered exactly)" % (matched, total))
    return 0


if __name__ == "__main__":
    sys.exit(main())
