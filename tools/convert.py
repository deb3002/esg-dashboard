#!/usr/bin/env python3
"""
Convert ESGReport.xls into data/disclosures.js for the ESG profile viewer.

Run this once whenever a new export arrives. It is a developer tool: it runs on
your machine, never in the browser. Nothing it needs ends up in the shipped page.

    python3 tools/convert.py                 # anonymised (default)
    python3 tools/convert.py --real          # real company name, links and people
    python3 tools/convert.py --input FILE --output FILE

Requires: openpyxl, and LibreOffice if the input is a legacy .xls.
See README.md for the plain-language version of all this.
"""

import argparse
import collections
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from brsr_indicators import (INDICATOR_CODES, GRI_BY_INDICATOR, SEBI_SOURCE,
                             IFC_BY_GRI_SERIES, IFC_SOURCE, IFC_NAMES)

# --------------------------------------------------------------------------
# CONFIGURATION — this is the part you may want to change
# --------------------------------------------------------------------------

# Which of the 28 source categories rolls up into which theme.
# Every category in the file must appear here or the conversion stops.
THEME_MAP = {
    "Management Approach": "Overview & Approach",
    "Company Overview": "Overview & Approach",
    "Corporate Information": "Overview & Approach",

    "Environment": "Environment",

    "Social": "Social",

    "Board of Directors": "Governance",
    "Governance": "Governance",
    "Resilience": "Governance",

    "Materiality Assessment": "Assurance & Recognition",
    "Awards and Recognitions": "Assurance & Recognition",
    "Verification and Assurances": "Assurance & Recognition",
    "Ratings and Indices": "Assurance & Recognition",
    "ISO and Certifications": "Assurance & Recognition",
    "Memberships": "Assurance & Recognition",
    "Partnerships": "Assurance & Recognition",
    "ESG Videos and News": "Assurance & Recognition",
    "Profile Sources": "Assurance & Recognition",

    "BRSR Section A: General Disclosures": "BRSR Disclosures",
    "BRSR Section B: Management And Process Disclosures": "BRSR Disclosures",
    "BRSR Section C: Principle 1": "BRSR Disclosures",
    "BRSR Section C: Principle 2": "BRSR Disclosures",
    "BRSR Section C: Principle 3": "BRSR Disclosures",
    "BRSR Section C: Principle 4": "BRSR Disclosures",
    "BRSR Section C: Principle 5": "BRSR Disclosures",
    "BRSR Section C: Principle 6": "BRSR Disclosures",
    "BRSR Section C: Principle 7": "BRSR Disclosures",
    "BRSR Section C: Principle 8": "BRSR Disclosures",
    "BRSR Section C: Principle 9": "BRSR Disclosures",
}

THEME_ORDER = [
    "Overview & Approach",
    "Environment",
    "Social",
    "Governance",
    "BRSR Disclosures",
    "Assurance & Recognition",
]

# Expected totals, measured from the August 2026 export. The conversion reports
# any drift rather than silently shipping different data.
EXPECTED = {
    "rows": 663,
    "themes": {
        "Overview & Approach": 37,
        "Environment": 82,
        "Social": 135,
        "Governance": 139,
        "BRSR Disclosures": 149,
        "Assurance & Recognition": 121,
    },
    "links_with_url": 912,
    "rows_with_metrics": 96,
    "distinct_keywords": 84,
}

ANON_COMPANY = "Demo Manufacturing Limited"
REAL_COMPANY = "Escorts Kubota Limited"
UPDATED = "17 Jul 2026"

# Longest first — "Escorts Kubota Limited" must be replaced before "Escorts".
COMPANY_TOKENS = [
    "Escorts Kubota Limited",
    "Escorts Kubota Ltd.",
    "Escorts Kubota Ltd",
    "Escorts Kubota",
    "Kubota Corporation",
    "Escorts Limited",
    "Escorts Group",
    "Escorts Ltd.",
    "Escorts Ltd",
    "Escorts",
    "Escort",          # the source text uses the singular in places
    "escortsgroup",
    "escortskubota",
    "Kubota",
    "EKL",
]
ANON_COMPANY_SHORT = "DML"

# Other organisations named in director biographies and partnership rows.
# These are a re-identification route: a reader can look up who sits on these
# boards. Extend this list as the residual review below surfaces more.
THIRD_PARTY_ORGS = [
    "Godrej Industries Limited",
    "Godrej Consumer Products Limited",
    "Godrej Agrovet Limited",
    "Godrej Industries",
    "Godrej Agrovet",
    "Godrej",
    "Maruti Udyog Limited",
    "Maruti Udyog",
    "Maruti Suzuki",
    "Maruti",
    "Suzuki Motor Corporation",
    "Hero MotoCorp",
    "Hero Motocorp",
    "Serendipity Arts Foundation",
    "Interstellar Testing Centre",
    "Invigorated Business Consulting Limited",
    "Invest Direct India Limited",
    "Watson Institute",
    "International Food Policy Research Institute",
    "Food Policy Research Institute",
    "Self Employed Women's Association",
    "SEWA",
]
ANON_ORG = "Another Listed Company"

