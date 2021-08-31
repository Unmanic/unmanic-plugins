#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
    unmanic-plugins.plugin.py

    Written by:               Josh.5 <jsunnex@gmail.com>
    Date:                     31 Aug 2021, (12:11 PM)

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
logger = logging.getLogger("Unmanic.Plugin.reject_files_larger_than_original")


class Settings(PluginSettings):
    settings = {}


def on_worker_process(data):
    """
    Runner function - enables additional configured processing jobs during the worker stages of a task.

    The 'data' object argument includes:
        exec_command            - A command that Unmanic should execute. Can be empty.
        command_progress_parser - A function that Unmanic can use to parse the STDOUT of the command to collect progress stats. Can be empty.
        file_in                 - The source file to be processed by the command.
        file_out                - The destination that the command should output (may be the same as the file_in if necessary).
        original_file_path      - The absolute path to the original file.
        repeat                  - Boolean, should this runner be executed again once completed with the same variables.

    :param data:
    :return:
    
    """
    # Default to no FFMPEG command required. This prevents the FFMPEG command from running if it is not required
    data['exec_command'] = []
    data['repeat'] = False

    # Get the path to the file
    abspath = data.get('file_in')
    original_file_path = data.get('original_file_path')
    if not os.path.exists(abspath):
        logger.debug("File in '{}' does not exist.".format(abspath))

    if not os.path.exists(original_file_path):
        logger.debug("Original file '{}' does not exist.".format(original_file_path))

    # Current cache file stats
    current_file_stats = os.stat(os.path.join(abspath))
    # Get the original file stats
    original_file_stats = os.stat(os.path.join(original_file_path))

    # Test that the source file is not smaller than the new file
    if int(current_file_stats.st_size) > int(original_file_stats.st_size):
        # The current file is larger than the original. Reset the cache file to the file in
        data['file_in'] = original_file_path
        logger.debug(
            "Rejecting processed file as it is larger than the original: '{}' > '{}'.".format(abspath,
                                                                                              original_file_path))

    return data
