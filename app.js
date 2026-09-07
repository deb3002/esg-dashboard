(function () {
  "use strict";

  var data = window.ESG_DATA;
  var ALL_THEMES = "All Themes";
  var ALL_KEYWORDS = "All Keywords";
  var ALL_FRAMEWORKS = "All Frameworks";
  var FRAMEWORK_ORDER = ["BRSR", "BRSR Core", "GRI", "IFC"];
  var SEARCH_DEBOUNCE_MS = 120;

  var themeSelect = document.getElementById("theme-select");
  var keywordSelect = document.getElementById("keyword-select");
  var frameworkSelect = document.getElementById("framework-select");
  var searchInput = document.getElementById("search-input");
  var clearSearchBtn = document.getElementById("clear-search");
  var visibleCountEl = document.getElementById("visible-count");
  var tableBody = document.getElementById("table-body");
  var emptyState = document.getElementById("empty-state");
  var clearFiltersBtn = document.getElementById("clear-filters-btn");
  var companyNameEl = document.getElementById("company-name");
  var updatedLineEl = document.getElementById("updated-line");
  var downloadCsvBtn = document.getElementById("download-csv-btn");
  var printBtn = document.getElementById("print-btn");
  var printSummaryEl = document.getElementById("print-summary");

  var searchDebounceTimer = null;

  function renderHeader() {
    companyNameEl.textContent = data.company;
    updatedLineEl.textContent = "Updated: " + data.updated;
  }

  function populateThemeSelect() {
    data.themes.forEach(function (theme) {
      var opt = document.createElement("option");
      opt.value = theme;
      opt.textContent = theme;
      themeSelect.appendChild(opt);
    });
  }

  function frameworkStats() {
    var counts = {}, provisional = {};
    data.rows.forEach(function (row) {
      (row.frameworks || []).forEach(function (f) {
        counts[f.name] = (counts[f.name] || 0) + 1;
        if (!f.verified) provisional[f.name] = (provisional[f.name] || 0) + 1;
      });
    });
    return { counts: counts, provisional: provisional };
  }

  function populateFrameworkSelect() {
    var stats = frameworkStats();
    FRAMEWORK_ORDER.forEach(function (name) {
      var n = stats.counts[name];
      if (!n) return;
      var opt = document.createElement("option");
      opt.value = name;
      opt.textContent = name + " (" + n + ")";
      frameworkSelect.appendChild(opt);
    });
  }

  function keywordCountsForTheme(theme) {
    var counts = {};
    data.rows.forEach(function (row) {
      if (theme !== ALL_THEMES && row.theme !== theme) return;
      row.keywords.forEach(function (kw) {
        counts[kw] = (counts[kw] || 0) + 1;
      });
    });
    return counts;
  }

  function rebuildKeywordSelect() {
    var currentTheme = themeSelect.value;
    var previousKeyword = keywordSelect.value;
    var counts = keywordCountsForTheme(currentTheme);
    var keywords = Object.keys(counts).sort(function (a, b) {
      return a.localeCompare(b);
    });

    keywordSelect.innerHTML = "";
    var allOpt = document.createElement("option");
    allOpt.value = ALL_KEYWORDS;
    allOpt.textContent = ALL_KEYWORDS;
    keywordSelect.appendChild(allOpt);

    keywords.forEach(function (kw) {
      var opt = document.createElement("option");
      opt.value = kw;
      opt.textContent = kw + " (" + counts[kw] + ")";
      keywordSelect.appendChild(opt);
    });

    if (previousKeyword !== ALL_KEYWORDS && counts.hasOwnProperty(previousKeyword)) {
      keywordSelect.value = previousKeyword;
    } else {
      keywordSelect.value = ALL_KEYWORDS;
    }
  }

  function formatMetricValue(value) {
    var str = String(value);
    var parts = str.split(".");
    var intPart = parts[0].replace(/\B(?=(\d{3})+(?!\d))/g, ",");
    return parts.length > 1 ? intPart + "." + parts[1] : intPart;
  }

  function textNode(tag, className, text) {
    var node = document.createElement(tag);
    if (className) node.className = className;
    if (text !== undefined && text !== null) node.textContent = text;
    return node;
  }

  /* ---------------------------------------------------------------
     Trend charts

     Hand-drawn SVG — no charting library, so the page still opens from
     a double-clicked file with no network.

     Two deliberate choices:
     - Columns, not a line. Three annual disclosures are three separate
       figures; a line implies values in between that were never reported.
     - The baseline is always zero. A truncated axis exaggerates change,
       which is the usual way a chart misleads.
     Exact values are printed under every chart, so nothing on screen is
     only readable by eye.
     --------------------------------------------------------------- */

  var SVG_NS = "http://www.w3.org/2000/svg";
  var BAR_W = 26, BAR_GAP = 12, PLOT_H = 46, LABEL_H = 15;

  function svgEl(name, attrs) {
    var node = document.createElementNS(SVG_NS, name);
    for (var k in attrs) {
      if (Object.prototype.hasOwnProperty.call(attrs, k)) {
        node.setAttribute(k, attrs[k]);
      }
    }
    return node;
  }

  function seriesTitle(series) {
    return series.measure + (series.unit ? " (" + series.unit + ")" : "");
  }

  function buildChart(series) {
    var pts = series.points;
    var n = pts.length;
    var width = BAR_GAP + n * (BAR_W + BAR_GAP);
    var height = PLOT_H + LABEL_H;
    var breaks = series.breaks || [];

    var max = 0;
    pts.forEach(function (p) { if (p.value > max) max = p.value; });

    var svg = svgEl("svg", {
      "class": "series-chart",
      width: width,
      height: height,
      viewBox: "0 0 " + width + " " + height,
      role: "img",
      "aria-label": seriesTitle(series) + ": " +
        pts.map(function (p) { return p.year + " " + p.value; }).join(", ")
    });

    pts.forEach(function (p, i) {
      var x = BAR_GAP + i * (BAR_W + BAR_GAP);
      // Zero and negative values still need something visible, so floor the
      // drawn height at 1px rather than rendering nothing at all.
      var h = max > 0 ? Math.max(1, Math.round((p.value / max) * (PLOT_H - 6))) : 1;
      var preBreak = breaks.length > 0 && i < breaks[0];

      svg.appendChild(svgEl("rect", {
        "class": "bar" + (preBreak ? " bar-prebreak" : ""),
        x: x, y: PLOT_H - h, width: BAR_W, height: h, rx: 1
      }));

      var label = svgEl("text", {
        "class": "bar-year", x: x + BAR_W / 2, y: height - 3,
        "text-anchor": "middle"
      });
      label.textContent = p.year;
      svg.appendChild(label);
    });

    // baseline
    svg.appendChild(svgEl("line", {
      "class": "axis", x1: 0, y1: PLOT_H, x2: width, y2: PLOT_H
    }));

    // a dashed rule where the reporting basis appears to change
    breaks.forEach(function (i) {
      var x = BAR_GAP + i * (BAR_W + BAR_GAP) - BAR_GAP / 2;
      svg.appendChild(svgEl("line", {
        "class": "break-line", x1: x, y1: 0, x2: x, y2: PLOT_H
      }));
    });

    return svg;
  }

  function buildValueList(series) {
    var ul = textNode("ul", "series-values");
    series.points.forEach(function (p) {
      var li = textNode("li", null);
      li.appendChild(textNode("span", "series-year", p.year));
      li.appendChild(textNode("span", "series-value", formatMetricValue(p.value)));
      ul.appendChild(li);
    });
    return ul;
  }

  /* Two points is not a trend. Say what changed instead of drawing it. */
  function buildChangeLine(series) {
    var pts = series.points;
    var latest = pts[pts.length - 1], prior = pts[0];
    var wrap = textNode("p", "series-change");
    wrap.appendChild(textNode("span", "series-value",
      formatMetricValue(latest.value)));
    var direction = latest.value === prior.value ? "unchanged from"
      : (latest.value > prior.value ? "up from" : "down from");
    wrap.appendChild(textNode("span", "series-change-text",
      " in " + latest.year + ", " + direction + " " +
      formatMetricValue(prior.value) + " in " + prior.year));
    return wrap;
  }

  function buildSeriesBlock(series) {
    var box = textNode("div", "series" + (series.flagged ? " series-flagged" : ""));
    box.appendChild(textNode("div", "series-head", seriesTitle(series)));

    if (series.points.length >= 3) {
      box.appendChild(buildChart(series));
      box.appendChild(buildValueList(series));
    } else {
      box.appendChild(buildChangeLine(series));
    }

    if (series.flagged && series.note) {
      var note = textNode("p", "series-note", series.note);
      box.appendChild(note);
    }
    return box;
  }

  function buildFiguresBlock(row) {
    var wrap = textNode("div", "figures");

    (row.series || []).forEach(function (s) {
      wrap.appendChild(buildSeriesBlock(s));
    });

    var loose = row.standalone || (row.series ? [] : row.metrics);
    if (loose && loose.length) {
      wrap.appendChild(buildMetricsBlock(loose));
    }
    return wrap;
  }

  function buildMetricsBlock(metrics) {
    var wrap = document.createElement("div");
    wrap.className = "metrics-block";
    metrics.forEach(function (m) {
      var stat = document.createElement("div");
      stat.className = "metric-stat";

      var value = document.createElement("div");
      value.className = "metric-value";
      value.textContent = formatMetricValue(m.value);

      var label = document.createElement("div");
      label.className = "metric-label";
      label.textContent = m.label;

      stat.appendChild(value);
      stat.appendChild(label);
      wrap.appendChild(stat);
    });
    return wrap;
  }

  function buildRow(row) {
    var tr = document.createElement("tr");
    tr.className = "data-row";

    var subfactorTd = document.createElement("td");
    subfactorTd.className = "subfactor-cell";
    subfactorTd.textContent = row.subfactor;
    tr.appendChild(subfactorTd);

    var keywordsTd = document.createElement("td");
    if (row.frameworks && row.frameworks.length > 0) {
      var fwWrap = document.createElement("div");
      fwWrap.className = "framework-list";
      row.frameworks.forEach(function (f) {
        var item = document.createElement("div");
        item.className = "fw-item";

        var pill = document.createElement("span");
        pill.className = "fw-pill" + (f.verified ? "" : " fw-provisional");
        pill.textContent = f.name;
        item.appendChild(pill);

        // The reference numbers are the point of the tag, so they go on the
        // page next to it. A tooltip is not visible during a demonstration.
        if (f.detail) {
          var detail = document.createElement("span");
          detail.className = "fw-detail";
          detail.textContent = f.detail;
          if (f.source) detail.title = "Source: " + f.source;
          item.appendChild(detail);
        }

        fwWrap.appendChild(item);
      });
      keywordsTd.appendChild(fwWrap);
    }

    // A "BRSR" keyword pill next to a BRSR framework tag is pure noise. The
    // keyword still drives the dropdown, search and export — only the
    // duplicate chip is hidden.
    var shown = (row.frameworks || []).map(function (f) { return f.name; });
    var visibleKeywords = row.keywords.filter(function (kw) {
      return shown.indexOf(kw) === -1;
    });

    if (visibleKeywords.length > 0) {
      var pillWrap = document.createElement("div");
      pillWrap.className = "keyword-pills";
      visibleKeywords.forEach(function (kw) {
        var pill = document.createElement("span");
        pill.className = "pill";
        pill.textContent = kw;
        pillWrap.appendChild(pill);
      });
      keywordsTd.appendChild(pillWrap);
    }
    tr.appendChild(keywordsTd);

    var documentsTd = document.createElement("td");
    if (row.documents.length > 0) {
      var docWrap = document.createElement("div");
      docWrap.className = "doc-links";
      row.documents.forEach(function (doc) {
        if (doc.url) {
          var a = document.createElement("a");
          a.href = doc.url;
          a.className = "doc-link";
          a.textContent = doc.label;
          a.target = "_blank";
          a.rel = "noopener noreferrer";
          docWrap.appendChild(a);
        } else {
          var span = document.createElement("span");
          span.className = "doc-label-only";
          span.textContent = doc.label;
          docWrap.appendChild(span);
        }
      });
      documentsTd.appendChild(docWrap);
    }
    tr.appendChild(documentsTd);

    var highlightsTd = document.createElement("td");

    if (row.metrics.length > 0) {
      highlightsTd.appendChild(buildFiguresBlock(row));
    }

    var highlightsP = document.createElement("p");
    highlightsP.className = "highlights-text";
    highlightsP.textContent = row.highlights;
    highlightsTd.appendChild(highlightsP);

    var toggleBtn = document.createElement("button");
    toggleBtn.type = "button";
    toggleBtn.className = "show-more-btn";
    toggleBtn.textContent = "Show more";
    toggleBtn.hidden = true;
    toggleBtn.addEventListener("click", function () {
      var expanded = highlightsP.classList.toggle("expanded");
      toggleBtn.textContent = expanded ? "Show less" : "Show more";
    });
    highlightsTd.appendChild(toggleBtn);

    tr.appendChild(highlightsTd);

    tr._rowData = row;
    tr._highlightsP = highlightsP;
    tr._toggleBtn = toggleBtn;
    return tr;
  }

  /* ---------------------------------------------------------------
     Group headers

     When a framework is selected the table regroups under that
     framework's own structure — choosing IFC groups by Performance
     Standard, the way IFC itself organises them — rather than leaving
     rows under the source spreadsheet's categories.
     --------------------------------------------------------------- */

  var IFC_ORDER = ["PS1", "PS2", "PS3", "PS4", "PS5", "PS6", "PS7", "PS8"];

  function shortCode(category) {
    var m = /Principle (\d+)/.exec(category);
    if (m) return "P" + m[1];
    m = /Section ([AB])/.exec(category);
    if (m) return m[1];
    return "";
  }

  function buildGroupRow(code, name, count) {
    var tr = document.createElement("tr");
    tr.className = "category-row";
    var th = document.createElement("th");
    th.setAttribute("scope", "colgroup");
    th.setAttribute("colspan", "4");

    var inner = document.createElement("div");
    inner.className = "group-head";

    if (code) {
      var chip = document.createElement("span");
      chip.className = "group-code";
      chip.textContent = code;
      inner.appendChild(chip);
    }

    var label = document.createElement("span");
    label.className = "group-name";
    label.textContent = name;
    inner.appendChild(label);

    var tally = document.createElement("span");
    tally.className = "group-count";
    tally.textContent = count + (count === 1 ? " disclosure" : " disclosures");
    inner.appendChild(tally);

    th.appendChild(inner);
    tr.appendChild(th);
    return tr;
  }

  /* Which heading a row sits under, for the framework currently chosen. */
  function groupKey(row, framework) {
    if (framework === "IFC") {
      var f = (row.frameworks || []).find(function (x) { return x.name === "IFC"; });
      // 9 rows map to more than one Performance Standard; group by the first
      // and leave the full list visible on the row itself.
      return f ? f.full.split(", ")[0] : "PS-none";
    }
    return row.category;
  }

  function groupLabel(key, framework) {
    if (framework === "IFC") {
      if (key === "PS-none") return { code: "", name: "Not mapped to a Performance Standard" };
      var n = (data.ifcNames || {})[key] || "";
      return { code: key.replace("PS", "PS "), name: n };
    }
    return { code: shortCode(key), name: key };
  }

  var allRowElements = [];
  var allCategoryElements = [];

  function buildAllRows() {
    data.rows.forEach(function (row) {
      var tr = buildRow(row);
      allRowElements.push(tr);
    });
  }

  /* Lay the table out for the chosen framework. Row elements are reused —
     only their order and their headings change — so nothing is rebuilt and
     no expand/collapse state is lost. */
  function layoutTable(framework) {
    var order = [];
    var buckets = {};

    allRowElements.forEach(function (tr) {
      var key = groupKey(tr._rowData, framework);
      if (!buckets[key]) { buckets[key] = []; order.push(key); }
      buckets[key].push(tr);
    });

    if (framework === "IFC") {
      order.sort(function (a, b) {
        return IFC_ORDER.indexOf(a) - IFC_ORDER.indexOf(b);
      });
    }

    tableBody.textContent = "";
    allCategoryElements.length = 0;

    var fragment = document.createDocumentFragment();
    order.forEach(function (key) {
      var label = groupLabel(key, framework);
      var header = buildGroupRow(label.code, label.name, buckets[key].length);
      header._categoryName = key;
      allCategoryElements.push(header);
      fragment.appendChild(header);

      buckets[key].forEach(function (tr) {
        tr._categoryName = key;
        fragment.appendChild(tr);
      });
    });
    tableBody.appendChild(fragment);
  }

  function detectClamps() {
    // One-time overflow check: only show "Show more" where the clamped text
    // actually overflows. Reads layout, so the rows must already be attached.
    allRowElements.forEach(function (tr) {
      var p = tr._highlightsP;
      if (p.scrollHeight > p.clientHeight + 1) {
        tr._toggleBtn.hidden = false;
      }
    });
  }

  function hasFramework(row, name) {
    var list = row.frameworks || [];
    for (var i = 0; i < list.length; i++) {
      if (list[i].name === name) return true;
    }
    return false;
  }

  function rowMatches(row, theme, keyword, query, framework) {
    if (theme !== ALL_THEMES && row.theme !== theme) return false;
    if (keyword !== ALL_KEYWORDS && row.keywords.indexOf(keyword) === -1) return false;
    if (framework && framework !== ALL_FRAMEWORKS && !hasFramework(row, framework)) return false;

    if (query === "") return true;

    var haystack = (
      row.subfactor + " " +
      row.category + " " +
      row.keywords.join(" ") + " " +
      row.metrics.map(function (m) { return m.label; }).join(" ") + " " +
      row.highlights
    ).toLowerCase();

    return haystack.indexOf(query) !== -1;
  }

  function applyFilters() {
    var theme = themeSelect.value;
    var keyword = keywordSelect.value;
    var framework = frameworkSelect.value;
    var query = searchInput.value.trim().toLowerCase();

    clearSearchBtn.hidden = searchInput.value.length === 0;

    var visibleCount = 0;
    var categoriesWithVisibleRows = {};

    allRowElements.forEach(function (tr) {
      var isVisible = rowMatches(tr._rowData, theme, keyword, query, framework);
      tr.hidden = !isVisible;

      if (isVisible) {
        visibleCount++;
        categoriesWithVisibleRows[tr._categoryName] = true;

        if (tr._highlightsP.classList.contains("expanded")) {
          tr._highlightsP.classList.remove("expanded");
          tr._toggleBtn.textContent = "Show more";
        }
      }
    });

    allCategoryElements.forEach(function (tr) {
      tr.hidden = !categoriesWithVisibleRows[tr._categoryName];
    });

    var total = data.rows.length;
    visibleCountEl.textContent = "Showing " + visibleCount + " of " + total + " disclosures";

    emptyState.hidden = visibleCount !== 0;
    tableBody.parentElement.hidden = visibleCount === 0;

    printSummaryEl.textContent = [
      data.company,
      "ESG Profile",
      "Updated: " + data.updated,
      theme + " · " + keyword + " · " + framework + " · " + visibleCount + " of " + total + " disclosures"
    ].join(" — ");
  }

  function clearFilters() {
    frameworkSelect.value = ALL_FRAMEWORKS;
    layoutTable(ALL_FRAMEWORKS);
    themeSelect.value = ALL_THEMES;
    rebuildKeywordSelect();
    keywordSelect.value = ALL_KEYWORDS;
    searchInput.value = "";
    applyFilters();
  }

  function slugify(str) {
    return str.toLowerCase().replace(/[^a-z0-9]+/g, "-").replace(/^-+|-+$/g, "");
  }

  function csvEscape(field) {
    var str = String(field == null ? "" : field);
    return '"' + str.replace(/"/g, '""') + '"';
  }

  function buildCsv(rows) {
    var header = ["Theme", "Category", "Sub Factor", "Frameworks", "Keywords", "Documents", "Metrics", "Highlights"];
    var lines = [header.map(csvEscape).join(",")];

    rows.forEach(function (row) {
      var keywords = row.keywords.join("; ");
      var documents = row.documents.map(function (d) {
        return d.url ? d.label + " (" + d.url + ")" : d.label;
      }).join("; ");
      var metrics = row.metrics.map(function (m) {
        return m.label + ": " + m.value;
      }).join("; ");

      // Use the unabbreviated form in the export: "GRI 302, GRI 303" rather
      // than the "302, 303" shorthand the table uses, so a downloaded file
      // is readable without the page next to it.
      var frameworks = (row.frameworks || []).map(function (f) {
        var text = f.full || f.detail;
        return f.name + (f.verified ? "" : " (provisional)") +
               (text ? ": " + text : "");
      }).join(" | ");

      var line = [row.theme, row.category, row.subfactor, frameworks, keywords, documents, metrics, row.highlights]
        .map(csvEscape).join(",");
      lines.push(line);
    });

    return "﻿" + lines.join("\r\n") + "\r\n";
  }

  function downloadCsv() {
    var theme = themeSelect.value;
    var keyword = keywordSelect.value;
    var framework = frameworkSelect.value;
    var query = searchInput.value.trim().toLowerCase();

    var visibleRows = data.rows.filter(function (row) {
      return rowMatches(row, theme, keyword, query, framework);
    });

    var csv = buildCsv(visibleRows);
    var blob = new Blob([csv], { type: "text/csv;charset=utf-8;" });
    var url = URL.createObjectURL(blob);

    var today = new Date();
    var dateStr = today.getFullYear() + "-" +
      String(today.getMonth() + 1).padStart(2, "0") + "-" +
      String(today.getDate()).padStart(2, "0");
    var filename = "esg-profile-" + slugify(data.company) + "-" + dateStr + ".csv";

    var a = document.createElement("a");
    a.href = url;
    a.download = filename;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  }

  themeSelect.addEventListener("change", function () {
    rebuildKeywordSelect();
    applyFilters();
  });

  frameworkSelect.addEventListener("change", function () {
    layoutTable(frameworkSelect.value);
    applyFilters();
  });

  keywordSelect.addEventListener("change", applyFilters);

  searchInput.addEventListener("input", function () {
    clearTimeout(searchDebounceTimer);
    searchDebounceTimer = setTimeout(applyFilters, SEARCH_DEBOUNCE_MS);
  });

  clearSearchBtn.addEventListener("click", function () {
    searchInput.value = "";
    applyFilters();
    searchInput.focus();
  });

  clearFiltersBtn.addEventListener("click", clearFilters);
  downloadCsvBtn.addEventListener("click", downloadCsv);
  printBtn.addEventListener("click", function () {
    window.print();
  });

  renderHeader();
  populateThemeSelect();
  populateFrameworkSelect();
  rebuildKeywordSelect();
  buildAllRows();
  layoutTable(frameworkSelect.value);
  detectClamps();
  applyFilters();
})();
