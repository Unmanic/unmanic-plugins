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
import filecmp
import logging
import os
import shutil
from configparser import NoSectionError, NoOptionError

from unmanic.libs.directoryinfo import UnmanicDirectoryInfo
from unmanic.libs.unplugins.settings import PluginSettings

# Configure plugin logger
logger = logging.getLogger("Unmanic.Plugin.reject_files_larger_than_original")


# TODO: Write config options in description
class Settings(PluginSettings):
    settings = {
        'fail_task_if_file_detected_larger':                 False,
        'if_end_result_file_is_still_larger_mark_as_ignore': False,
        'size_threshold_percent':                            0,
    }
    form_settings = {
        "fail_task_if_file_detected_larger":                 {
            "label": "Mark the task as failed",
        },
        "if_end_result_file_is_still_larger_mark_as_ignore": {
            "label": "Ignore files in future scans if end result is larger than source (regardless of task history)",
        },
        "size_threshold_percent":                            {
            "label":          "Size threshold",
            "input_type":     "slider",
            "slider_options": {
                "min":    -50,
                "max":    10,
                "step":   0.5,
                "suffix": "%",
            },
            "description":    "Shifts the size that a new file is rejected at, relative to the original file. "
                              "Leave at 0% to reject any file larger than the original. "
                              "Set a positive value to permit a small increase, for tasks that only rewrite the "
                              "container and can add a few bytes without re-encoding. "
                              "Set a negative value to demand a minimum saving, rejecting a transcode that did not "
                              "shrink the file by enough to be worth keeping.",
        },
    }


def get_size_threshold(settings):
    """Read the configured size threshold as a percentage of the original file size"""
    try:
        return float(settings.get_setting('size_threshold_percent'))
    except (TypeError, ValueError):
        return 0


def get_maximum_permitted_size(original_size, threshold):
    """
    Return the largest size that the new file may be before it is rejected

    A positive threshold permits the new file to be slightly larger than the original.
    Container level operations can add bytes without the video having been re-encoded
    (eg. an MP4 remux with '-movflags +faststart' relocating the moov atom, or a codec
    tag rewrite), and rejecting those over a handful of bytes reverts work that
    otherwise succeeded.

    A negative threshold demands a minimum saving, rejecting a new file that is smaller
    than the original but not by enough to be worth keeping.
    """
    return int(original_size) * (1 + (threshold / 100))


def describe_threshold(threshold):
    """Describe the size test in the terms that the configured threshold applies"""
    if threshold > 0:
        return "is more than {}% larger than the original file".format(threshold)
    if threshold < 0:
        return "is not at least {}% smaller than the original file".format(abs(threshold))
    return "is larger than the original file"


def file_marked_as_failed(settings, path):
    """Read directory info to check if file was previously marked as failed"""
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


def write_file_marked_as_failed(path):
    """Write entry to directory infor to mark this file as failed"""
    directory_info = UnmanicDirectoryInfo(os.path.dirname(path))
    directory_info.set('reject_files_larger_than_original', os.path.basename(path), 'Ignoring')
    directory_info.save()
    logger.debug("Ignore on next scan written for '{}'.".format(path))


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

    # Configure settings object
    settings = Settings(library_id=data.get('library_id'))

    if file_marked_as_failed(settings, abspath):
        # Ensure this file is not added to the pending tasks
        data['add_file_to_pending_tasks'] = False
        logger.debug("File '{}' has been previously marked as failed.".format(abspath))


