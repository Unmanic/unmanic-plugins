const ResetMetrics = (function () {
  const resetDialog = document.querySelector("[data-reset-modal]");
  const resetBtn = document.getElementById("reset-metrics-btn");
  const cancelBtn = document.getElementById("reset-cancel-btn");
  const confirmBtn = document.getElementById("reset-confirm-btn");

  const showResetDialog = () => {
    resetDialog.showModal();
  };

  const hideResetDialog = () => {
    resetDialog.close();
  };

  const performReset = () => {
    // Disable the confirm button and show loading state
    confirmBtn.disabled = true;
    confirmBtn.textContent = "Resetting...";

    jQuery
      .ajax({
        url: "resetMetrics/",
        method: "GET",
        dataType: "json",
      })
      .done(function (data) {
        hideResetDialog();

        if (data && data.success === true) {
          // Refresh the DataTable
          $("#history_completed_tasks_table").DataTable().ajax.reload();

          // Refresh the total size chart
          CompletedTasksFileSizeDiffChart.init();

          // Clear the individual chart selection
          $("#selected_task_id").val("").triggerHandler("change");
          $(".selected_task_name").html("");
        } else {
          const message = (data && data.message) || "Unknown error occurred";
          alert("Failed to reset metrics: " + message);
        }

        // Reset button state
        confirmBtn.disabled = false;
        confirmBtn.textContent = "Reset All Data";
      })
      .fail(function (jqXHR, textStatus, errorThrown) {
        hideResetDialog();
        alert("An error occurred while trying to reset metrics: " + textStatus);

        // Reset button state
        confirmBtn.disabled = false;
        confirmBtn.textContent = "Reset All Data";
      });
  };

  const bindEvents = () => {
    // Open dialog when reset button is clicked
    resetBtn.addEventListener("click", (e) => {
      e.preventDefault();
      e.stopPropagation();
      showResetDialog();
    });

    // Close dialog when cancel is clicked
    cancelBtn.addEventListener("click", (e) => {
      e.preventDefault();
      hideResetDialog();
    });

    // Perform reset when confirm is clicked
    confirmBtn.addEventListener("click", (e) => {
      e.preventDefault();
      performReset();
    });

    // Close dialog when clicking outside (on backdrop)
    resetDialog.addEventListener("click", (e) => {
      if (e.target === resetDialog) {
        hideResetDialog();
      }
    });

    // Close dialog on Escape key
    resetDialog.addEventListener("keydown", (e) => {
      if (e.key === "Escape") {
        hideResetDialog();
      }
    });
  };

  return {
    init: () => {
      bindEvents();
    },
  };
})();
