// ==========================================================================
// AI CSV Analyzer - Client Application Logic (script.js)
// ==========================================================================

document.addEventListener("DOMContentLoaded", () => {
    // DOM Element References
    const dropZone = document.getElementById("dropZone");
    const csvFileInput = document.getElementById("csvFileInput");
    const selectBtn = document.getElementById("selectBtn");
    const selectedFileInfo = document.getElementById("selectedFileInfo");
    const selectedFileName = document.getElementById("selectedFileName");
    const selectedFileSize = document.getElementById("selectedFileSize");
    const clearFileBtn = document.getElementById("clearFileBtn");
    const uploadForm = document.getElementById("uploadForm");
    const analyzeBtn = document.getElementById("analyzeBtn");
    const sampleDataBtn = document.getElementById("sampleDataBtn");
    const errorAlert = document.getElementById("errorAlert");
    const errorMessage = document.getElementById("errorMessage");
    const loadingSection = document.getElementById("loadingSection");
    const resultsSection = document.getElementById("resultsSection");
    const printReportBtn = document.getElementById("printReportBtn");

    let currentFile = null;

    // -------------------------------------------------------------------------
    // File Selection & Drag-and-Drop Handlers
    // -------------------------------------------------------------------------

    selectBtn.addEventListener("click", () => csvFileInput.click());

    dropZone.addEventListener("click", (e) => {
        if (e.target !== selectBtn && !e.target.closest(".selected-file-info")) {
            csvFileInput.click();
        }
    });

    dropZone.addEventListener("keydown", (e) => {
        if (e.key === "Enter" || e.key === " ") {
            e.preventDefault();
            csvFileInput.click();
        }
    });

    ["dragenter", "dragover"].forEach((eventName) => {
        dropZone.addEventListener(eventName, (e) => {
            e.preventDefault();
            e.stopPropagation();
            dropZone.classList.add("dragover");
        });
    });

    ["dragleave", "drop"].forEach((eventName) => {
        dropZone.addEventListener(eventName, (e) => {
            e.preventDefault();
            e.stopPropagation();
            dropZone.classList.remove("dragover");
        });
    });

    dropZone.addEventListener("drop", (e) => {
        const dt = e.dataTransfer;
        const files = dt.files;
        if (files && files.length > 0) {
            handleFileSelect(files[0]);
        }
    });

    csvFileInput.addEventListener("change", (e) => {
        if (e.target.files && e.target.files.length > 0) {
            handleFileSelect(e.target.files[0]);
        }
    });

    clearFileBtn.addEventListener("click", (e) => {
        e.stopPropagation();
        resetFileInput();
    });

    function handleFileSelect(file) {
        hideError();
        if (!file.name.toLowerCase().endsWith(".csv")) {
            showError("Invalid file format. Please choose a file ending with .csv.");
            resetFileInput();
            return;
        }
        currentFile = file;
        selectedFileName.textContent = file.name;
        selectedFileSize.textContent = `(${formatBytes(file.size)})`;
        selectedFileInfo.style.display = "inline-flex";
    }

    function resetFileInput() {
        currentFile = null;
        csvFileInput.value = "";
        selectedFileInfo.style.display = "none";
    }

    function formatBytes(bytes) {
        if (bytes === 0) return "0 Bytes";
        const k = 1024;
        const sizes = ["Bytes", "KB", "MB", "GB"];
        const i = Math.floor(Math.log(bytes) / Math.log(k));
        return parseFloat((bytes / Math.pow(k, i)).toFixed(1)) + " " + sizes[i];
    }

    // -------------------------------------------------------------------------
    // Form Submission & Analysis Pipeline
    // -------------------------------------------------------------------------

    uploadForm.addEventListener("submit", async (e) => {
        e.preventDefault();
        hideError();

        if (!currentFile) {
            showError("Please select a CSV file first or click 'Quick Demo with Sample'.");
            return;
        }

        const formData = new FormData();
        formData.append("file", currentFile);

        await executeAnalysisRequest("/analyze", {
            method: "POST",
            body: formData,
        });
    });

    sampleDataBtn.addEventListener("click", async () => {
        hideError();
        await executeAnalysisRequest("/sample", { method: "GET" });
    });

    async function executeAnalysisRequest(url, options) {
        setLoadingState(true);
        resultsSection.style.display = "none";

        try {
            const response = await fetch(url, options);
            const json = await response.json();

            if (!response.ok || !json.success) {
                const errText = json.error || `Server responded with status ${response.status}`;
                showError(errText);
                return;
            }

            renderDashboard(json.data);
            resultsSection.scrollIntoView({ behavior: "smooth", block: "start" });
        } catch (err) {
            showError("Connection error: Unable to reach analysis server. Please ensure the app is running.");
            console.error("Analysis Request Error:", err);
        } finally {
            setLoadingState(false);
        }
    }

    function setLoadingState(isLoading) {
        loadingSection.style.display = isLoading ? "block" : "none";
        analyzeBtn.disabled = isLoading;
        sampleDataBtn.disabled = isLoading;
    }

    function showError(msg) {
        errorMessage.textContent = msg;
        errorAlert.style.display = "flex";
        errorAlert.scrollIntoView({ behavior: "smooth", block: "nearest" });
    }

    window.hideError = function () {
        errorAlert.style.display = "none";
    };

    // -------------------------------------------------------------------------
    // Dashboard Rendering
    // -------------------------------------------------------------------------

    function renderDashboard(data) {
        document.getElementById("resFilename").textContent = data.filename || "Dataset";
        document.getElementById("resTotalRows").textContent = Number(data.total_rows).toLocaleString("en-US");
        document.getElementById("resTotalCols").textContent = Number(data.total_columns).toLocaleString("en-US");
        document.getElementById("resTotalMissing").textContent = Number(data.total_missing).toLocaleString("en-US");

        // Primary Financial/Sales Metric Highlight
        const salesCard = document.getElementById("salesSummaryMetricCard");
        if (data.sales_analysis) {
            salesCard.style.display = "flex";
            document.getElementById("resSalesLabel").textContent = `Total ${data.sales_analysis.column}`;
            document.getElementById("resSalesTotal").textContent = formatCurrency(data.sales_analysis.total);
        } else {
            salesCard.style.display = "none";
        }

        renderAiReport(data.ai_report, data.ai_error);
        renderNumericTable(data.numeric_stats);
        renderMissingTable(data.missing, data.total_rows);
        renderTopCategories(data.top_values);
        renderRawPreview(data.columns, data.preview);

        resultsSection.style.display = "block";
    }

    function renderAiReport(reportText, errorText) {
        const bodyEl = document.getElementById("aiReportContent");
        const warningBox = document.getElementById("aiWarningBox");
        const warningText = document.getElementById("aiWarningText");

        bodyEl.innerHTML = "";
        warningBox.style.display = "none";

        if (errorText) {
            warningText.textContent = errorText;
            warningBox.style.display = "flex";
        }

        if (reportText) {
            bodyEl.innerHTML = formatMarkdownSections(reportText);
        } else if (!errorText) {
            bodyEl.innerHTML = "<p>No AI report could be produced for this dataset.</p>";
        }
    }

    function formatMarkdownSections(rawText) {
        // Split by numbered sections (e.g. "1. Executive Summary" or "1. Genel Özet")
        const sections = rawText.split(/(?=\d+\.\s+)/);
        let html = "";

        sections.forEach((sec) => {
            const trimmed = sec.trim();
            if (!trimmed) return;

            const headerMatch = trimmed.match(/^(\d+\.\s+[^\n:]+):?/);
            if (headerMatch) {
                const heading = headerMatch[1];
                const content = trimmed.substring(headerMatch[0].length).trim();
                const lines = content.split("\n").filter((l) => l.trim().length > 0);

                let listHtml = "<ul>";
                lines.forEach((line) => {
                    let cleaned = line.replace(/^[-*•]\s*/, "").trim();
                    cleaned = cleaned.replace(/\*\*(.*?)\*\*/g, "<strong>$1</strong>");
                    listHtml += `<li>${cleaned}</li>`;
                });
                listHtml += "</ul>";

                html += `
                    <div class="ai-section-box">
                        <h3>📌 ${heading}</h3>
                        ${listHtml}
                    </div>
                `;
            } else {
                let formatted = trimmed.replace(/\*\*(.*?)\*\*/g, "<strong>$1</strong>");
                html += `<div class="ai-section-box"><p>${formatted.replace(/\n/g, "<br>")}</p></div>`;
            }
        });

        return html || rawText.replace(/\n/g, "<br>");
    }

    function renderNumericTable(numericStats) {
        const tbody = document.getElementById("numericTableBody");
        tbody.innerHTML = "";

        const cols = Object.keys(numericStats || {});
        if (cols.length === 0) {
            tbody.innerHTML = '<tr><td colspan="5" class="text-center text-muted">No purely numeric columns detected in this dataset.</td></tr>';
            return;
        }

        cols.forEach((col) => {
            const s = numericStats[col];
            const tr = document.createElement("tr");
            tr.innerHTML = `
                <td><strong>${escapeHtml(col)}</strong></td>
                <td class="text-right num-cell">${formatNumber(s.total)}</td>
                <td class="text-right num-cell">${formatNumber(s.average)}</td>
                <td class="text-right num-cell">${formatNumber(s.min)}</td>
                <td class="text-right num-cell">${formatNumber(s.max)}</td>
            `;
            tbody.appendChild(tr);
        });
    }

    function renderMissingTable(missingDict, totalRows) {
        const tbody = document.getElementById("missingTableBody");
        tbody.innerHTML = "";

        const cols = Object.keys(missingDict || {});
        cols.forEach((col) => {
            const item = missingDict[col];
            const isWarning = item.percent > 0;
            const tr = document.createElement("tr");
            tr.innerHTML = `
                <td>${escapeHtml(col)}</td>
                <td class="text-right num-cell">${item.count}</td>
                <td class="text-right num-cell">${totalRows}</td>
                <td class="text-right num-cell">
                    <div class="percent-bar-wrap">
                        <div class="percent-bar">
                            <div class="percent-bar-fill ${isWarning ? 'warning' : ''}" style="width: ${Math.min(item.percent, 100)}%;"></div>
                        </div>
                        <span>${item.percent.toFixed(1)}%</span>
                    </div>
                </td>
            `;
            tbody.appendChild(tr);
        });
    }

    function renderTopCategories(topValues) {
        const container = document.getElementById("categoriesContent");
        container.innerHTML = "";

        const cols = Object.keys(topValues || {});
        if (cols.length === 0) {
            container.innerHTML = "<p class='text-muted'>No recurring categorical text values identified.</p>";
            return;
        }

        const grid = document.createElement("div");
        grid.className = "categories-grid";

        cols.forEach((col) => {
            const items = topValues[col];
            const card = document.createElement("div");
            card.className = "category-column-card";

            let itemsHtml = "";
            items.forEach(([val, count]) => {
                itemsHtml += `
                    <div class="category-item">
                        <span class="category-val" title="${escapeHtml(val)}">${escapeHtml(val)}</span>
                        <span class="category-cnt">${count}x</span>
                    </div>
                `;
            });

            card.innerHTML = `
                <div class="category-col-name">${escapeHtml(col)}</div>
                <div class="category-list">${itemsHtml}</div>
            `;
            grid.appendChild(card);
        });

        container.appendChild(grid);
    }

    function renderRawPreview(columns, previewRows) {
        const thead = document.getElementById("previewTableHead");
        const tbody = document.getElementById("previewTableBody");

        thead.innerHTML = "";
        tbody.innerHTML = "";

        if (!columns || columns.length === 0) return;

        const headerTr = document.createElement("tr");
        columns.forEach((col) => {
            const th = document.createElement("th");
            th.textContent = col;
            headerTr.appendChild(th);
        });
        thead.appendChild(headerTr);

        previewRows.forEach((row) => {
            const tr = document.createElement("tr");
            columns.forEach((_, idx) => {
                const td = document.createElement("td");
                td.textContent = row[idx] !== undefined ? row[idx] : "";
                tr.appendChild(td);
            });
            tbody.appendChild(tr);
        });
    }

    function formatNumber(num) {
        if (num === null || num === undefined || isNaN(num)) return "-";
        return Number(num).toLocaleString("en-US", {
            minimumFractionDigits: 2,
            maximumFractionDigits: 2,
        });
    }

    function formatCurrency(num) {
        if (num === null || num === undefined || isNaN(num)) return "-";
        return Number(num).toLocaleString("en-US", {
            minimumFractionDigits: 2,
            maximumFractionDigits: 2,
        });
    }

    function escapeHtml(str) {
        if (!str) return "";
        return String(str)
            .replace(/&/g, "&amp;")
            .replace(/</g, "&lt;")
            .replace(/>/g, "&gt;")
            .replace(/"/g, "&quot;")
            .replace(/'/g, "&#039;");
    }

    printReportBtn.addEventListener("click", () => {
        window.print();
    });
});