def on_worker_process(data):
    """
    Runner function - enables additional configured processing jobs during the worker stages of a task.

    The 'data' object argument includes:
        library_id              - The library that the current task is associated with.
        exec_command            - A command that Unmanic should execute. Can be empty.
        command_progress_parser - A function that Unmanic can use to parse the STDOUT of the command to collect progress stats. Can be empty.
        file_in                 - The source file to be processed by the command.
        file_out                - The destination that the command should output (may be the same as the file_in if necessary).
        original_file_path      - The absolute path to the original file.
        repeat                  - Boolean, should this runner be executed again once completed with the same variables.

    :param data:
    :return:
    
    """
    # Default to no command required.
    data['exec_command'] = []
    data['repeat'] = False

    # Get the path to the file
    abspath = data.get('file_in')
    original_file_path = data.get('original_file_path')
    if not os.path.exists(abspath):
        logger.debug("File in '{}' does not exist.".format(abspath))

    if not os.path.exists(original_file_path):
        logger.debug("Original file '{}' does not exist.".format(original_file_path))

    # Configure settings object
    settings = Settings(library_id=data.get('library_id'))

    # Current cache file stats
    current_file_stats = os.stat(os.path.join(abspath))
    # Get the original file stats
    original_file_stats = os.stat(os.path.join(original_file_path))

    # Test that the source file is not smaller than the new file
    threshold = get_size_threshold(settings)
    maximum_permitted_size = get_maximum_permitted_size(original_file_stats.st_size, threshold)
    if int(current_file_stats.st_size) > maximum_permitted_size:
        if settings.get_setting('fail_task_if_file_detected_larger'):
            # Add some worker logs to be transparent as to what is happening
            if data.get('worker_log'):
                data['worker_log'].append(
                    "\nFailing task as current cache file {}:".format(describe_threshold(threshold)))
                data['worker_log'].append(
                    "\n  - Original File: {} bytes '<em>{}</em>'".format(original_file_stats.st_size,
                                                                         original_file_path))
                data['worker_log'].append(
                    "\n  - Cache File: {} bytes '<em>{}</em>'".format(current_file_stats.st_size, abspath))
            # Create a job that will exit falsy
            data['exec_command'] = ['false']
            if settings.get_setting('if_end_result_file_is_still_larger_mark_as_ignore'):
                # Write the failure file here because the post-processor file movement runner will not be executed
                # if the task fails
                write_file_marked_as_failed(original_file_path)
            # Return here because the rest does not matter
            return

        # Add some more worker logs...
        if data.get('worker_log'):
            data['worker_log'].append(
                "\nResetting task file back to original source as current cache file {}:".format(
                    describe_threshold(threshold)))
            data['worker_log'].append(
                "\n  - Original File: {} bytes '<em>{}</em>'".format(original_file_stats.st_size,
                                                                     original_file_path))
            data['worker_log'].append(
                "\n  - Cache File: {} bytes '<em>{}</em>'".format(current_file_stats.st_size, abspath))

        # The current file failed the size test. Reset the cache file to the 'file_in'
        data['file_in'] = original_file_path
        logger.debug(
            "Rejecting processed file as it {}: '{}' > '{}'.".format(describe_threshold(threshold), abspath,
                                                                      original_file_path))
    else:
        logger.debug("Keeping the processed file as it is within the permitted size.")


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
    # Configure settings object
    settings = Settings(library_id=data.get('library_id'))

    if settings.get_setting('if_end_result_file_is_still_larger_mark_as_ignore'):
        # Get the original file's absolute path
        original_source_path = data.get('source_data', {}).get('abspath')
        if not original_source_path:
            logger.error("Provided 'source_data' is missing the source file abspath data.")
            return
        if not os.path.exists(original_source_path):
            logger.error("Original source path could not be found.")
            return

        abspath = data.get('file_in')

        # Check if the file in and the original source file are the same
        if filecmp.cmp(original_source_path, abspath, shallow=True):
            logger.debug("Original file was unchanged.")
            # Mark it as to be ignored on the next scan
            write_file_marked_as_failed(original_source_path)
            return

        # Current cache file stats
        current_file_stats = os.stat(os.path.join(abspath))
        # Get the original file stats
        original_file_stats = os.stat(os.path.join(original_source_path))

        # Test that the source file is not smaller than the new file
        threshold = get_size_threshold(settings)
        maximum_permitted_size = get_maximum_permitted_size(original_file_stats.st_size, threshold)
        if int(current_file_stats.st_size) > maximum_permitted_size:
            # The current file failed the size test.
            # Mark it as failed
            write_file_marked_as_failed(original_source_path)
            if not filecmp.cmp(original_source_path, data.get('file_in'), shallow=True):
                # Copy the original file to the cache file
                # Do this rather than letting the Unmanic post-processor handle the copy.
                # This prevents a destination file from being recorded in history which would skew any metrics if
                # they were being recorded.
                shutil.copyfile(original_source_path, data.get('file_in'))
                logger.debug("Original file copied to replace cache file.")
