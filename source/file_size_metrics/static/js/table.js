var viewConversionDetails = function (jobId) {
    $('#selected_task_id').val(jobId).triggerHandler('change');
};

var CompletedTasksDatatable = function () {

    var recordName = function (task_label) {
        return '<span class="wrap"> ' + task_label + ' </span>';
    };
    var recordSuccessStatus = function (task_success) {
        var html = '';
        if (task_success) {
            html = '<span class="label label-sm label-success"> Success </span>';
        } else {
            html = '<span class="label label-sm label-danger"> Failed </span>';
        }
        return html;
    };
    var recordActionButton = function (data) {
        var row_id = data.id;
        return '<a class="view-btn" ' +
            'onclick="viewConversionDetails(' + $.trim(row_id) + ');"> View details &#x25B2;\n' +
            '</a>';
    };

    var buildTable = function () {
        $('#history_completed_tasks_table').DataTable({
            processing: true,
            serverSide: true,
            ajax: {
                url: "list/", // ajax source
                type: "GET", // request type
                data: function (data) {
                    return {
                        data: JSON.stringify(data)
                    }
                }
            },
            columnDefs: [
                {
                    targets: 0,
                    title: "New File Name",
                    className: "basename",
                    name: "basename",
                    data: "basename",
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
                {
                    targets: 3,
                    title: "Status",
                    name: "task_success",
                    data: "task_success",
                    render: recordSuccessStatus,
                },
                {
                    targets: 4,
                    title: "View Details",
                    data: null,
                    searchable: false,
                    orderable: false,
                    mRender: recordActionButton,
                },
            ],

            lengthMenu: [
                [7, 10, 20, 50, 100, 500],
                [7, 10, 20, 50, 100, 500] // change per page values here
            ],
            pageLength: 7, // default record count per page
            order: [
                [2, "desc"]
            ]

        });
    };

    return {
        //main function to initiate the module
        init: function () {
            buildTable();
        }

    };

}();
