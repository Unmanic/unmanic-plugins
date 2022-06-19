#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
    plugins.plugin.py

    Written by:               Josh.5 <jsunnex@gmail.com>
    Date:                     19 June 2022, (5:31 PM)

    Copyright:
        Copyright (C) 2021 Josh Sunnex

        This program is free software: you can redistribute it and/or modify it under the terms of the GNU General
        Public License as published by the Free Software Foundation, version 3.

        This program is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the
        implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License
        for more details.

        You should have received a copy of the GNU General Public License along with this program.
        If not, see <https://www.gnu.org/licenses/>.

"""

import logging
import os

from unmanic.libs.unplugins.settings import PluginSettings

# Configure plugin logger
logger = logging.getLogger("Unmanic.Plugin.ignore_completed_tasks")


class Settings(PluginSettings):
    settings = {
        "allowed_extensions": ''
    }
    form_settings = {
        "allowed_extensions": {
            "label":       "Apply filter only to specified file extensions",
            "description": "Speed up the library scan by only checking files with matching file extensions.\n"
                           "Leaving this blank will do a DB lookup against every file scanned to check if it "
                           "is in the completed task list.",
        },
    }

    def __init__(self, *args, **kwargs):
        super(Settings, self).__init__(*args, **kwargs)


def file_ends_in_allowed_extensions(abspath, allowed_extensions):
    """
    Check if the file is in the allowed search extensions

    :param abspath:
    :param allowed_extensions:
    :return:
    """
    """
    Check if the file is in the allowed search extensions

    :return:
    """
    # Get the file extension
    file_extension = os.path.splitext(abspath)[-1][1:]
    # Ensure the file's extension is lowercase
    file_extension = file_extension.lower()
    # If the config is empty (not yet configured) ignore everything
    if not allowed_extensions:
        logger.debug("Plugin has not been configured with a list of file extensions to allow. Testing everything.")
        return True
    # Check if it ends with one of the allowed search extensions
    if file_extension in allowed_extensions:
        return True
    logger.debug("File '{}' does not end in the specified file extensions '{}'.".format(abspath, allowed_extensions))
    return False


def file_exists_in_completed_tasks(abspath):
    """
    Check if the file path exists in the completed task list.
    This check is regardless of if the file was previously completed successfully or not

    :param abspath:
    :return:
    """
    # Fetch historical tasks
    from unmanic.libs import history
    history_logging = history.History()
    failed_tasks = history_logging.get_historic_tasks_list_with_source_probe(task_success=None, abspath=abspath)
    # Check if any historic tasks were found
    if failed_tasks.count() > 0:
        return True
    return False


def on_library_management_file_test(data):
    """
    Runner function - enables additional actions during the library management file tests.

    The 'data' object argument includes:
        library_id                      - The library that the current task is associated with
        path                            - String containing the full path to the file being tested.
        issues                          - List of currently found issues for not processing the file.
        add_file_to_pending_tasks       - Boolean, is the file currently marked to be added to the queue for processing.
        priority_score                  - Integer, an additional score that can be added to set the position of the new task in the task queue.
        shared_info                     - Dictionary, information provided by previous plugin runners. This can be appended to for subsequent runners.

    :param data:
    :return:
    
    """
    # Get the path to the file
    abspath = data.get('path')

    # Configure settings object (maintain compatibility with v1 plugins)
    settings = Settings(library_id=data.get('library_id'))

    # Get the list of configured extensions to search for
    allowed_extensions = settings.get_setting('allowed_extensions')

    # Check if file ends with the specified file extensions (if blank then all files will be tested)
    if not file_ends_in_allowed_extensions(abspath, allowed_extensions):
        # Ignore this file
        data['add_file_to_pending_tasks'] = False
        return

    # Check if file exists already in the completed tasks list (successfully or not)
    if file_exists_in_completed_tasks(abspath):
        data['add_file_to_pending_tasks'] = False