# Director biographies list previous employers, universities, other board seats
# and industry bodies. That combination identifies a person in one search, and
# no keyword list can reliably catch all of it. In anonymised builds the
# biography text for these categories is replaced wholesale rather than filtered.
REDACT_BIO_CATEGORIES = {"Board of Directors"}
REDACTED_BIO = ("Biography withheld in this demonstration build. In a live "
                "profile this row carries the director's role, tenure, "
                "committee memberships and background.")

# Sector and site references that identify the company even without its name.
SECTOR_LITERALS = {
    "Advanced Farming Institute": "Advanced Research Institute",
    "Tractor Division": "Primary Products Division",
    "Groundcare Equipment Division": "Secondary Products Division",
    "tractor manufacturing": "equipment manufacturing",
    "tractors and": "equipment and",
    "Tractors and": "Equipment and",
}

# Board members and named executives. Order matters only for stable lettering.
PEOPLE = [
    "Nikhil Nanda",
    "Nitasha Nanda",
    "Hardeep Singh",
    "Sunil Kant Munjal",
    "Tanya Arvind Dubash",
    "Tanya Dubash",
    "Harish N. Salve",
    "Harish Salve",
    "Ravindra Chandra Bhargava",
    "Nobushige Ichikawa",
    "Kinji Saito",
    "Vimal Bhandari",
    "Reema Rameshchandra Nanavati",
    "Reema Nanavaty",
    "Reema Nanavati",
    "Hitoshi Sasaki",
    "Akira Kato",
    "Satoshi Suzuki",
    "Rupinder Singh Sodhi",
    "Bharat Madan",
    "Seiji Fukuoka",
    "Arvind Kumar",
]

# Surnames that must not survive on their own once full names are replaced.
BARE_SURNAMES = ["Nanda", "Kato", "Madan", "Munjal", "Dubash", "Salve",
                 "Bhargava", "Ichikawa", "Saito", "Bhandari", "Nanavaty",
                 "Nanavati", "Sasaki", "Suzuki", "Sodhi", "Fukuoka"]

# Identifiers and contact details that appear in Corporate Information.
LITERALS = {
    "Railway Equipment Division": "Legacy Equipment Division",
    "Railway Equipment business": "Legacy Equipment business",
    "Agri Machinery Business": "Primary Machinery Business",
    "Construction Equipment Business": "Secondary Equipment Business",
    "L74899HR1944PLC039088": "L00000XX0000XXX000000",
    "15/5, Mathura Road, Faridabad": "Plot 00, Industrial Area, City",
    "15/5 Mathura Road, Faridabad": "Plot 00, Industrial Area, City",
    "Mathura Road, Faridabad": "Industrial Area, City",
    "Faridabad": "City",
    "121003": "000000",
    "1800-103-2010": "1800-000-0000",
    "0129 2250 222": "0000 0000 000",
    "escortskubota.com": "example-manufacturing.com",
    "EscortsKubota": "DemoManufacturing",
    "escortskubotaltd": "demomanufacturing",
    "escortskubotalimited": "demomanufacturing",
}


# --------------------------------------------------------------------------
# REPORTING FRAMEWORKS
# --------------------------------------------------------------------------

# Two kinds of framework tag, and the difference matters on screen.
#
#   VERIFIED   - taken from the source export. BRSR and BRSR Core come from
#                keywords the ESG portal itself applied.
#   PROVISIONAL- derived here by keyword pattern matching. GRI and IFC are
#                not referenced anywhere in the export, so these are guesses.
#                A row mentioning water gets GRI 303 whether or not that is
#                the correct disclosure.
#
# Provisional tags are marked as such in the data and flagged in the page, so
# a keyword guess is never mistaken for a professional mapping. Replace them
# by filling in the mapping worksheet and dropping the reviewed CSV in as
# FRAMEWORK_OVERRIDE_FILE; anything it covers is then treated as verified.

FRAMEWORK_OVERRIDE_FILE = "framework-mapping.csv"

# GRI mapping comes from the published linkage document, not from guesswork:
#
#   "Linking the GRI Standards and the SEBI BRSR Framework" (GRI with BSE, 2022)
#   https://www.globalreporting.org/media/ioqnxtmx/sebi_brsb_gri_linkage_doc.pdf
#
# That document maps BRSR requirements to GRI disclosures at indicator level
# (P6-E3, P9-E2 and so on). This export does not carry indicator numbers — only
# the principle, and whether the row is an Essential or Leadership indicator.
# So the mapping is applied at PRINCIPLE level, which is the finest granularity
# the data actually supports. Each tag names the GRI standards the linkage
# document associates with that BRSR section, and is citable back to it.
#
# Rows outside the BRSR sections get no GRI tag. The linkage document says
# nothing about them, and inventing one would be the guesswork this replaces.

