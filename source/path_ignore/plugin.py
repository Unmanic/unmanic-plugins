#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
    Written by:               Josh.5 <jsunnex@gmail.com>
    Date:                     8 May 2021, (11:32 PM)
 
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
import re

from unmanic.libs.unplugins.settings import PluginSettings


class Settings(PluginSettings):
    settings = {
        "patterns": "",
    }

    form_settings = {
        "patterns": {
            "input_type": "textarea",
            "label":      "Patterns"
        }
    }


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

    regex_patterns = settings.get_setting('patterns')

    file_path = data.get('path')
    for regex_pattern in regex_patterns.splitlines():
        if not regex_pattern:
            continue

        pattern = re.compile(regex_pattern)
        if pattern.search(file_path):
            # Found a match
            data['add_file_to_pending_tasks'] = False
            data['issues'].append({
                'id':      'Path Ignore',
                'message': "File should be ignored because path '{}' matches the configured regex '{}'".format(
                    file_path, regex_pattern),
            })

    return data
