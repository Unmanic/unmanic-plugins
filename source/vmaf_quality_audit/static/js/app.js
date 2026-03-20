const AppState = {
  records: [],
  filtered: [],
  selectedId: null,
};

const query = (selector) => document.querySelector(selector);

const formatNumber = (value, decimals = 3) => {
  if (value === null || value === undefined || Number.isNaN(Number(value))) {
    return "-";
  }
  return Number(value).toFixed(decimals);
};

const formatTestDuration = (seconds) => {
  if (seconds === null || seconds === undefined || Number.isNaN(Number(seconds))) {
    return "";
  }
  const totalSeconds = Math.max(0, Math.round(Number(seconds)));
  const minutes = Math.floor(totalSeconds / 60);
  const hours = Math.floor(minutes / 60);
  const remMinutes = minutes % 60;
  const remSeconds = totalSeconds % 60;
  if (hours) return `${hours}h ${remMinutes}m ${remSeconds}s`;
  if (minutes) return `${minutes}m ${remSeconds}s`;
  return `${remSeconds}s`;
};

const describeVmaf = (value) => {
  const score = Number(value);
  if (Number.isNaN(score)) return "No VMAF result";
  if (score >= 95) return "Excellent retention";
  if (score >= 90) return "Very good retention";
  if (score >= 80) return "Noticeable compromise";
  return "Low score, inspect closely";
};

const statusBadge = (record) => {
  const status = record.overall_status || "unknown";

  if (status.startsWith("completed")) {
    return `<span class="badge success">Completed</span>`;
  }
  if (status.startsWith("postprocess_failed")) {
    return `<span class="badge warning">Post-process Failed</span>`;
  }
  if (status.startsWith("processing_failed")) {
    return `<span class="badge failed">Processing Failed</span>`;
  }
  return `<span class="badge muted">${status}</span>`;
};

const analysisBadge = (record) => {
  if (record.analysis_success) {
    return `<span class="badge success">VMAF Ready</span>`;
  }
  return `<span class="badge failed">Analysis Failed</span>`;
};

const statusMatchesFilter = (record, filterValue) => {
  if (filterValue === "all") return true;
  if (filterValue === "analysis_failed") return !record.analysis_success;
  return (record.overall_status || "").startsWith(filterValue);
};

const sortRecords = (records, sortValue) => {
  const copy = [...records];
  copy.sort((left, right) => {
    switch (sortValue) {
      case "finish_asc":
        return (left.finish_time || "").localeCompare(right.finish_time || "");
      case "vmaf_desc":
        return (right.vmaf_mean ?? -1) - (left.vmaf_mean ?? -1);
      case "vmaf_asc":
        return (left.vmaf_mean ?? 9999) - (right.vmaf_mean ?? 9999);
      case "finish_desc":
      default:
        return (right.finish_time || "").localeCompare(left.finish_time || "");
    }
  });
  return copy;
};

const renderSummary = (summary) => {
  query("#summaryTotal").textContent = summary.total_records ?? 0;
  query("#summaryCompleted").textContent = summary.completed_records ?? 0;
  query("#summaryFailed").textContent = summary.failed_records ?? 0;
  query("#summaryAverage").textContent =
    summary.average_vmaf === null || summary.average_vmaf === undefined
      ? "-"
      : formatNumber(summary.average_vmaf, 2);
};

const renderRecordList = () => {
  const list = query("#recordList");
  const emptyState = query("#emptyState");
  const count = query("#recordCount");
  count.textContent = `${AppState.filtered.length} shown`;

  if (!AppState.filtered.length) {
    list.innerHTML = "";
    emptyState.classList.remove("hidden");
    return;
  }

  emptyState.classList.add("hidden");
  list.innerHTML = AppState.filtered
    .map((record) => {
      const activeClass = record.id === AppState.selectedId ? "active" : "";
      const testDuration = formatTestDuration(record.test_duration_seconds);
      return `
        <article class="record-card ${activeClass}" data-record-id="${record.id}">
          <div class="record-head">
            <div>
              <div class="record-title">${record.source_basename || record.task_label}</div>
              <div class="record-subtitle">
                ${record.codec_name || "Unknown codec"} ${record.resolution ? `• ${record.resolution}` : ""}
              </div>
            </div>
            <div class="badge-row">
              ${statusBadge(record)}
              ${analysisBadge(record)}
            </div>
          </div>
          <div class="record-tail">
            <div class="record-meta">
              <span class="muted">Finished ${record.finish_time || "Pending"}</span>
              ${testDuration ? `<span class="muted">Test Duration ${testDuration}</span>` : ""}
            </div>
            <div class="record-title">${record.vmaf_mean === null || record.vmaf_mean === undefined ? "No score" : `VMAF ${formatNumber(record.vmaf_mean, 2)}`}</div>
          </div>
        </article>
      `;
    })
    .join("");

  list.querySelectorAll("[data-record-id]").forEach((item) => {
    item.addEventListener("click", async () => {
      AppState.selectedId = Number(item.dataset.recordId);
      renderRecordList();
      await fetchDetail(AppState.selectedId);
    });
  });
};

