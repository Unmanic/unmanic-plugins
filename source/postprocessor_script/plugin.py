#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
    unmanic-plugins.plugin.py

    Written by:               Josh.5 <jsunnex@gmail.com>
    Date:                     03 Jul 2021, (10:07 PM)

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
import subprocess

from unmanic.libs.unplugins.settings import PluginSettings

# Configure plugin logger
logger = logging.getLogger("Unmanic.Plugin.postprocessor_script")


class Settings(PluginSettings):
    settings = {
        'only_on_task_processing_success': False,
        'run_for_each_destination_file':   False,
        'cmd':                             '',
        'args':                            '',
    }
    form_settings = {
        "only_on_task_processing_success": {
            "label": "Only run the command when the all worker processes completed successfully.",
        },
        "run_for_each_destination_file":   {
            "label": "Run the command for each output file created by Unmanic.",
        },
        "cmd":                             {
            "label": "Command or script to execute.",
        },
        "args":                            {
            "label":      "Arguments to pass to the command or script. ",
            "input_type": "textarea",
        },
    }


class DefaultMissingKeys(dict):
    def __missing__(self, key):
        return "{%s}" % key


def exec_subprocess(cmd, args):
    """
    Execute a subprocess command

    :param cmd:
    :param args:
    :return:
    """
    full_command = "{} {}".format(cmd, args)
    if full_command.strip():
        logger.debug("Executing command: '{}'.".format(full_command))

        # Execute command
        process = subprocess.Popen(full_command, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                                   universal_newlines=True, errors='replace', shell=True)

        # Poll process for new output until finished
        while True:
            line_text = process.stdout.readline()
            logger.debug(line_text)
            if line_text == '' and process.poll() is not None:
                break

        # Get the final output and the exit status
        var = process.communicate()[0]
        if process.returncode == 0:
            return True
        else:
            raise Exception("Failed to execute command: '{}'".format(full_command))


def on_postprocessor_task_results(data):
    """
    Runner function - provides a means for additional postprocessor functions based on the task success.

    The 'data' object argument includes:
        task_processing_success         - Boolean, did all task processes complete successfully.
        file_move_processes_success     - Boolean, did all postprocessor movement tasks complete successfully.
        destination_files               - List containing all file paths created by postprocessor file movements.
        source_data                     - Dictionary containing data pertaining to the original source file.

    :param data:
    :return:

    """
    # Fetch the configured command and settings
    settings = Settings()

    if settings.get_setting('only_on_task_processing_success'):
        # Ensure all worker task processes completed successfully
        if not data.get('task_processing_success'):
            # The worker task processes did not complete successfully
            return data

    cmd = settings.get_setting('cmd')
    args = settings.get_setting('args')
    run_for_each_destination_file = settings.get_setting('run_for_each_destination_file')

    # Remove any line-breaks in args
    args = args.replace('\n', ' ').replace('\r', '')

    # Map variables to be replaced in cmd and args
    variable_map = {
        'source_file_path': data.get('source_data', {}).get('abspath'),
        'source_file_size': data.get('source_data', {}).get('size'),
    }

    # If this is to be run for each file in the destination files, loop over the 'destination_files' list;
    # Otherwise Just run the command once.
    if run_for_each_destination_file:
        for destination_file in data.get('destination_files'):
            # Set the single destination file to the 'output_file_path' mapped variable
            variable_map['output_file_path'] = "{}".format(destination_file)

            # Substitute all variables in the cmd and args strings
            cmd = cmd.format_map(DefaultMissingKeys(variable_map))
            args = args.format_map(DefaultMissingKeys(variable_map))

            exec_subprocess(cmd, args)
    else:
        # Set the 'output_files' mapped variable to a JSON dumped object of the 'destination_files' list
        variable_map['output_files'] = "{}".format(json.dumps(data.get('destination_files', [])))

        # Substitute all variables in the cmd and args strings
        cmd = cmd.format_map(DefaultMissingKeys(variable_map))
        args = args.format_map(DefaultMissingKeys(variable_map))

        exec_subprocess(cmd, args)

    return data
