#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
    unmanic-plugins.plugin.py

    Written by:               Josh.5 <jsunnex@gmail.com>
    Date:                     04 Sep 2021, (10:47 PM)

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

import humanfriendly
from unmanic.libs.unplugins.settings import PluginSettings

# Configure plugin logger
logger = logging.getLogger("Unmanic.Plugin.ignore_over_size")


class Settings(PluginSettings):
    settings = {
        "max_file_size": '0'
    }
    form_settings = {
        "max_file_size": {
            "label": "Maximum file size",
        },
    }


def check_file_size_over_max_file_size(path, max_file_size):
    file_stats = os.stat(os.path.join(path))
    if int(humanfriendly.parse_size(max_file_size)) > int(file_stats.st_size):
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
    max_file_size = settings.get_setting('max_file_size')

    if check_file_size_over_max_file_size(data.get('path'), max_file_size):
        # Ignore this file
        data['add_file_to_pending_tasks'] = False
        data['issues'].append({
            'id':      'Ignore files by size on disk',
            'message': "File '{}' should ignored because it is over the configured maximum size '{}'.".format(
                data.get('path'), max_file_size),
        })

    return data