LINKAGE_SOURCE = ("GRI–SEBI BRSR linkage document (GRI with BSE, 2022)")

# Short display codes for the BRSR sections. The export records the principle
# a disclosure sits under, but NOT the BRSR indicator number (P6-E3 and the
# like) — those are not in the source data and are not invented here.
BRSR_CODES = {
    "BRSR Section A: General Disclosures": "Section A",
    "BRSR Section B: Management And Process Disclosures": "Section B",
}


def brsr_code(category):
    if category in BRSR_CODES:
        return BRSR_CODES[category]
    m = re.search(r"Principle (\d+)", category)
    return "Principle " + m.group(1) if m else category


def indicator_type(keywords):
    if "SEBI: Essential Core" in keywords:
        return "Essential (Core)"
    if "SEBI: Essential" in keywords:
        return "Essential"
    if "SEBI: Leadership" in keywords:
        return "Leadership"
    return ""

BRSR_GRI_LINKAGE = {
    "BRSR Section A: General Disclosures":
        ["GRI 2", "GRI 3", "GRI 201", "GRI 401", "GRI 405"],
    "BRSR Section B: Management And Process Disclosures":
        ["GRI 2", "GRI 3"],
    "BRSR Section C: Principle 1":
        ["GRI 2", "GRI 205"],
    "BRSR Section C: Principle 2":
        ["GRI 2", "GRI 3", "GRI 205", "GRI 301", "GRI 306", "GRI 308", "GRI 414"],
    "BRSR Section C: Principle 3":
        ["GRI 2", "GRI 3", "GRI 201", "GRI 401", "GRI 403", "GRI 404",
         "GRI 405", "GRI 414"],
    "BRSR Section C: Principle 4":
        ["GRI 2", "GRI 3"],
    "BRSR Section C: Principle 5":
        ["GRI 2", "GRI 3", "GRI 202", "GRI 205", "GRI 403", "GRI 404",
         "GRI 405", "GRI 406", "GRI 410", "GRI 414"],
    "BRSR Section C: Principle 6":
        ["GRI 2", "GRI 3", "GRI 301", "GRI 302", "GRI 303", "GRI 304",
         "GRI 305", "GRI 306", "GRI 308", "GRI 413"],
    "BRSR Section C: Principle 7":
        ["GRI 2", "GRI 3", "GRI 206", "GRI 415"],
    "BRSR Section C: Principle 8":
        ["GRI 2", "GRI 3", "GRI 201", "GRI 204", "GRI 413"],
    "BRSR Section C: Principle 9":
        ["GRI 2", "GRI 3", "GRI 416", "GRI 417", "GRI 418"],
}

# No equivalent published BRSR-to-IFC linkage exists, so IFC is not tagged.
# Adding it would mean going back to keyword guessing. It returns to the
# filter when the mapping worksheet comes back with reviewed answers.

FRAMEWORK_ORDER = ["BRSR", "BRSR Core", "GRI", "IFC"]
GRI_RULES = []
IFC_RULES = []


def load_overrides(base_dir):
    """Reviewed mappings, if the worksheet has been returned as CSV.

    Expected columns: Sub Factor, GRI, IFC. A value of 'None' means the
    reviewer decided the row maps to nothing.
    """
    path = os.path.join(base_dir, FRAMEWORK_OVERRIDE_FILE)
    if not os.path.exists(path):
        return {}
    import csv
    out = {}
    with open(path, encoding="utf-8-sig", newline="") as fh:
        for rec in csv.DictReader(fh):
            key = (rec.get("Sub Factor") or "").strip()
            if key:
                out[key] = {
                    "GRI": (rec.get("GRI") or "").strip(),
                    "IFC": (rec.get("IFC") or "").strip(),
                }
    return out


def match_rules(rules, text):
    hits = []
    for pattern, label in rules:
        if re.search(pattern, text, re.I) and label not in hits:
            hits.append(label)
    return hits


GRI_SERIES_RE = re.compile(r"\b(\d{1,3})(?:-|\b)")


def ifc_from_gri(gri_text):
    """Chain GRI standards to IFC Performance Standards.

    Weaker than every other mapping here — see the note in brsr_indicators.py.
    """
    series = set()
    for token in GRI_SERIES_RE.findall(gri_text or ""):
        if token in IFC_BY_GRI_SERIES:
            series.add(IFC_BY_GRI_SERIES[token])
    # PS1 is the catch-all management standard; when a row already maps to a
    # topic standard, listing PS1 as well adds noise without adding meaning.
    if len(series) > 1:
        series.discard("PS1")
    return sorted(series)


