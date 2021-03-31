#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
    example_library_management_file_test

    Docs:
        https://docs.unmanic.app/docs/plugins/writing_plugins/plugin_runner_types/

"""
import os


def on_library_management_file_test(data):
    """
    Runner function - enables additional actions during the library management file tests.

    The 'data' object argument includes:
        path                            - String containing the full path to the file being tested.
        issues                          - List of currently found issues for not processing the file.
        add_file_to_pending_tasks       - Boolean, is the file currently marked to be added to the queue for processing.

    :param data:
    :return:
    """

    # Get the file extension
    file_extension = os.path.splitext(data.get('path'))[-1][1:]

    # Ensure the file's extension is lowercase
    file_extension = file_extension.lower()

    # If this is flash video file, add it to pending tasks
    if file_extension.lower() in ['flv']:
        data['add_file_to_pending_tasks'] = True

    return data
