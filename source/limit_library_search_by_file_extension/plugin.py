#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
    unmanic-plugins.plugin.py

    Written by:               Josh.5 <jsunnex@gmail.com>
    Date:                     23 Jun 2021, (23:09 PM)

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
logger = logging.getLogger("Unmanic.Plugin.limit_library_search_by_file_extension")


class Settings(PluginSettings):
    settings = {
        "allowed_extensions": ''
    }
    form_settings = {
        "allowed_extensions": {
            "label": "Search library only for extensions",
        },
    }


def file_ends_in_allowed_extensions(path, allowed_extensions):
    """
    Check if the file is in the allowed search extensions

    :return:
    """
    # Get the file extension
    file_extension = os.path.splitext(path)[-1][1:]

    # Ensure the file's extension is lowercase
    file_extension = file_extension.lower()

    # If the config is empty (not yet configured) ignore everything
    if not allowed_extensions:
        logger.debug("Plugin has not yet been configured with a list of file extensions to allow. Blocking everything.")
        return False

    # Check if it ends with one of the allowed search extensions
    if file_extension in allowed_extensions:
        return True

    logger.debug("File '{}' does not end in the specified file extensions '{}'.".format(path, allowed_extensions))
    return False


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
    # Get the path to the file
    abspath = data.get('path')

    # Get the list of configured extensions to search for
    settings = Settings()
    allowed_extensions = settings.get_setting('allowed_extensions')

    if not file_ends_in_allowed_extensions(abspath, allowed_extensions):
        # Ignore this file
        data['add_file_to_pending_tasks'] = False

    return data