def build_frameworks(subfactor, category, keywords, overrides):
    frameworks = []

    # Subfactor titles are NOT unique across the file — "Energy Consumption"
    # appears under both Environment and BRSR Principle 6. Indicator codes
    # apply only inside the BRSR sections.
    is_brsr = category.startswith("BRSR")
    # Some titles contain non-breaking spaces, which do not match a normal
    # space and would silently drop the indicator code.
    lookup = re.sub(r"\s+", " ", subfactor.replace("\u00a0", " ")).strip()
    indicator = INDICATOR_CODES.get(lookup) if is_brsr else None

    if "BRSR" in keywords:
        code = brsr_code(category)
        kind = indicator_type(keywords)
        # Show the indicator number where it is known — that is the reference
        # a reader actually wants — and fall back to the principle otherwise.
        label = indicator if indicator else code
        detail = label
        if indicator and indicator != code:
            detail = indicator + " · " + code
        if kind:
            detail += " · " + kind
        frameworks.append({
            "name": "BRSR",
            "detail": detail,
            "indicator": indicator or "",
            "verified": True,
            "source": SEBI_SOURCE,
        })
    if "SEBI: Essential Core" in keywords:
        frameworks.append({"name": "BRSR Core", "detail": "", "verified": True})

    reviewed = overrides.get(subfactor)

    if reviewed is not None:
        for name in ("GRI", "IFC"):
            answer = reviewed.get(name, "")
            if answer and answer.lower() != "none":
                frameworks.append({"name": name, "detail": answer,
                                   "verified": True, "source": "reviewed mapping"})
        return frameworks

    # Indicator-level GRI where the linkage document gives one for this exact
    # indicator; otherwise the principle-level mapping, which is coarser but
    # equally sourced.
    exact = GRI_BY_INDICATOR.get(indicator) if indicator else None
    if exact:
        numbers = exact.replace("GRI ", "")
        frameworks.append({
            "name": "GRI",
            "detail": numbers,
            "full": exact,
            "level": "indicator",
            "verified": True,
            "source": LINKAGE_SOURCE,
        })
        add_ifc(frameworks, exact)
        return frameworks

    linked = BRSR_GRI_LINKAGE.get(category)
    if linked:
        # "GRI 302" -> "302"; the pill already says GRI, so repeating it in
        # every entry just makes the cell unreadable.
        numbers = [x.replace("GRI ", "") for x in linked]
        frameworks.append({
            "name": "GRI",
            "detail": ", ".join(numbers),
            "full": ", ".join(linked),
            "level": "principle",
            "verified": True,
            "source": LINKAGE_SOURCE,
        })
        # No IFC here. Principle-level GRI is the union of every standard
        # linked to that whole BRSR section, so chaining it to IFC gives
        # nonsense — Section A's union includes GRI 401 and 405, which put
        # "CIN" and "Paid-up Capital" under Labour and Working Conditions.
        # IFC is derived only where the GRI answer is indicator-precise.

    return frameworks


def add_ifc(frameworks, gri_text):
    standards = ifc_from_gri(gri_text)
    if not standards:
        return
    frameworks.append({
        "name": "IFC",
        "detail": ", ".join(standards) + " · by GRI alignment",
        "full": ", ".join(standards),
        "level": "alignment",
        "verified": False,
        "source": IFC_SOURCE,
    })


# --------------------------------------------------------------------------
# TREND SERIES
# --------------------------------------------------------------------------

# A metric label carries the measure, the year and the unit, e.g.
# "GHG Emission 2026 (tCO2e)". Splitting those apart turns six loose values
# into a series that can be charted.

# Any year-on-year change of this ratio or more is treated as suspicious. A
# jump that large is usually a change in what was counted, not a change in
# what happened, and charting it as a trend tells a false story.
DISCONTINUITY_RATIO = 3.0

# Captions for series where the cause of a jump has been established. Keyed by
# (subfactor, measure). Anything flagged but not listed here gets the generic
# caption, and should be investigated and moved into this table.
SERIES_NOTES = {
    ("Amount of GHG Emissions", "GHG Emission"):
        "2024 excludes Scope 3, first disclosed in 2025. The three years are "
        "not directly comparable.",
}

GENERIC_NOTE = ("Reporting basis may differ between years — verify before "
                "reading this as a trend.")

YEAR_RE = re.compile(r"\b(20\d\d)\b")
UNIT_RE = re.compile(r"\(([^)]*)\)\s*$")


def split_label(label):
    """'GHG Emission 2026 (tCO2e)' -> ('GHG Emission', '2026', 'tCO2e')"""
    year_match = YEAR_RE.search(label)
    if not year_match:
        return None, None, None
    year = year_match.group(1)
    rest = YEAR_RE.sub("", label, count=1)
    unit_match = UNIT_RE.search(rest)
    unit = unit_match.group(1).strip() if unit_match else ""
    measure = UNIT_RE.sub("", rest).replace("  ", " ").strip()
    return measure, year, unit