const renderMetaList = (targetSelector, data) => {
  const entries = [
    ["Codec", data.codec_name || "-"],
    ["Profile", data.profile || "-"],
    ["Resolution", data.width && data.height ? `${data.width}x${data.height}` : "-"],
    ["Pixel Format", data.pix_fmt || "-"],
    ["Bitrate", data.bit_rate ? `${data.bit_rate} bps` : "-"],
    ["FPS", data.avg_frame_rate ? formatNumber(data.avg_frame_rate, 3) : "-"],
    ["Duration", data.duration ? `${formatNumber(data.duration, 3)} s` : "-"],
    ["Color Space", data.color_space || "-"],
  ];

  query(targetSelector).innerHTML = entries
    .map(([label, value]) => `<dt>${label}</dt><dd>${value}</dd>`)
    .join("");
};

const polylinePoints = (frames) => {
  if (!frames.length) return "";
  const width = 960;
  const height = 260;
  return frames
    .map((item, index) => {
      const x = frames.length === 1 ? width / 2 : (index / (frames.length - 1)) * width;
      const clamped = Math.max(0, Math.min(100, item.vmaf ?? 0));
      const y = height - (clamped / 100) * height;
      return `${x},${y}`;
    })
    .join(" ");
};

const renderChart = (frames) => {
  const svg = query("#detailChart");
  if (!frames.length) {
    svg.innerHTML = "";
    query("#detailChartCaption").textContent = "No frame-level scores were stored for this record.";
    return;
  }

  svg.innerHTML = `
    <defs>
      <linearGradient id="chartFill" x1="0" x2="0" y1="0" y2="1">
        <stop offset="0%" stop-color="var(--accent)" stop-opacity="0.32"></stop>
        <stop offset="100%" stop-color="var(--accent)" stop-opacity="0"></stop>
      </linearGradient>
    </defs>
    <polyline
      fill="none"
      stroke="var(--accent)"
      stroke-width="4"
      stroke-linecap="round"
      stroke-linejoin="round"
      points="${polylinePoints(frames)}"
    ></polyline>
  `;

  query("#detailChartCaption").textContent =
    `${frames.length} sampled frame scores are shown. Values are charted on a 0-100 VMAF scale.`;
};

const renderPaths = (detail) => {
  const items = [
    ["Source File", detail.source_abspath],
    ["Analyzed Cache File", detail.analyzed_abspath],
    ["Final Cache File", detail.final_cache_path],
    ["Started", detail.start_time],
    ["Finished", detail.finish_time],
  ];

  query("#detailPaths").innerHTML = items
    .filter(([, value]) => value)
    .map(
      ([label, value]) => `
        <div class="path-item">
          <span>${label}</span>
          <strong>${value}</strong>
        </div>
      `
    )
    .join("");
};

const renderDestinationFiles = (files) => {
  if (!files.length) {
    query("#destinationFiles").innerHTML = `<div class="destination-item"><span>Destination Files</span><strong>No destination files were recorded.</strong></div>`;
    return;
  }

  query("#destinationFiles").innerHTML = files
    .map(
      (file) => `
        <div class="destination-item">
          <span>${file.exists ? "Recorded Destination" : "Missing Destination"}</span>
          <strong>${file.path}</strong>
          <div class="muted">${file.size ? `${file.size} bytes` : "Size unavailable"}</div>
        </div>
      `
    )
    .join("");
};

