(function () {
  "use strict";

  var data = window.ESG_DATA;
  var ALL_THEMES = "All Themes";
  var ALL_KEYWORDS = "All Keywords";
  var SEARCH_DEBOUNCE_MS = 120;

  var themeSelect = document.getElementById("theme-select");
  var keywordSelect = document.getElementById("keyword-select");
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
    if (row.keywords.length > 0) {
      var pillWrap = document.createElement("div");
      pillWrap.className = "keyword-pills";
      row.keywords.forEach(function (kw) {
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
      highlightsTd.appendChild(buildMetricsBlock(row.metrics));
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

  function buildCategoryRow(categoryName) {
    var tr = document.createElement("tr");
    tr.className = "category-row";
    var th = document.createElement("th");
    th.setAttribute("scope", "colgroup");
    th.setAttribute("colspan", "4");
    th.textContent = categoryName;
    tr.appendChild(th);
    tr._categoryName = categoryName;
    return tr;
  }

  var allRowElements = [];
  var allCategoryElements = [];

  function renderTable() {
    var fragment = document.createDocumentFragment();
    var currentCategory = null;

    data.rows.forEach(function (row) {
      if (row.category !== currentCategory) {
        currentCategory = row.category;
        var categoryRow = buildCategoryRow(currentCategory);
        fragment.appendChild(categoryRow);
        allCategoryElements.push(categoryRow);
      }
      var dataRow = buildRow(row);
      dataRow._categoryName = currentCategory;
      fragment.appendChild(dataRow);
      allRowElements.push(dataRow);
    });

    tableBody.appendChild(fragment);

    // One-time overflow check: only show "Show more" when the clamped
    // text actually overflows. Reads layout, so it must happen after the
    // rows are attached to the document.
    allRowElements.forEach(function (tr) {
      var p = tr._highlightsP;
      if (p.scrollHeight > p.clientHeight + 1) {
        tr._toggleBtn.hidden = false;
      }
    });
  }

  function rowMatches(row, theme, keyword, query) {
    if (theme !== ALL_THEMES && row.theme !== theme) return false;
    if (keyword !== ALL_KEYWORDS && row.keywords.indexOf(keyword) === -1) return false;

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
    var query = searchInput.value.trim().toLowerCase();

    clearSearchBtn.hidden = searchInput.value.length === 0;

    var visibleCount = 0;
    var categoriesWithVisibleRows = {};

    allRowElements.forEach(function (tr) {
      var isVisible = rowMatches(tr._rowData, theme, keyword, query);
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
      theme + " · " + keyword + " · " + visibleCount + " of " + total + " disclosures"
    ].join(" — ");
  }

  function clearFilters() {
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
    var header = ["Theme", "Category", "Sub Factor", "Keywords", "Documents", "Metrics", "Highlights"];
    var lines = [header.map(csvEscape).join(",")];

    rows.forEach(function (row) {
      var keywords = row.keywords.join("; ");
      var documents = row.documents.map(function (d) {
        return d.url ? d.label + " (" + d.url + ")" : d.label;
      }).join("; ");
      var metrics = row.metrics.map(function (m) {
        return m.label + ": " + m.value;
      }).join("; ");

      var line = [row.theme, row.category, row.subfactor, keywords, documents, metrics, row.highlights]
        .map(csvEscape).join(",");
      lines.push(line);
    });

    return "﻿" + lines.join("\r\n") + "\r\n";
  }

  function downloadCsv() {
    var theme = themeSelect.value;
    var keyword = keywordSelect.value;
    var query = searchInput.value.trim().toLowerCase();

    var visibleRows = data.rows.filter(function (row) {
      return rowMatches(row, theme, keyword, query);
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
  rebuildKeywordSelect();
  renderTable();
  applyFilters();
})();