def build_series(metrics):
    """Group metrics into year-over-year series.

    Returns (series, standalone) where standalone holds every metric that is
    not part of a series of two or more points — single-year values, targets
    and counts, which still render as plain figures.
    """
    grouped = collections.OrderedDict()
    used = set()

    for idx, m in enumerate(metrics):
        measure, year, unit = split_label(m["label"])
        if measure is None or not isinstance(m["value"], (int, float)):
            continue
        grouped.setdefault((measure, unit), []).append((idx, year, m["value"]))

    series = []
    for (measure, unit), points in grouped.items():
        if len(points) < 2:
            continue
        for idx, _, _ in points:
            used.add(idx)
        points.sort(key=lambda p: p[1])          # chronological
        pts = [{"year": y, "value": v} for _, y, v in points]

        flagged, breaks = False, []
        for i in range(1, len(pts)):
            a, b = pts[i - 1]["value"], pts[i]["value"]
            if a > 0 and b > 0 and max(a, b) / min(a, b) >= DISCONTINUITY_RATIO:
                flagged = True
                breaks.append(i)

        entry = {
            "measure": measure,
            "unit": unit,
            "points": pts,
            "flagged": flagged,
        }
        if flagged:
            entry["breaks"] = breaks
            entry["note"] = SERIES_NOTES.get(
                (CURRENT_SUBFACTOR[0], measure), GENERIC_NOTE)
        series.append(entry)

    standalone = [m for i, m in enumerate(metrics) if i not in used]
    return series, standalone


# build_series needs the row's subfactor to look up a caption; passing it
# through every call would clutter the signature for one lookup.
CURRENT_SUBFACTOR = [""]


# --------------------------------------------------------------------------
# LOADING
# --------------------------------------------------------------------------

def load_sheet(path):
    """Return an openpyxl worksheet, converting a legacy .xls first if needed."""
    try:
        import openpyxl
    except ImportError:
        sys.exit("ERROR: openpyxl is not installed.  Run: pip3 install openpyxl")

    if path.lower().endswith(".xls"):
        soffice = shutil.which("soffice") or shutil.which("libreoffice")
        if not soffice:
            sys.exit(
                "ERROR: this is a legacy .xls file and LibreOffice was not found.\n"
                "       Install LibreOffice, or open the file in Excel and save it\n"
                "       as .xlsx, then run:  python3 tools/convert.py --input <that file>"
            )
        tmp = tempfile.mkdtemp(prefix="esgconv-")
        subprocess.run(
            [soffice, "--headless", "--convert-to", "xlsx", "--outdir", tmp, path],
            check=True, capture_output=True, timeout=300,
        )
        converted = os.path.join(
            tmp, os.path.splitext(os.path.basename(path))[0] + ".xlsx")
        if not os.path.exists(converted):
            sys.exit("ERROR: LibreOffice could not convert the .xls file.")
        path = converted

    wb = openpyxl.load_workbook(path)          # keep hyperlinks
    wbv = openpyxl.load_workbook(path, data_only=True)   # cached values
    return wb["Profile"], wbv["Profile"]


# --------------------------------------------------------------------------
# ANONYMISATION
# --------------------------------------------------------------------------

def build_person_map():
    """Map each real name to a stable placeholder: Director A, Director B, ..."""
    canonical, mapping, letter = {}, {}, 0
    for name in PEOPLE:
        # Group name variants by surname so Tanya Dubash and Tanya Arvind
        # Dubash resolve to the same placeholder.
        key = name.split()[-1].rstrip(".")
        if key not in canonical:
            canonical[key] = "Director " + chr(ord("A") + letter)
            letter += 1
        mapping[name] = canonical[key]
    for surname in BARE_SURNAMES:
        if surname in canonical:
            mapping.setdefault(surname, canonical[surname])
    return mapping


PERSON_MAP = build_person_map()


URL_RE = re.compile(r"https?://[^\s,;)\]]+|\bwww\.[^\s,;)\]]+", re.I)

# Underscores and digits count as word characters to Python's \b, so a plain
# \bEKL\b never matches inside "EKL_Anti_Bribery_Policy.pdf". These boundaries
# treat any letter or digit as adjacency but allow underscores and punctuation.
def token_re(token):
    return re.compile(r"(?<![A-Za-z0-9])" + re.escape(token) + r"(?![A-Za-z0-9])",
                      re.IGNORECASE if token.islower() else 0)


