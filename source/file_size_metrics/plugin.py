#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
    Written by:               Josh.5 <jsunnex@gmail.com>
    Date:                     25 April 2021, (3:41 AM)

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
import hashlib
import json
import logging
import os
import uuid

from unmanic.libs.unplugins.settings import PluginSettings

from file_size_metrics.lib.history import Data

# Configure plugin logger
logger = logging.getLogger("Unmanic.Plugin.file_size_metrics")


class Settings(PluginSettings):
    settings = {}


def get_historical_data(data):
    results = []
    arguments = data.get('arguments')
    request_body = arguments.get('data', [])
    if request_body:
        request_dict = json.loads(request_body[0])

        settings = Settings()
        data = Data(settings, logger)

        # Return a list of historical tasks based on the request JSON body
        results = data.prepare_filtered_historic_tasks(request_dict)

        data.close()

    return json.dumps(results, indent=2)


def get_historical_data_details(data):
    results = []
    arguments = data.get('arguments')
    task_id = arguments.get('task_id', [])
    if task_id:
        settings = Settings()
        data = Data(settings, logger)

        # Return a list of historical tasks based on the request JSON body
        results = data.get_history_probe_data(task_id)

        data.close()

    return json.dumps(results, indent=2)


def get_total_size_change_data_details(data):
    settings = Settings()
    data = Data(settings, logger)

    # Return a list of historical tasks based on the request JSON body
    results = data.calculate_total_file_size_difference()

    data.close()

    return json.dumps(results, indent=2)


def save_source_size(abspath, size):
    settings = Settings()
    data = Data(settings, logger)

    # Return a list of historical tasks based on the request JSON body
    task_id = data.save_source_item(abspath, size)

    data.close()

    if task_id is None:
        return False

    # Store
    profile_directory = settings.get_profile_directory()
    # Use the basename of the source path to create a unique file for storing the file_out data.
    # This can then be read and used by the on_postprocessor_task_results function below.
    src_file_hash = hashlib.md5(abspath.encode('utf8')).hexdigest()
    plugin_data_file = os.path.join(profile_directory, '{}.json'.format(src_file_hash))
    with open(plugin_data_file, 'w') as f:
        required_data = {
            'db_id': task_id,
        }
        json.dump(required_data, f, indent=4)

    return True


def save_destination_size(task_id, abspath, size):
    settings = Settings()
    data = Data(settings, logger)

    # Return a list of historical tasks based on the request JSON body
    success = data.save_destination_item(task_id, abspath, size)

    data.close()

    return success


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
    # Get the path to the file
    abspath = data.get('original_file_path')
    source_size = os.path.getsize(abspath)
    if not save_source_size(abspath, source_size):
        logger.error("Failed to create source size entry for this file")

    return data


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
    # Get the original file's absolute path
    original_source_path = data.get('source_data', {}).get('abspath')
    if not original_source_path:
        logger.error("Provided 'source_data' is missing the source file abspath data.")
        return data

    # Read the data from the on_postprocessor_file_movement runner
    settings = Settings()
    profile_directory = settings.get_profile_directory()
    # Get the file out and store
    src_file_hash = hashlib.md5(original_source_path.encode('utf8')).hexdigest()
    plugin_data_file = os.path.join(profile_directory, '{}.json'.format(src_file_hash))
    if not os.path.exists(plugin_data_file):
        logger.error("Plugin data file is missing.")
        raise Exception("Plugin data file is missing.")
    with open(plugin_data_file) as infile:
        task_metadata = json.load(infile)

    # Ensure the file was correctly moved as required
    for dest_file in data.get('destination_files', []):
        abspath = os.path.abspath(dest_file)
        # Add a destination file entry if the file actually exists
        if os.path.exists(abspath):
            task_id = task_metadata.get('db_id')
            size = os.path.getsize(abspath)
            save_destination_size(task_id, abspath, size)
        else:
            logger.info("Skipping file '{}' as it does not exist.".format(abspath))

    # Clean up plugin's data file
    os.remove(plugin_data_file)

    return data


def render_frontend_panel(data):
    if data.get('path') in ['list', '/list', '/list/', '/list/']:
        data['content_type'] = 'application/json'
        data['content'] = get_historical_data(data)
        return

    if data.get('path') in ['conversionDetails', '/conversionDetails', '/conversionDetails/', '/conversionDetails/']:
        data['content_type'] = 'application/json'
        data['content'] = get_historical_data_details(data)
        return

    if data.get('path') in ['totalSizeChange', '/totalSizeChange', '/totalSizeChange/', '/totalSizeChange/']:
        data['content_type'] = 'application/json'
        data['content'] = get_total_size_change_data_details(data)
        return

    with open(os.path.abspath(os.path.join(os.path.dirname(__file__), 'static', 'index.html'))) as f:
        content = f.read()
        data['content'] = content.replace("{cache_buster}", str(uuid.uuid4()))

    return data
