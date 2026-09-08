"""
Assemble brsr-app.html — the single-file report-to-profile app.

    python3 tools/build_app.py

Takes app-src/brsr-app.template.html and inlines:

  - pdf.js (reading a PDF in a browser cannot be done without it)
  - the shipped viewer's styles.css and app.js, so a generated profile is
    the same page the demo uses rather than a lookalike
  - the GRI and IFC mapping tables from tools/brsr_indicators.py

Everything is embedded, so the result opens by double-clicking, works
offline, and makes no network request. The shipped viewer itself keeps
its zero dependencies — pdf.js only ever reaches this separate app.

pdf.js is vendored under vendor/. Fetch it once with:

    npm pack pdfjs-dist@3.11.174
    tar xzf pdfjs-dist-3.11.174.tgz
    mkdir -p vendor && cp package/legacy/build/pdf.min.js \\
        package/legacy/build/pdf.worker.min.js vendor/
"""
import base64
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)

from brsr_indicators import GRI_BY_INDICATOR, IFC_BY_GRI_SERIES

TEMPLATE = os.path.join(ROOT, "app-src", "brsr-app.template.html")
OUT = os.path.join(ROOT, "brsr-app.html")
VENDOR = os.path.join(ROOT, "vendor")

IFC_NAMES = {
    "PS1": "Assessment and Management of E&S Risks",
    "PS2": "Labor and Working Conditions",
    "PS3": "Resource Efficiency and Pollution Prevention",
    "PS4": "Community Health, Safety and Security",
    "PS5": "Land Acquisition and Involuntary Resettlement",
    "PS6": "Biodiversity Conservation",
    "PS7": "Indigenous Peoples",
    "PS8": "Cultural Heritage",
}


def b64(path):
    with open(path, "rb") as fh:
        return base64.b64encode(fh.read()).decode("ascii")


def b64_text(text):
    return base64.b64encode(text.encode("utf-8")).decode("ascii")


def profile_body():
    """The <body> of index.html, so a generated profile is the real page."""
    html = open(os.path.join(ROOT, "index.html"), encoding="utf-8").read()
    m = re.search(r"<body[^>]*>(.*)</body>", html, re.S | re.I)
    if not m:
        sys.exit("ERROR: could not find <body> in index.html")
    body = m.group(1)
    # The viewer loads its data and code with <script src=...>; the generated
    # page inlines both instead, so those tags are dropped.
    body = re.sub(r"<script[^>]*\bsrc=[^>]*>\s*</script>", "", body, flags=re.I)
    return body.strip()


def main():
    missing = [n for n in ("pdf.min.js", "pdf.worker.min.js")
               if not os.path.exists(os.path.join(VENDOR, n))]
    if missing:
        sys.exit("ERROR: vendor/%s not found.\n%s"
                 % (", ".join(missing), __doc__.split("pdf.js is vendored")[1]))

    template = open(TEMPLATE, encoding="utf-8").read()

    ifc_map = {k: (v if isinstance(v, list) else [v])
               for k, v in IFC_BY_GRI_SERIES.items()}

    subs = {
        "__PDFJS_LIB__": b64(os.path.join(VENDOR, "pdf.min.js")),
        "__PDFJS_WORKER__": b64(os.path.join(VENDOR, "pdf.worker.min.js")),
        "__PROFILE_CSS__": b64_text(
            open(os.path.join(ROOT, "styles.css"), encoding="utf-8").read()),
        "__PROFILE_JS__": b64_text(
            open(os.path.join(ROOT, "app.js"), encoding="utf-8").read()),
        "__GRI_MAP__": json.dumps(GRI_BY_INDICATOR, ensure_ascii=False),
        "__IFC_MAP__": json.dumps(ifc_map, ensure_ascii=False),
        "__IFC_NAMES__": json.dumps(IFC_NAMES, ensure_ascii=False),
        "__PROFILE_BODY__": json.dumps(profile_body(), ensure_ascii=False),
    }

    out = template
    for key, value in subs.items():
        if key not in out:
            sys.exit("ERROR: placeholder %s missing from the template" % key)
        out = out.replace(key, value)

    left = re.findall(r"__[A-Z_]+__", out)
    if left:
        sys.exit("ERROR: unfilled placeholders: %s" % ", ".join(sorted(set(left))))

    with open(OUT, "w", encoding="utf-8") as fh:
        fh.write(out)

    print("Wrote %s  (%.1f MB)" % (OUT, os.path.getsize(OUT) / 1048576.0))
    print("Open it by double-clicking. It works offline and uploads nothing.")


if __name__ == "__main__":
    main()