def anonymise(text):
    if not text:
        return text
    out = text

    # Whole URLs go first — their paths carry the company name in filenames
    # like /templates/escortsgroup_home/... and EKL_Anti_Bribery_Policy.pdf.
    out = URL_RE.sub("https://www.example-manufacturing.com/", out)

    for literal, repl in LITERALS.items():
        out = out.replace(literal, repl)
    for literal, repl in SECTOR_LITERALS.items():
        out = out.replace(literal, repl)
    for org in sorted(THIRD_PARTY_ORGS, key=len, reverse=True):
        out = token_re(org).sub(ANON_ORG, out)
    for name in sorted(PERSON_MAP, key=len, reverse=True):
        out = token_re(name).sub(PERSON_MAP[name], out)
    for token in sorted(COMPANY_TOKENS, key=len, reverse=True):
        repl = ANON_COMPANY_SHORT if token == "EKL" else ANON_COMPANY
        out = token_re(token).sub(repl, out)

    # Collapse "Another Listed Company, Another Listed Company and Another
    # Listed Company" runs left by replacing several orgs in one sentence.
    out = re.sub(r"(?:Another Listed Company)(?:,?\s+(?:and\s+)?Another Listed Company)+",
                 "Another Listed Company", out)
    return out


def anonymise_url(url):
    """Anonymised builds keep the link label but drop the destination."""
    return None


# --------------------------------------------------------------------------
# PARSING
# --------------------------------------------------------------------------

HEADER_ROW = 6
FIRST_DATA_ROW = 7
COL_CATEGORY, COL_SUBFACTOR, COL_KEYWORDS = 1, 3, 4
LINK_COLS = range(5, 11)
METRIC_COLS = [(11, 12), (13, 14), (15, 16), (17, 18), (19, 20), (21, 22)]
COL_HIGHLIGHTS = 23


def clean(value):
    if value is None:
        return ""
    return str(value).strip()


def parse(ws_links, ws_values, do_anon, overrides=None):
    rows, problems = [], []
    link_url_count = 0
    overrides = overrides or {}

    for r in range(FIRST_DATA_ROW, ws_values.max_row + 1):
        category = clean(ws_values.cell(r, COL_CATEGORY).value)
        if not category:
            continue

        theme = THEME_MAP.get(category)
        if theme is None:
            problems.append("row %d: category not in THEME_MAP: %r" % (r, category))
            continue

        subfactor = clean(ws_values.cell(r, COL_SUBFACTOR).value)
        highlights = clean(ws_values.cell(r, COL_HIGHLIGHTS).value)

        keywords = [k.strip() for k in clean(
            ws_values.cell(r, COL_KEYWORDS).value).split(",") if k.strip()]

        documents = []
        for c in LINK_COLS:
            label = clean(ws_values.cell(r, c).value)
            if not label:
                continue
            link = ws_links.cell(r, c).hyperlink
            url = link.target if link and link.target else None
            if url:
                link_url_count += 1
                if not url.lower().startswith(("http://", "https://")):
                    url = None
            if do_anon:
                url = anonymise_url(url)
                label = anonymise(label)
            documents.append({"label": label, "url": url})

        metrics = []
        for mcol, ucol in METRIC_COLS:
            raw = ws_values.cell(r, mcol).value
            unit = clean(ws_values.cell(r, ucol).value)
            if raw is None or raw == "":
                if unit:
                    problems.append("row %d: unit %r has no value" % (r, unit))
                continue
            if not unit:
                problems.append("row %d: value %r has no unit label" % (r, raw))
                continue
            try:
                value = float(raw)
                if value == int(value):
                    value = int(value)
            except (TypeError, ValueError):
                value = clean(raw)
            metrics.append({"value": value,
                            "label": anonymise(unit) if do_anon else unit})

        if do_anon:
            subfactor = anonymise(subfactor)
            if category in REDACT_BIO_CATEGORIES:
                highlights = REDACTED_BIO
            else:
                highlights = anonymise(highlights)

        CURRENT_SUBFACTOR[0] = subfactor
        series, standalone = build_series(metrics)
        frameworks = build_frameworks(subfactor, category, keywords, overrides)

        rows.append({
            "theme": theme,
            "category": category,
            "subfactor": subfactor,
            "keywords": keywords,
            "documents": documents,
            "metrics": metrics,          # complete list — CSV export uses this
            "frameworks": frameworks,    # BRSR/BRSR Core verified; GRI/IFC provisional
            "series": series,            # multi-year, for charts
            "standalone": standalone,    # single values, rendered as figures
            "highlights": highlights,
        })

    return rows, problems, link_url_count


# --------------------------------------------------------------------------
# VERIFICATION
# --------------------------------------------------------------------------

