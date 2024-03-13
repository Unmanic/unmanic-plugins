const viewConversionDetails = (jobId) => {
  $("#selected_task_id").val(jobId).triggerHandler("change");
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
        data: (data) => {
          return {
            data: JSON.stringify(data),
          };
        },
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
        },
        {
          targets: 2,
          title: "Finish Time",
          name: "finish_time",
          data: "finish_time",
        },
      ],
      lengthMenu: [
        [7, 10, 15, 20, 50, 100, 500],
        [7, 10, 15, 20, 50, 100, 500], // change per page values here
      ],
      pageLength: 15, // default record count per page
      order: [[2, "desc"]],
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
