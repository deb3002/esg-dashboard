#!/usr/bin/env python3
"""
Converts ESGReport.xls into data/disclosures.js for the ESG Dashboard page.

Run it whenever a new export replaces ESGReport.xls:

    python3 tools/convert.py

This is a one-off developer tool. It runs once on your computer, never in the
browser, and nothing it needs (xlrd, this script) ships with the actual page.

ANONYMIZE controls whether the real company name, the real board member names,
and the real document links are scrubbed from the output before it's written.
The owner decided (10 Aug 2026) to keep the demo anonymized. If that decision
changes later, set ANONYMIZE = False below and re-run -- but re-confirm with
the owner first, since this is a reputational call, not a technical one.
"""

import json
import re
import sys
from pathlib import Path

import xlrd

ANONYMIZE = True

SOURCE_FILE = Path(__file__).parent.parent / "ESGReport.xls"
OUTPUT_FILE = Path(__file__).parent.parent / "data" / "disclosures.js"

ANON_COMPANY_NAME = "Demo Manufacturing Limited"
UPDATED_DATE = "17 Jul 2026"  # the source file carries no date field; this matches the reference page

# Category (as it appears in column A, after stripping whitespace) -> theme.
# Every one of the 28 real categories must appear here. A category that shows
# up in the file but not in this map is a hard error, not a silent skip.
CATEGORY_TO_THEME = {
    "Management Approach": "Overview & Approach",
    "Company Overview": "Overview & Approach",
    "Corporate Information": "Overview & Approach",
    "Board of Directors": "Governance",
    "Governance": "Governance",
    "Resilience": "Governance",
    "Environment": "Environment",
    "Social": "Social",
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

THEMES_IN_ORDER = [
    "Overview & Approach",
    "Environment",
    "Social",
    "Governance",
    "BRSR Disclosures",
    "Assurance & Recognition",
]

EXPECTED_THEME_TOTALS = {
    "Overview & Approach": 37,
    "Environment": 82,
    "Social": 135,
    "Governance": 139,
    "BRSR Disclosures": 149,
    "Assurance & Recognition": 121,
}

HEADER_ROW_IDX = 5      # row 6, 0-indexed
FIRST_DATA_ROW_IDX = 6  # row 7, 0-indexed
LAST_DATA_ROW_IDX = 668  # row 669, 0-indexed, inclusive

COL_CATEGORY = 0
COL_SUBFACTOR = 2
COL_KEYWORDS = 3
LINK_COLS = [4, 5, 6, 7, 8, 9]  # Link1..Link6
METRIC_PAIR_COLS = [(10, 11), (12, 13), (14, 15), (16, 17), (18, 19), (20, 21)]
COL_HIGHLIGHTS = 22

# Real board member names -> a role-based, non-identifying replacement.
# Built from the file's own "Board of Directors" rows (16 people). Each entry
# includes the honorific + full-name form as it actually appears in the
# narrative text, plus known abbreviated/alternate-spelling forms spotted by
# inspection (e.g. "R. C. Bhargava", "Reema Nanavaty").
NAME_REPLACEMENTS = [
    (r"Mr\.?\s+Nikhil Nanda", "the Chairman & Managing Director"),
    (r"\bNikhil Nanda\b", "the Chairman & Managing Director"),
    (r"Mr\.?\s+Akira Kato", "the Deputy Managing Director"),
    (r"\bAkira Kato\b", "the Deputy Managing Director"),
    (r"Mr\.?\s+Bharat Madan", "the Chief Financial Officer"),
    (r"\bBharat Madan\b", "the Chief Financial Officer"),
    (r"Mr\.?\s+Hardeep Singh", "a Non-Executive Director"),
    (r"\bHardeep Singh\b", "a Non-Executive Director"),
    (r"Ms\.?\s+Nitasha Nanda", "a Whole-time Director"),
    (r"\bNitasha Nanda\b", "a Whole-time Director"),
    (r"Mr\.?\s+Sunil Kant Munjal", "an Independent Director"),
    (r"\bSunil Kant Munjal\b", "an Independent Director"),
    (r"Ms\.?\s+Tanya Arvind Dubash", "an Independent Director"),
    (r"Ms\.?\s+Tanya Dubash", "an Independent Director"),
    (r"\bTanya Arvind Dubash\b", "an Independent Director"),
    (r"\bTanya Dubash\b", "an Independent Director"),
    (r"Mr\.?\s+Harish N\.? Salve", "an Independent Director"),
    (r"\bHarish N\.? Salve\b", "an Independent Director"),
    (r"Mr\.?\s+R\.?\s?C\.?\s+Bhargava", "an Independent Director"),
    (r"Mr\.?\s+Ravindra Chandra Bhargava", "an Independent Director"),
    (r"\bRavindra Chandra Bhargava\b", "an Independent Director"),
    (r"Mr\.?\s+Nobushige Ichikawa", "a Non-Executive Director"),
    (r"\bNobushige Ichikawa\b", "a Non-Executive Director"),
    (r"Mr\.?\s+Kinji Saito", "an Independent Director"),
    (r"\bKinji Saito\b", "an Independent Director"),
    (r"Mr\.?\s+Vimal Bhandari", "an Independent Director"),
    (r"\bVimal Bhandari\b", "an Independent Director"),
    (r"Ms\.?\s+Reema Nanavat[yi]", "an Independent Director"),
    (r"\bReema Rameshchandra Nanavati\b", "an Independent Director"),
    (r"Mr\.?\s+Hitoshi Sasaki", "a Non-Executive Director"),
    (r"\bHitoshi Sasaki\b", "a Non-Executive Director"),
    (r"Mr\.?\s+Satoshi Suzuki", "a Non-Executive Director"),
    (r"\bSatoshi Suzuki\b", "a Non-Executive Director"),
    (r"Dr\.?\s+Rupinder Singh Sodhi", "an Independent Director"),
    (r"\bRupinder Singh Sodhi\b", "an Independent Director"),
    # Ambiguous lone-surname mentions, disambiguated by honorific gender/title.
    (r"Mr\.?\s+Nanda\b", "the Chairman & Managing Director"),
    (r"Ms\.?\s+Nanda\b", "a Whole-time Director"),
    (r"Mr\.?\s+Singh\b", "a Non-Executive Director"),
    (r"Mr\.?\s+Munjal\b", "an Independent Director"),
    (r"Ms\.?\s+Dubash\b", "an Independent Director"),
    (r"Mr\.?\s+Salve\b", "an Independent Director"),
    (r"Mr\.?\s+Bhargava\b", "an Independent Director"),
    (r"Mr\.?\s+Bhandari\b", "an Independent Director"),
    (r"Ms\.?\s+Nanavat[yi]\b", "an Independent Director"),
    (r"Mr\.?\s+Sasaki\b", "a Non-Executive Director"),
    (r"Mr\.?\s+Suzuki\b", "a Non-Executive Director"),
    (r"Mr\.?\s+Sodhi\b", "an Independent Director"),
    (r"Dr\.?\s+Sodhi\b", "an Independent Director"),
    (r"Mr\.?\s+Kato\b", "the Deputy Managing Director"),
    (r"Mr\.?\s+Madan\b", "the Chief Financial Officer"),
    # Real outside organisations named in board-member bios, which would
    # otherwise stay as identifying breadcrumbs even after the person's own
    # name is removed.
    (r"Suzuki Motor Corporation", "a global automotive manufacturer"),
    (r"\bSuzuki\b", "the manufacturer"),
    (r"BML Munjal University \(BMU\)", "a private university"),
    (r"BML Munjal University", "a private university"),
    (r"Vishwanath Singh & Associates", "an accounting firm"),
]

COMPANY_REPLACEMENTS = [
    (r"Escorts Kubota Limited", ANON_COMPANY_NAME),
    (r"Escorts Kubota", "Demo Manufacturing"),
    (r"\bEKL\b", "DML"),
    (r"\bKubota\b", "Demo Manufacturing"),
    (r"\bEscorts\b", "Demo Manufacturing"),
    # Real domain names and URL fragments written out as plain text in the
    # narrative (not hyperlinks -- those are handled separately by nulling
    # every document url). "escortskubota.com" and "escortsgroup" are run
    # together with no word boundary, so the word-bounded rules above never
    # touch them.
    (r"static\.escortskubota\.com", "static.demomanufacturing.example"),
    (r"www\.escortskubota\.com", "www.demomanufacturing.example"),
    (r"escortskubota\.com", "demomanufacturing.example"),
    (r"escortsgroup", "demogroup"),
]

ALL_TEXT_REPLACEMENTS = [(re.compile(p, re.IGNORECASE), r) for p, r in NAME_REPLACEMENTS + COMPANY_REPLACEMENTS]

# A name replacement often leaves behind the person's own title in
# parentheses right after it (e.g. "Nikhil Nanda (Chairman & Managing
# Director)" becomes "the Chairman & Managing Director (Chairman & Managing
# Director)"). Strip a trailing parenthetical that immediately follows one
# of these role phrases, regardless of the source file's exact wording
# inside the parentheses.
ROLE_PHRASES = [
    "the Chairman & Managing Director",
    "the Deputy Managing Director",
    "the Chief Financial Officer",
    "a Non-Executive Director",
    "a Whole-time Director",
    "an Independent Director",
]
ROLE_PAREN_CLEANUP = [
    (re.compile(re.escape(role) + r"\s*\([^)]*\)"), role) for role in ROLE_PHRASES
]

# Checked as a whole-word match -- these are common enough as substrings
# (e.g. "Kato" inside some unrelated word) that substring matching would
# over-report.
RESIDUAL_CHECK_TERMS_WORD_BOUNDED = [
    "Escorts", "Kubota", "EKL",
    "Nanda", "Singh", "Munjal", "Dubash", "Salve", "Bhargava", "Ichikawa",
    "Saito", "Bhandari", "Nanavati", "Nanavaty", "Sasaki", "Kato", "Suzuki",
    "Sodhi", "Madan",
]

# Checked as a plain substring, no word boundary -- catches the company name
# run together inside a domain name or URL path (e.g. "escortskubota.com",
# "escortsgroup_home"), which a \b-bounded check on "Escorts"/"Kubota" alone
# would silently miss.
RESIDUAL_CHECK_TERMS_SUBSTRING = [
    "escortskubota", "escortsgroup",
]


def anonymize_text(text):
    if not ANONYMIZE or not text:
        return text
    for pattern, replacement in ALL_TEXT_REPLACEMENTS:
        text = pattern.sub(replacement, text)
    for pattern, role in ROLE_PAREN_CLEANUP:
        text = pattern.sub(role, text)
    return text


def clean_str(value):
    return str(value).strip() if value != "" else ""


def parse_documents(sheet, row_idx):
    documents = []
    real_url_count = 0
    for col in LINK_COLS:
        label = clean_str(sheet.cell_value(row_idx, col))
        if not label:
            continue
        link = sheet.hyperlink_map.get((row_idx, col))
        url = None
        if link is not None and link.url_or_path:
            candidate = link.url_or_path
            if candidate.startswith("http://") or candidate.startswith("https://"):
                url = candidate
                real_url_count += 1
        if ANONYMIZE:
            url = None
        documents.append({"label": anonymize_text(label), "url": url})
    return documents, real_url_count


def parse_metrics(sheet, row_idx):
    metrics = []
    for value_col, label_col in METRIC_PAIR_COLS:
        raw_value = sheet.cell_value(row_idx, value_col)
        raw_label = sheet.cell_value(row_idx, label_col)
        has_value = raw_value != ""
        has_label = clean_str(raw_label) != ""
        if not has_value and not has_label:
            continue
        if has_value != has_label:
            raise ValueError(
                f"Row {row_idx + 1}: metric value/label mismatch "
                f"(value={raw_value!r}, label={raw_label!r})"
            )
        metrics.append({"value": raw_value, "label": anonymize_text(clean_str(raw_label))})
    return metrics


def main():
    if not SOURCE_FILE.exists():
        print(f"ERROR: source file not found at {SOURCE_FILE}")
        sys.exit(1)

    book = xlrd.open_workbook(str(SOURCE_FILE), formatting_info=False)
    sheet = book.sheet_by_index(0)

    rows = []
    theme_counts = {}
    total_real_urls = 0
    metric_row_count = 0
    keyword_set = set()
    unmapped_categories = set()

    for row_idx in range(FIRST_DATA_ROW_IDX, LAST_DATA_ROW_IDX + 1):
        category = clean_str(sheet.cell_value(row_idx, COL_CATEGORY))
        subfactor = clean_str(sheet.cell_value(row_idx, COL_SUBFACTOR))
        highlights = clean_str(sheet.cell_value(row_idx, COL_HIGHLIGHTS))

        if not category or not subfactor or not highlights:
            print(f"ERROR: row {row_idx + 1} missing category/subfactor/highlights")
            sys.exit(1)

        theme = CATEGORY_TO_THEME.get(category)
        if theme is None:
            unmapped_categories.add(category)
            continue

        keywords_raw = clean_str(sheet.cell_value(row_idx, COL_KEYWORDS))
        keywords = [k.strip() for k in keywords_raw.split(",") if k.strip()] if keywords_raw else []
        keyword_set.update(keywords)

        documents, real_url_count = parse_documents(sheet, row_idx)
        total_real_urls += real_url_count

        metrics = parse_metrics(sheet, row_idx)
        if metrics:
            metric_row_count += 1

        theme_counts[theme] = theme_counts.get(theme, 0) + 1

        rows.append({
            "theme": theme,
            "category": category,
            "subfactor": anonymize_text(subfactor),
            "keywords": [anonymize_text(k) for k in keywords],
            "documents": documents,
            "metrics": metrics,
            "highlights": anonymize_text(highlights),
        })

    if unmapped_categories:
        print("ERROR: these categories have no theme mapping and were not converted:")
        for c in sorted(unmapped_categories):
            print(f"  - {c!r}")
        sys.exit(1)

    # ---- Verification checks ----
    print("=== Conversion verification ===")
    ok = True

    check = len(rows) == 663
    print(f"[{'OK' if check else 'FAIL'}] Row count: {len(rows)} (expected 663)")
    ok &= check

    check = all(r["subfactor"] and r["category"] and r["theme"] and r["highlights"] for r in rows)
    print(f"[{'OK' if check else 'FAIL'}] Every row has non-empty subfactor/category/theme/highlights")
    ok &= check

    check = not unmapped_categories
    print(f"[{'OK' if check else 'FAIL'}] Every category maps to a theme")
    ok &= check

    check = theme_counts == EXPECTED_THEME_TOTALS
    print(f"[{'OK' if check else 'FAIL'}] Theme totals match expected:")
    for t in THEMES_IN_ORDER:
        got = theme_counts.get(t, 0)
        exp = EXPECTED_THEME_TOTALS[t]
        flag = "OK" if got == exp else "FAIL"
        print(f"    [{flag}] {t}: {got} (expected {exp})")
    ok &= check

    check = total_real_urls == 912
    print(f"[{'OK' if check else 'FAIL'}] Real hyperlinks parsed from the source file: {total_real_urls} (expected 912)")
    if ANONYMIZE:
        print("    (these are set to null in the output below, per the anonymization decision)")
    ok &= check

    check = metric_row_count == 96
    print(f"[{'OK' if check else 'FAIL'}] Rows with at least one metric: {metric_row_count} (expected 96)")
    ok &= check

    check = len(keyword_set) == 84
    print(f"[{'OK' if check else 'FAIL'}] Distinct keywords: {len(keyword_set)} (expected 84)")
    ok &= check

    if not ok:
        print("\nOne or more checks failed. Not writing the data file.")
        sys.exit(1)

    # ---- Anonymization residual check ----
    if ANONYMIZE:
        full_text = json.dumps(rows)
        print("\n=== Anonymization residual check ===")
        residual_found = False
        for term in RESIDUAL_CHECK_TERMS_WORD_BOUNDED:
            n = len(re.findall(r"\b" + re.escape(term) + r"\b", full_text, re.IGNORECASE))
            if n:
                residual_found = True
                print(f"  [REMAINING] {term!r}: {n} whole-word mention(s) still present")
        for term in RESIDUAL_CHECK_TERMS_SUBSTRING:
            n = len(re.findall(re.escape(term), full_text, re.IGNORECASE))
            if n:
                residual_found = True
                print(f"  [REMAINING] {term!r}: {n} substring occurrence(s) still present")

        if residual_found:
            print("\nResidual real-identity mentions found. Not writing the data file.")
            print("Add a pattern to NAME_REPLACEMENTS or COMPANY_REPLACEMENTS in this script to close the gap.")
            sys.exit(1)
        else:
            print("  No residual mentions of the real company name or director names found.")
            print("  (This is a mechanical text scrub, not a formal guarantee -- see README.md for its limits.)")

    output = {
        "company": ANON_COMPANY_NAME if ANONYMIZE else clean_str(sheet.cell_value(2, 1)),
        "updated": UPDATED_DATE,
        "themes": THEMES_IN_ORDER,
        "rows": rows,
    }

    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        f.write("// Generated by tools/convert.py from ESGReport.xls. Do not hand-edit -- see README.md.\n")
        f.write("window.ESG_DATA = ")
        json.dump(output, f, ensure_ascii=False, indent=2)
        f.write(";\n")

    print(f"\nWrote {OUTPUT_FILE} ({len(rows)} rows).")


if __name__ == "__main__":
    main()
