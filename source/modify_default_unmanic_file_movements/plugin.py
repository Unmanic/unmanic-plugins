#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
    unmanic-plugins.plugin.py

    Written by:               Josh.5 <jsunnex@gmail.com>
    Date:                     10 Sep 2021, (10:07 PM)

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
import json
import logging
import os

from unmanic.libs import common
from unmanic.libs.unplugins.settings import PluginSettings

# Configure plugin logger
logger = logging.getLogger("Unmanic.Plugin.modify_default_unmanic_file_movements")


class Settings(PluginSettings):
    settings = {}

    def __init__(self, *args, **kwargs):
        super(Settings, self).__init__(*args, **kwargs)
        self.settings = {
            "disable_same_source_copy_to_cache": False,
            "disable_unmanic_default_file_copy": False,
            "disable_removing_source_file":      False,
        }
        self.form_settings = {
            "disable_same_source_copy_to_cache": {
                "label":       "Disable creating a cache copy if source files if missing (Worker - Processing file)",
                "description": "By default, Unmanic will create a cache copy if no plugins were run against a file.\n"
                               "This would then allow for any post-processing functions to continue as normal,\n"
                               "even when the worker plugins did nothing.\n"
                               "Enable this option to create a dummy cache file and prevent Unmanic from carrying out\n"
                               "this action.\n"
                               "Note: This requires that the plugin is setup to run last in the worker process stack.\n"
                               "Note2: This may prevent some post-processor plugins from being able to run.",
            },
            "disable_unmanic_default_file_copy": {
                "label":       "Disable the default file copy (Post-processor - File movements)",
                "description": "By default, Unmanic will copy the final cache file back to the source directory.\n"
                               "Enabling this option will prevent that from happening.",
            },
            "disable_removing_source_file":      {
                "label":       "Disable the removal of the original source files (Post-processor - File movements)",
                "description": "Enable this option to prevent Unmanic from removing the source file during post-processing.",
            },
        }


def on_worker_process(data):
    """
    Runner function - enables additional configured processing jobs during the worker stages of a task.

    The 'data' object argument includes:
        worker_log              - Array, the log lines that are being tailed by the frontend. Can be left empty.
        library_id              - Number, the library that the current task is associated with.
        exec_command            - Array, a subprocess command that Unmanic should execute. Can be empty.
        command_progress_parser - Function, a function that Unmanic can use to parse the STDOUT of the command to collect progress stats. Can be empty.
        file_in                 - String, the source file to be processed by the command.
        file_out                - String, the destination that the command should output (may be the same as the file_in if necessary).
        original_file_path      - String, the absolute path to the original file.
        repeat                  - Boolean, should this runner be executed again once completed with the same variables.

    :param data:
    :return:

    """
    # Configure settings object
    settings = Settings(library_id=data.get('library_id'))
    dump_data = {
        'success': True
    }

    # Create the cache directory if it does not yet exist
    cache_directory = os.path.dirname(data.get('file_out'))
    if not os.path.isdir(cache_directory):
        os.makedirs(cache_directory)

    if settings.get_setting('disable_same_source_copy_to_cache'):
        # Check if the current out file is the same as the original file
        if os.path.abspath(data.get('file_in')) == os.path.abspath(data.get('original_file_path')):
            # Set the file out to a dummy file to prevent a cache copy being created
            data['file_out'] = os.path.join(cache_directory, 'modify_default_unmanic_file_movements.dummy')
            common.touch(data['file_out'])
            dump_data['dummy_out'] = True

    config_data = os.path.join(cache_directory, 'modify_default_unmanic_file_movements.json')
    with open(config_data, 'w') as f:
        json.dump(dump_data, f, indent=4)


def on_postprocessor_file_movement(data):
    """
    Runner function - configures additional postprocessor file movements during the postprocessor stage of a task.

    The 'data' object argument includes:
        library_id              - Integer, the library that the current task is associated with.
        source_data             - Dictionary, data pertaining to the original source file.
        remove_source_file      - Boolean, should Unmanic remove the original source file after all copy operations are complete. (default: 'True' if file name has changed)
        copy_file               - Boolean, should Unmanic run a copy operation with the returned data variables. (default: 'False')
        file_in                 - String, the converted cache file to be copied by the postprocessor.
        file_out                - String, the destination file that the file will be copied to.
        run_default_file_copy   - Boolean, should Unmanic run the default post-process file movement. (default: 'True')

    :param data:
    :return:
    
    """
    settings = Settings(library_id=data.get('library_id'))
    dump_data = {}

    # Load worker data
    config_data = os.path.join(os.path.dirname(data.get('file_in')), 'modify_default_unmanic_file_movements.json')
    if os.path.exists(config_data):
        with open(config_data) as f:
            dump_data = json.load(f)

    # Should the plugin disable the default file copy function
    if dump_data.get('dummy_out'):
        # Disable the default file copy if the final cache file is a dummy file
        data['run_default_file_copy'] = False
    elif settings.get_setting('disable_unmanic_default_file_copy'):
        # Disable the default file copy if configured
        data['run_default_file_copy'] = False

    # Should the plugin disable the removal of the source file?
    if settings.get_setting('disable_removing_source_file'):
        # Disable removal of source file if configured
        data['remove_source_file'] = False
