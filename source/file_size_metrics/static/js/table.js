const viewConversionDetails = (jobId) => {
  $("#selected_task_id").val(jobId).triggerHandler("change");
};

const defaultEmptyStateMessage =
  "Add this plugin to at least one library and process files to populate this panel.";
const panelState = {
  hasData: false,
  isAssigned: false,
};

const formatLocalDateTime = (timestamp) => {
  const numericTimestamp = Number(timestamp);
  if (!Number.isFinite(numericTimestamp) || numericTimestamp <= 0) {
    return "";
  }

  const date = new Date(numericTimestamp * 1000);
  const parts = new Intl.DateTimeFormat(undefined, {
    year: "numeric",
    month: "2-digit",
    day: "2-digit",
    hour: "2-digit",
    minute: "2-digit",
    second: "2-digit",
    hour12: false,
  }).formatToParts(date);

  const lookup = {};
  parts.forEach((part) => {
    lookup[part.type] = part.value;
  });

  return `${lookup.year}-${lookup.month}-${lookup.day} ${lookup.hour}:${lookup.minute}:${lookup.second}`;
};

const setMetricsPanelState = ({ hasData, isAssigned, message } = {}) => {
  const notice = document.getElementById("panelNotice");
  const noticeTitle = document.getElementById("panelNoticeTitle");
  const noticeMessage = document.getElementById("panelNoticeMessage");
  const noticeLink = document.getElementById("panelNoticeLink");

  if (!notice || !noticeTitle || !noticeMessage || !noticeLink) {
    return;
  }

  if (typeof hasData === "boolean") {
    panelState.hasData = panelState.hasData || hasData;
  }
  if (typeof isAssigned === "boolean") {
    panelState.isAssigned = panelState.isAssigned || isAssigned;
  }

  const hasMetrics = panelState.hasData;
  const hasAssignment = panelState.isAssigned;

  if (!hasMetrics && !hasAssignment) {
    notice.classList.remove("notice-banner-neutral");
    notice.classList.add("notice-banner-warning");
    noticeTitle.textContent =
      "Add this plugin to a library to start collecting metrics";
    noticeMessage.textContent = message || defaultEmptyStateMessage;
    noticeLink.classList.add("hidden");
    return;
  }

  notice.classList.remove("notice-banner-warning");
  notice.classList.add("notice-banner-neutral");
  noticeTitle.textContent =
    "Use Unmanic Central for multi-installation dashboards";
  noticeMessage.textContent =
    "This local panel is useful for reviewing one Unmanic installation. Unmanic Central lets you collect file size metrics from multiple installations into one place, then build custom dashboards alongside logs, resource usage, and other installation data.";
  noticeLink.classList.remove("hidden");
};

const CompletedTasksDatatable = (function () {
  const modal = document.querySelector("[data-modal]");

  const recordName = (basename, type, { task_success } = row) => {
    if (task_success) {
      return `<span class="q-badge success"></span> <span class="name" title="View Details">${basename}</span>`;
    }

    return `<span class="q-badge failed"></span> <span class="name" title="View Details">${basename}</span>`;
  };

  const buildTable = () => {
    const table = $("#history_completed_tasks_table").DataTable({
      autoWidth: false,
      processing: true,
      serverSide: true,
      ajax: {
        url: "list/", // ajax source
        type: "GET", // request type
        dataSrc: (json) => {
          setMetricsPanelState({
            hasData:
              typeof json?.hasData === "boolean"
                ? json.hasData
                : Number(json?.recordsTotal || 0) > 0,
            isAssigned:
              typeof json?.isAssigned === "boolean"
                ? json.isAssigned
                : undefined,
            message: json?.emptyStateMessage,
          });
          return json?.data || [];
        },
        data: (data) => {
          return {
            data: JSON.stringify(data),
          };
        },
        error: () => {
          setMetricsPanelState({
            hasData: false,
            message:
              "The metrics history could not be loaded. Add the plugin to a library and reload after the first processed files complete.",
          });
        },
      },
      language: {
        emptyTable:
          "No completed tasks have been recorded yet. Enable the plugin on a library and let Unmanic process files.",
        zeroRecords:
          "No matching metric records were found for the current filters.",
      },
      columnDefs: [
        {
          targets: 0,
          title: "New File Name",
          className: "basename",
          name: "basename",
          data: "basename",
          render: recordName,
        },
        {
          targets: 1,
          className: "start_time",
          title: "Start Time",
          name: "start_time",
          data: "start_time",
          render: (value) => formatLocalDateTime(value),
        },
        {
          targets: 2,
          title: "Finish Time",
          name: "finish_time",
          data: "finish_time",
          render: (value) => formatLocalDateTime(value),
        },
      ],
      lengthMenu: [
        [7, 10, 15, 20, 50, 100, 500],
        [7, 10, 15, 20, 50, 100, 500], // change per page values here
      ],
      pageLength: 15, // default record count per page
      order: [[2, "desc"]],
    });

    $("#refreshButton").on("click", () => {
      table.ajax.reload();
    });

    table.on("click", "tbody tr", function (e) {
      const data = table.row(this).data();
      const classList = e.currentTarget.classList;

      if (classList.contains("selected") === false) {
        table
          .rows(".selected")
          .nodes()
          .each((row) => row.classList.remove("selected"));
        classList.add("selected");

        viewConversionDetails(data.id);
      }

      if ($("#individual_file_size_chart").is(":visible") === false) {
        modal.showModal();
      }
    });
  };

  return {
    //main function to initiate the module
    init: () => {
      buildTable();
    },
  };
})();