def verify(rows, problems, link_url_count):
    print()
    print("=" * 68)
    print("CONVERSION CHECKS")
    print("=" * 68)

    ok = True

    def check(n, label, actual, expected):
        nonlocal ok
        good = actual == expected
        ok = ok and good
        print("  %d. %-42s %8s  %s" % (
            n, label, actual,
            "OK" if good else "MISMATCH (expected %s)" % expected))

    check(1, "Total rows", len(rows), EXPECTED["rows"])

    missing = sum(1 for r in rows if not (r["subfactor"] and r["category"]
                                          and r["theme"] and r["highlights"]))
    check(2, "Rows missing a required field", missing, 0)

    unmapped = sum(1 for p in problems if "THEME_MAP" in p)
    check(3, "Categories with no theme", unmapped, 0)

    print("  4. Theme totals")
    counts = collections.Counter(r["theme"] for r in rows)
    for theme in THEME_ORDER:
        exp = EXPECTED["themes"][theme]
        act = counts.get(theme, 0)
        good = act == exp
        ok = ok and good
        print("       %-28s %8d  %s" % (
            theme, act, "OK" if good else "MISMATCH (expected %d)" % exp))

    check(5, "Document links carrying a URL", link_url_count,
          EXPECTED["links_with_url"])

    with_metrics = sum(1 for r in rows if r["metrics"])
    check(6, "Rows with at least one metric", with_metrics,
          EXPECTED["rows_with_metrics"])

    orphans = sum(1 for p in problems if "no unit" in p or "no value" in p)
    check(7, "Orphaned metrics or units", orphans, 0)

    kw = {k for r in rows for k in r["keywords"]}
    check(8, "Distinct keywords", len(kw), EXPECTED["distinct_keywords"])

    # Every metric must be accounted for exactly once: either it belongs to a
    # series or it stands alone. A metric that falls through both would vanish
    # from the page while still appearing in the CSV.
    lost = 0
    for r in rows:
        in_series = sum(len(s["points"]) for s in r["series"])
        if in_series + len(r["standalone"]) != len(r["metrics"]):
            lost += 1
    check(9, "Rows where a figure would not render", lost, 0)

    print("=" * 68)
    if problems:
        print("PROBLEMS REPORTED (%d):" % len(problems))
        for p in problems[:25]:
            print("   -", p)
        if len(problems) > 25:
            print("   ... and %d more" % (len(problems) - 25))
    print("RESULT:", "ALL CHECKS PASSED" if ok else "FAILED — do not ship this data file")
    print("=" * 68)
    print()
    return ok


def framework_report(rows):
    counts = collections.Counter()
    provisional = collections.Counter()
    for r in rows:
        for f in r["frameworks"]:
            counts[f["name"]] += 1
            if not f["verified"]:
                provisional[f["name"]] += 1

    coded = sum(1 for r in rows for f in r["frameworks"]
                if f["name"] == "BRSR" and f.get("indicator"))
    lvl = collections.Counter(f.get("level") for r in rows
                              for f in r["frameworks"] if f["name"] == "GRI")

    print("REPORTING FRAMEWORKS")
    print("-" * 68)
    for name in FRAMEWORK_ORDER:
        n = counts.get(name, 0)
        p = provisional.get(name, 0)
        state = "verified from source" if p == 0 else (
            "%d DERIVED BY ALIGNMENT — chained via GRI, not a published "
            "BRSR-to-IFC mapping" % p)
        print("   %-10s %4d rows   (%s)" % (name, n, state))
    print()
    print("   BRSR rows carrying an indicator number: %d of %d"
          % (coded, counts.get("BRSR", 0)))
    print("   GRI mapped at indicator level: %d   at principle level: %d"
          % (lvl.get("indicator", 0), lvl.get("principle", 0)))
    if sum(provisional.values()):
        print()
        print("   Derived tags render differently on the page from sourced ones.")
        print("   Replace them with reviewed answers via %s"
              % FRAMEWORK_OVERRIDE_FILE)
    print("-" * 68)
    print()


def series_report(rows):
    """Print what will be charted, and every series flagged as discontinuous."""
    total = charted = two_pt = 0
    flagged = []
    for r in rows:
        for s in r["series"]:
            total += 1
            if len(s["points"]) >= 3:
                charted += 1
            else:
                two_pt += 1
            if s["flagged"]:
                flagged.append((r["subfactor"], s))

    print("TREND SERIES")
    print("-" * 68)
    print("   %d series built: %d with 3+ years (charted), %d with 2 years "
          "(shown as change)" % (total, charted, two_pt))
    print()
    print("   DISCONTINUITIES FLAGGED (%d) — a jump of %.0fx or more between"
          % (len(flagged), DISCONTINUITY_RATIO))
    print("   consecutive years, which usually means the reporting basis")
    print("   changed rather than the underlying figure.")
    for subfactor, s in flagged:
        pts = "  ".join("%s=%s" % (p["year"], p["value"]) for p in s["points"])
        print()
        print("       %s — %s" % (subfactor, s["measure"]))
        print("         %s" % pts)
        explained = s["note"] != GENERIC_NOTE
        print("         caption: %s" % ("SPECIFIC" if explained else
                                        "generic — investigate and add to "
                                        "SERIES_NOTES"))
    print("-" * 68)
    print()


GENERIC_ORG_WORDS = {
    "Another Listed Company", "Demo Manufacturing Limited", "The Company",
    "Indian Institute", "Bombay Stock Exchange", "National Stock Exchange",
}


