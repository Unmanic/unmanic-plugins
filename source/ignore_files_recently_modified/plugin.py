#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
    unmanic-plugins.plugin.py

    Written by:               Josh.5 <jsunnex@gmail.com>
    Date:                     31 Aug 2021, (23:09 PM)

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
import time

import humanfriendly
from unmanic.libs.unplugins.settings import PluginSettings

# Configure plugin logger
logger = logging.getLogger("Unmanic.Plugin.ignore_files_recently_modified")


class Settings(PluginSettings):
    settings = {
        "min_ctime": '1min'
    }
    form_settings = {
        "min_ctime": {
            "label": "Time since last modified",
        },
    }


def ensure_last_modified_time_on_file(path, minimum_age):
    # get the file stats
    file_stats = os.stat(os.path.join(path))

    # Get the required timestamp calculated from the configured value
    current_timestamp = time.time()
    minimum_required_timestamp = (int(current_timestamp) - int(humanfriendly.parse_timespan(minimum_age)))

    # If the file's modification timestamp is more recent than the minimum required timestamp, ignore the file.
    if minimum_required_timestamp < int(file_stats.st_ctime):
        return False
    return True


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
    settings = Settings()
    minimum_age = settings.get_setting('min_ctime')

    if not ensure_last_modified_time_on_file(data.get('path'), minimum_age):
        # Ignore this file
        data['add_file_to_pending_tasks'] = False
        logger.debug("File found to be newer than the minimum ignore time of '{}'. Ignoring!".format(minimum_age))

    return data