const renderDetail = (detail) => {
  query("#detailPlaceholder").classList.add("hidden");
  query("#detailView").classList.remove("hidden");

  query("#detailTitle").textContent = detail.source_basename || detail.task_label || `Task ${detail.task_id}`;
  query("#detailTaskBadge").outerHTML = statusBadge(detail).replace('<span class="badge', '<span id="detailTaskBadge" class="badge');
  query("#detailAnalysisBadge").outerHTML = analysisBadge(detail).replace('<span class="badge', '<span id="detailAnalysisBadge" class="badge');

  query("#detailVmafMean").textContent = formatNumber(detail.vmaf_mean, 2);
  query("#detailVmafMeaning").textContent = describeVmaf(detail.vmaf_mean);
  query("#detailVmafHarmonic").textContent = formatNumber(detail.vmaf_harmonic_mean, 2);
  query("#detailVmafRange").textContent =
    detail.vmaf_min === null || detail.vmaf_max === null
      ? "-"
      : `${formatNumber(detail.vmaf_min, 2)} - ${formatNumber(detail.vmaf_max, 2)}`;
  query("#detailFrameCount").textContent = detail.frame_count ?? "-";

  renderChart(detail.vmaf_frames || []);
  renderMetaList("#sourceVideoMeta", detail.source_video || {});
  renderMetaList("#outputVideoMeta", detail.output_video || {});
  renderPaths(detail);
  renderDestinationFiles(detail.destination_files || []);
  query("#ffmpegCommand").textContent = detail.ffmpeg_command || "No command was stored.";

  if (detail.analysis_error) {
    query("#analysisErrorSection").classList.remove("hidden");
    query("#analysisError").textContent = detail.analysis_error;
  } else {
    query("#analysisErrorSection").classList.add("hidden");
    query("#analysisError").textContent = "";
  }
};

const applyFilters = () => {
  const searchValue = query("#searchInput").value.trim().toLowerCase();
  const statusValue = query("#statusFilter").value;
  const sortValue = query("#sortSelect").value;

  AppState.filtered = AppState.records.filter((record) => {
    const haystack = [
      record.source_basename,
      record.task_label,
      record.codec_name,
      record.overall_status,
      record.analysis_error,
    ]
      .join(" ")
      .toLowerCase();

    const matchesSearch = !searchValue || haystack.includes(searchValue);
    return matchesSearch && statusMatchesFilter(record, statusValue);
  });

  AppState.filtered = sortRecords(AppState.filtered, sortValue);

  if (!AppState.filtered.some((record) => record.id === AppState.selectedId)) {
    AppState.selectedId = AppState.filtered[0]?.id ?? null;
  }

  renderRecordList();
  if (AppState.selectedId) {
    fetchDetail(AppState.selectedId);
  } else {
    query("#detailPlaceholder").classList.remove("hidden");
    query("#detailView").classList.add("hidden");
  }
};

const fetchRecords = async () => {
  const response = await fetch("records/");
  const payload = await response.json();
  AppState.records = payload.data || [];
  renderSummary(payload.summary || {});
  applyFilters();
};

const fetchDetail = async (recordId) => {
  if (!recordId) return;
  const response = await fetch(`detail/?id=${recordId}`);
  const payload = await response.json();
  renderDetail(payload || {});
};

const resetHistory = async () => {
  const response = await fetch("reset/");
  const payload = await response.json();
  if (!payload.success) {
    window.alert(payload.message || "Failed to reset history.");
    return;
  }
  AppState.selectedId = null;
  await fetchRecords();
};

const init = () => {
  query("#searchInput").addEventListener("input", applyFilters);
  query("#statusFilter").addEventListener("change", applyFilters);
  query("#sortSelect").addEventListener("change", applyFilters);
  query("#refreshButton").addEventListener("click", fetchRecords);

  const guidanceDialog = query("#guidanceDialog");
  query("#guidanceInfoButton").addEventListener("click", () => guidanceDialog.showModal());

  const dialog = query("#confirmDialog");
  query("#resetButton").addEventListener("click", () => dialog.showModal());
  dialog.addEventListener("close", async () => {
    if (dialog.returnValue === "confirm") {
      await resetHistory();
    }
  });

  fetchRecords();
};

window.addEventListener("DOMContentLoaded", init);