def leak_scan(rows):
    """Report anything identifying that survived anonymisation."""
    patterns = COMPANY_TOKENS + BARE_SURNAMES + THIRD_PARTY_ORGS + [
        "L74899HR1944PLC039088", "Faridabad", "Mathura Road", "1800-103-2010",
        "Railway Equipment", "escortsgroup", "escortskubota",
    ]
    blob = json.dumps(rows)
    found = collections.Counter()
    for p in patterns:
        n = len(token_re(p).findall(blob)) if p.islower() else \
            len(re.findall(r"(?<![A-Za-z0-9])" + re.escape(p) + r"(?![A-Za-z0-9])",
                           blob, flags=re.I))
        if n:
            found[p] = n

    print("ANONYMISATION LEAK SCAN")
    print("-" * 68)
    if found:
        for p, n in found.most_common():
            print("   LEAK  %-34s %d occurrence(s)" % (p, n))
    else:
        print("   Clean: no known company names, people, identifiers, domains")
        print("   or third-party organisations remain.")

    # Automated replacement only catches what it has been told about. Surface
    # the remaining organisation-like proper nouns so a human can review them.
    text = " ".join(r["highlights"] + " " + r["subfactor"] for r in rows)
    residual = collections.Counter(
        m.strip() for m in re.findall(
            r"\b(?:[A-Z][A-Za-z&.'-]+\s){1,4}"
            r"(?:Limited|Ltd|Pvt|Private|Corporation|Corp|Company|Foundation|"
            r"Trust|Institute|Association|Council|Federation|University|"
            r"Award|Awards|Division|Plant|Works|Factory)\b", text)
    )
    residual = {k: v for k, v in residual.items()
                if not any(g in k for g in GENERIC_ORG_WORDS)}

    print()
    print("   RESIDUAL PROPER NOUNS FOR HUMAN REVIEW (%d distinct)" % len(residual))
    print("   These were not replaced because the converter was never told")
    print("   about them. Check each one; add anything identifying to")
    print("   THIRD_PARTY_ORGS or LITERALS at the top of this file.")
    for k, v in sorted(residual.items(), key=lambda x: -x[1])[:30]:
        print("       %3d  %s" % (v, k))
    print("-" * 68)
    print()
    return not found


# --------------------------------------------------------------------------
# OUTPUT
# --------------------------------------------------------------------------

def emit(rows, path, company, anonymised):
    payload = {
        "company": company,
        "updated": UPDATED,
        "anonymised": anonymised,
        "themes": THEME_ORDER,
        "ifcNames": IFC_NAMES,
        "rows": rows,
    }
    body = json.dumps(payload, indent=2, ensure_ascii=False)
    header = [
        "// GENERATED FILE — DO NOT EDIT BY HAND.",
        "// Produced by tools/convert.py from ESGReport.xls.",
        "// To change anything here, fix the converter and run it again.",
    ]
    if anonymised:
        header += [
            "//",
            "// This is an ANONYMISED build. Company name, people, links and",
            "// contact details have been replaced. The underlying figures are",
            "// real, so the source company may still be identifiable.",
        ]
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as fh:
        fh.write("\n".join(header) + "\n\n")
        fh.write("window.ESG_DATA = " + body + ";\n")
    print("Wrote %s  (%.1f KB)" % (path, os.path.getsize(path) / 1024.0))


def main():
    here = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--input", default=os.path.join(here, "ESGReport.xls"))
    ap.add_argument("--output", default=os.path.join(here, "data", "disclosures.js"))
    ap.add_argument("--real", action="store_true",
                    help="use the real company name, people and links")
    args = ap.parse_args()

    do_anon = not args.real
    print("Reading %s" % args.input)
    print("Mode:   %s" % ("ANONYMISED" if do_anon else "REAL COMPANY DATA"))

    ws_links, ws_values = load_sheet(args.input)
    overrides = load_overrides(here)
    if overrides:
        print("Using reviewed framework mappings for %d disclosures" % len(overrides))
    rows, problems, link_url_count = parse(ws_links, ws_values, do_anon, overrides)

    passed = verify(rows, problems, link_url_count)

    # Stop before writing. A half-right data file that looks fine on screen is
    # worse than no new file at all: the old one still works, this one might
    # be missing rows nobody would notice until a client did.
    if not passed:
        print("STOPPED. The existing data file has NOT been changed.")
        print("Fix the problems listed above and run this again.")
        sys.exit(1)

    framework_report(rows)
    series_report(rows)

    clean_anon = leak_scan(rows) if do_anon else True
    if do_anon and not clean_anon:
        print("STOPPED. Anonymisation is incomplete — see the leaks above.")
        print("The existing data file has NOT been changed.")
        sys.exit(2)

    emit(rows, args.output,
         ANON_COMPANY if do_anon else REAL_COMPANY, do_anon)


if __name__ == "__main__":
    main()
