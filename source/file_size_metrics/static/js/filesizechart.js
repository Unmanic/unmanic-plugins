const CompletedTasksFileSizeDiffChart = function () {

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
        if (bytes === 0) return '0 Bytes';
        // Rather than using `let k = 1024;` (base 2) use `let k = 1000;` (base 10)
        // This way the end result will better fit in with the high chart logic
        // Using Base 2 will lead to the chart sections showing a rounded number and the bar showing something different
        let k = 1000;
        let dm = 2
        let sizes = ['Bytes', 'KB', 'MB', 'GB', 'TB', 'PB', 'EB', 'ZB', 'YB'];
        let i = Math.floor(Math.log(bytes) / Math.log(k));
        return parseFloat((bytes / Math.pow(k, i)).toFixed(dm)) + ' ' + sizes[i];
    };

    let positive = '#009fdd';
    let negative = '#C10015';

    let chart_title = '(Select a task from the table below)';
    let source_file_size = 0;
    let destination_file_size = 0;
    let source_total_size = 0;
    let destination_total_size = 0;

    const individualChart = Highcharts.chart('file_size_chart', {
        title: {
            text: ''
        },
        subtitle: {
            text: chart_title
        },
        colors: ['#555555', '#cccccc'],
        xAxis: {
            categories: ['Original', 'New']
        },
        series: []
    });

    const totalChart = Highcharts.chart('total_size_chart', {
        title: {
            text: ''
        },
        subtitle: {
            text: 'Displaying the total file size changed on disk by Unmanic processing files'
        },
        colors: ['#555555', '#cccccc'],
        xAxis: {
            categories: ['Before', 'After']
        },
        series: []
    });


    const updateIndividualChart = function () {
        // If the destination file size is greater than the source, then mark it negative, otherwise positive
        let reduced = true;
        let destination_bar_colour = positive;
        let percent_changed = 100 - (destination_file_size / source_file_size * 100);
        if (destination_file_size >= source_file_size) {
            reduced = false;
            destination_bar_colour = negative;
            percent_changed = 100 - (source_file_size / destination_file_size * 100);
        }
        source_file_size = Number(source_file_size)
        destination_file_size = Number(destination_file_size)

        individualChart.update({
            chart: {
                type: 'bar',
                width: null
            },
            colors: ['#555555', destination_bar_colour],
            title: {
                text: Highcharts.numberFormat(percent_changed, 2) + '% ' + ((reduced) ? 'decrease' : 'increase') + ' in file size'
            },
            subtitle: {
                text: chart_title
            },
            tooltip: {
                formatter: function () {
                    return '<b>' + this.series.name + '</b><br/>' +
                        'File Size: ' + formatBytes(Math.abs(this.point.y));
                }
            },
        });
        let newSeriesData = [
            {
                name: 'New',
                data: [0, destination_file_size]
            },
            {
                name: 'Original',
                data: [source_file_size, 0]
            },
        ]
        for (let i = individualChart.series.length - 1; i >= 0; i--) {
            individualChart.series[i].remove();
        }
        for (let y = newSeriesData.length - 1; y >= 0; y--) {
            individualChart.addSeries(newSeriesData[y]);
        }
    };


    const updateTotalChart = function () {
        // If the destination file size is greater than the source, then mark it negative, otherwise positive
        let change_text = 'decrease';
        let destination_bar_colour = positive;
        let difference_in_total_file_sizes = (source_total_size - destination_total_size)
        if (destination_total_size > source_total_size) {
            change_text = 'increase';
            destination_bar_colour = negative;
            difference_in_total_file_sizes = (destination_total_size - source_total_size)
        }
        source_total_size = Number(source_total_size)
        destination_total_size = Number(destination_total_size)

        totalChart.update({
            chart: {
                type: 'bar',
                width: null
            },
            title: {
                text: formatBytes(difference_in_total_file_sizes) + ' total ' + change_text + ' in file size'
            },
            colors: ['#555555', destination_bar_colour],
            tooltip: {
                formatter: function () {
                    return '<b>' + this.series.name + '</b><br/>' +
                        'File Size: ' + formatBytes(Math.abs(this.point.y));
                }
            },
        });
        let newSeriesData = [
            {
                name: 'After',
                data: [0, destination_total_size]
            },
            {
                name: 'Before',
                data: [source_total_size, 0]
            },
        ]
        for (let i = totalChart.series.length - 1; i >= 0; i--) {
            totalChart.series[i].remove();
        }
        for (let y = newSeriesData.length - 1; y >= 0; y--) {
            totalChart.addSeries(newSeriesData[y]);
        }
    };

    const fetchConversionDetails = function (taskId) {
        jQuery.get('conversionDetails/?task_id=' + taskId, function (data) {
            // Update/set the conversion details list
            let source_abspath = '';
            let destination_abspath = '';
            for (let i = 0; i < data.length; i++) {
                let item = data[i];
                if (item.type === 'source') {
                    source_file_size = Number(item.size);
                    source_abspath = item.abspath;
                } else if (item.type === 'destination') {
                    chart_title = item.basename;
                    destination_file_size = Number(item.size);
                    destination_abspath = item.abspath;
                }
            }
            updateIndividualChart();

            let html = 'Original File Path: "' + source_abspath + '"'
            html += '<br>'
            html += 'New File Path: "' + destination_abspath + '"'
            $('#selected_task_name').html(html)
        });
    };

    const fetchTotalFileSizeDetails = function () {
        jQuery.get('totalSizeChange', function (data) {
            // Update/set the conversion details list
            source_total_size = data.source;
            destination_total_size = data.destination;
            updateTotalChart();
        });
    };

    const watch = function () {
        let selectedTaskId = $('#selected_task_id');
        selectedTaskId.on("change", function () {
            if (this.value !== '') {
                fetchConversionDetails(this.value);
            }
        }).triggerHandler('change');
    }

    return {
        //main function to initiate the module
        init: function () {
            watch();
            fetchTotalFileSizeDetails();
        }
    };

}();

