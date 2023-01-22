#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
    example_postprocessor_task_results

    Docs:
        https://docs.unmanic.app/docs/plugins/writing_plugins/plugin_runner_types/#post-processor---marking-task-successfailure

"""
import requests


def notify(source_data):
    url = 'https://ptsv2.com/t/bbhvl-1617098134/post'
    result = requests.post(url, json=source_data)
    # print(result.text)


def on_postprocessor_task_results(data):
    """
    Runner function - provides a means for additional postprocessor functions based on the task success.

    The 'data' object argument includes:
        task_processing_success         - Boolean, did all task processes complete successfully.
        file_move_processes_success     - Boolean, did all postprocessor movement tasks complete successfully.
        destination_files               - List containing all file paths created by postprocessor file movements.
        source_data                     - Dictionary containing data pertaining to the original source file.

    :param data:
    :return:
    """
    if data.get('task_processing_success') and data.get('file_move_processes_success'):
        notify(data.get('source_data'))

    return data
