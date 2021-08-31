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
import shutil
from configparser import NoSectionError, NoOptionError

from unmanic.libs.directoryinfo import UnmanicDirectoryInfo
from unmanic.libs.unplugins.settings import PluginSettings

# Configure plugin logger
logger = logging.getLogger("Unmanic.Plugin.reject_files_larger_than_original")


class Settings(PluginSettings):
    settings = {
        'if_end_result_file_is_still_larger_mark_as_ignore': False,
    }
    form_settings = {
        "if_end_result_file_is_still_larger_mark_as_ignore": {
            "label": "If the final result is still larger than the original file, ignore this file in the future.",
        },
    }


def file_marked_as_failed(path):
    settings = Settings()
    if settings.get_setting('if_end_result_file_is_still_larger_mark_as_ignore'):
        directory_info = UnmanicDirectoryInfo(os.path.dirname(path))

        try:
            previously_failed = directory_info.get('reject_files_larger_than_original', os.path.basename(path))
        except NoSectionError as e:
            previously_failed = ''
        except NoOptionError as e:
            previously_failed = ''
        except Exception as e:
            logger.debug("Unknown exception {}.".format(e))
            previously_failed = ''

        if previously_failed:
            # This stream already has been attempted and failed
            return True

    # Default to...
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

    if file_marked_as_failed(abspath):
        # Mark this file to be added to the pending tasks
        data['add_file_to_pending_tasks'] = False
        logger.debug("File '{}' has been previously marked as failed.".format(abspath))

    return data


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
        data['exec_command'] = [
            'cp',
            '-fv',
            original_file_path,
            data.get('file_out')
        ]
        logger.debug(
            "Rejecting processed file as it is larger than the original: '{}' > '{}'.".format(abspath,
                                                                                              original_file_path))
    else:
        logger.debug("Keeping the processed file as it is smaller than the original.")

    return data


def on_postprocessor_file_movement(data):
    """
    Runner function - configures additional postprocessor file movements during the postprocessor stage of a task.

    The 'data' object argument includes:
        source_data             - Dictionary containing data pertaining to the original source file.
        remove_source_file      - Boolean, should Unmanic remove the original source file after all copy operations are complete.
        copy_file               - Boolean, should Unmanic run a copy operation with the returned data variables.
        file_in                 - The converted cache file to be copied by the postprocessor.
        file_out                - The destination file that the file will be copied to.

    :param data:
    :return:

    """
    settings = Settings()
    if settings.get_setting('if_end_result_file_is_still_larger_mark_as_ignore'):
        # Get the original file's absolute path
        original_source_path = data.get('source_data', {}).get('abspath')
        if not original_source_path:
            logger.error("Provided 'source_data' is missing the source file abspath data.")
            return data
        if not os.path.exists(original_source_path):
            logger.error("Original source path could not be found.")
            return data

        abspath = data.get('file_in')

        # Current cache file stats
        current_file_stats = os.stat(os.path.join(abspath))
        # Get the original file stats
        original_file_stats = os.stat(os.path.join(original_source_path))

        # Test that the source file is not smaller than the new file
        if int(current_file_stats.st_size) > int(original_file_stats.st_size):
            # The current file is larger than the original.
            # Mark it as failed
            directory_info = UnmanicDirectoryInfo(os.path.dirname(original_source_path))
            directory_info.set('reject_files_larger_than_original', os.path.basename(original_source_path), 'Ignoring')
            directory_info.save()
            logger.debug("Ignore on next scan written for '{}'.".format(original_source_path))
            # Copy the original file to the cache file
            # Do this rather than letting the Unmanic post-processor handle the copy.
            # This prevents a destination file from being recorded which would sku metrics if they were being recorded.
            shutil.copyfile(original_source_path, data.get('file_in'))
            logger.debug("Original file copied to replace cache file.")

    return data
