const CompletedTasksFileSizeDiffChart = (function () {
  /**
   * Format a byte integer into the smallest possible number appending a suffix
   *
   * REF:
   *  https://stackoverflow.com/questions/15900485/correct-way-to-convert-size-in-bytes-to-kb-mb-gb-in-javascript
   *
   * @param bytes
   * @param decimals
   * @returns {string}
   */
  const formatBytes = function (bytes) {
    if (bytes === 0) {
      return "0 Bytes";
    }

    // Rather than using `k = 1024;` (base 2) use `k = 1000;` (base 10)
    // This way the end result will better fit in with the high chart logic
    // Using Base 2 will lead to the chart sections showing a rounded number and
    // the bar showing something different
    const k = 1000;
    const dm = 2;
    const sizes = ["Bytes", "KB", "MB", "GB", "TB", "PB", "EB", "ZB", "YB"];
    const i = Math.floor(Math.log(bytes) / Math.log(k));

    return parseFloat((bytes / Math.pow(k, i)).toFixed(dm)) + " " + sizes[i];
  };

  const default_bar_colour = "#555";
  const positive_bar_colour = "var(--q-positive)";
  const negative_bar_colour = "var(--q-negative)";
  const text_colour = "var(--q-text)";
  const subtext_colour = "var(--q-subtext)";
  const chart_background = "var(--q-card)";
  const chartHeight = 300;

  let chart_title = "(Select a task from the table)";
  let source_file_size = 0;
  let destination_file_size = 0;
  let source_total_size = 0;
  let destination_total_size = 0;

  const individualChart = Highcharts.chart("file_size_chart", {
    chart: {
      backgroundColor: chart_background,
      height: chartHeight,
    },
    title: {
      text: "",
      style: {
        color: text_colour,
      },
    },
    subtitle: {
      text: chart_title,
      style: {
        color: subtext_colour,
      },
    },
    colors: [default_bar_colour, positive_bar_colour],
    xAxis: {
      type: "category",
      labels: {
        style: {
          color: text_colour,
        },
      },
      lineColor: text_colour,
    },
    yAxis: {
      labels: {
        style: {
          color: text_colour,
        },
      },
      title: {
        text: "Sizes",
        style: {
          color: subtext_colour,
        },
      },
    },
    legend: {
      enabled: false,
    },
    series: [],
  });

  const totalChart = Highcharts.chart("total_size_chart", {
    chart: {
      backgroundColor: chart_background,
      height: chartHeight,
    },
    title: {
      text: "",
      style: {
        color: text_colour,
      },
    },
    subtitle: {
      text: "Displaying the total file size changed on disk by Unmanic processing files",
      style: {
        color: subtext_colour,
      },
    },
    colors: [default_bar_colour, positive_bar_colour],
    xAxis: {
      type: "category",
      labels: {
        style: {
          color: text_colour,
        },
      },
      lineColor: text_colour,
    },
    yAxis: {
      labels: {
        style: {
          color: text_colour,
        },
      },
      title: {
        text: "Sizes",
        style: {
          color: subtext_colour,
        },
      },
    },
    legend: {
      enabled: false,
    },
    series: [],
  });

  const updateIndividualChart = function () {
    // If the destination file size is greater than the source, then mark it
    // negative, otherwise positive
    let reduced = true;
    let destination_bar_colour = positive_bar_colour;
    let percent_changed =
      100 - (destination_file_size / source_file_size) * 100;

    if (destination_file_size >= source_file_size) {
      reduced = false;
      destination_bar_colour = negative_bar_colour;
      percent_changed = 100 - (source_file_size / destination_file_size) * 100;
    }

    source_file_size = Number(source_file_size);
    destination_file_size = Number(destination_file_size);

    individualChart.update({
      chart: {
        backgroundColor: chart_background,
        type: "bar",
        width: null,
      },
      colors: [default_bar_colour, destination_bar_colour],
      title: {
        text:
          Highcharts.numberFormat(percent_changed, 2) +
          "% " +
          (reduced ? "decrease" : "increase") +
          " in file size",
      },
      subtitle: {
        text: chart_title,
      },
      tooltip: {
        formatter: function () {
          return `<strong>${this.series.name}</strong>
            <br>
            File Size: ${formatBytes(Math.abs(this.point.y))}`;
        },
      },
    });

    const newSeriesData = {
      borderWidth: 0,
      colorByPoint: true,
      name: "Size",
      data: [
        {
          name: "Original",
          y: source_file_size,
        },
        {
          name: "New",
          y: destination_file_size,
        },
      ],
    };

    for (let i = individualChart.series.length - 1; i >= 0; i--) {
      individualChart.series[i].remove(false);
    }

    individualChart.addSeries(newSeriesData, false);
    individualChart.redraw();
  };

  const updateTotalChart = function () {
    // If the destination file size is greater than the source, then mark it
    // negative, otherwise positive
    let change_text = "decrease";
    let destination_bar_colour = positive_bar_colour;
    let difference_in_total_file_sizes =
      source_total_size - destination_total_size;

    if (destination_total_size > source_total_size) {
      change_text = "increase";
      destination_bar_colour = negative_bar_colour;
      difference_in_total_file_sizes =
        destination_total_size - source_total_size;
    }

    source_total_size = Number(source_total_size);
    destination_total_size = Number(destination_total_size);

    totalChart.update({
      chart: {
        backgroundColor: chart_background,
        type: "bar",
        width: null,
      },
      title: {
        text: `${formatBytes(difference_in_total_file_sizes)}
          total ${change_text} in file size`,
      },
      colors: [default_bar_colour, destination_bar_colour],
      tooltip: {
        formatter: function () {
          return `<strong>${this.series.name}</strong>
            <br>
            File Size: ${formatBytes(Math.abs(this.point.y))}`;
        },
      },
    });

    const newSeriesData = {
      borderWidth: 0,
      colorByPoint: true,
      name: "Size",
      data: [
        {
          name: "Before",
          y: source_total_size,
        },
        {
          name: "After",
          y: destination_total_size,
        },
      ],
    };

    for (let i = totalChart.series.length - 1; i >= 0; i--) {
      totalChart.series[i].remove(false);
    }

    totalChart.addSeries(newSeriesData, false);
    totalChart.redraw();
  };

  const fetchConversionDetails = function (taskId) {
    jQuery.get(`conversionDetails/?task_id=${taskId}`, function (data) {
      // Update/set the conversion details list
      let source_abspath = "";
      let destination_abspath = "";

      for (let i = 0; i < data.length; i++) {
        const item = data[i];

        if (item.type === "source") {
          source_file_size = Number(item.size);
          source_abspath = item.abspath;
        } else if (item.type === "destination") {
          chart_title = item.basename;
          destination_file_size = Number(item.size);
          destination_abspath = item.abspath;
        }
      }

      updateIndividualChart();

      let html = "";

      if (source_abspath !== destination_abspath) {
        html = `<p>
                <strong>Original File Path:</strong>
                <br>
                ${source_abspath}
            </p>
            <p>
                <strong>New File Path:</strong>
                <br>
                ${destination_abspath}
            </p>`;
      } else {
        html = `<p>
            <strong>File Path:</strong>
            <br>
            ${source_abspath}
        </p>`;
      }

      $("#selected_task_name").html(html);
    });
  };

  const fetchTotalFileSizeDetails = function () {
    jQuery.get("totalSizeChange", function (data) {
      // Update/set the conversion details list
      source_total_size = data.source;
      destination_total_size = data.destination;
      updateTotalChart();
    });
  };

  const watch = function () {
    const selectedTaskId = $("#selected_task_id");

    selectedTaskId
      .on("change", function () {
        if (this.value !== "") {
          fetchConversionDetails(this.value);
        }
      })
      .triggerHandler("change");
  };

  return {
    //main function to initiate the module
    init: function () {
      watch();
      fetchTotalFileSizeDetails();
    },
  };
})();
