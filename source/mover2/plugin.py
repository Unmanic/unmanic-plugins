#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
    Written by:               Josh.5 <jsunnex@gmail.com>
    Date:                     22 Aug 2021, (9:55 PM)

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

from unmanic.libs.unplugins.settings import PluginSettings

# Configure plugin logger
logger = logging.getLogger("Unmanic.Plugin.mover2")


class Settings(PluginSettings):
    settings = {
        "destination_directory":        "/library",
        "recreate_directory_structure": True,
        "remove_source_file":           False,
    }
    form_settings = {
        "destination_directory":        {
            "label":      "Destination directory",
            "input_type": "browse_directory",
        },
        "recreate_directory_structure": {
            "label": "Recreate directory structure",
        },
        "remove_source_file":           {
            "label": "Remove source files",
        },
    }


def all_parent_directories(head):
    dirs = []
    while True:
        head, tail = os.path.split(head)
        if tail != "":
            dirs[0:0] = [tail]
        else:
            # Dont bother appending the root to this path...
            break
    return dirs


def get_file_out(original_source_path, file_out):
    settings = Settings()

    # Get the destination directory
    destination_directory = settings.get_setting('destination_directory')

    # Is the plugin configured to recreate the directory structure?
    if settings.get_setting('recreate_directory_structure'):
        # Recreate the FULL directory path
        # Get the parent directory of the original file
        # Eg. /library/path/to/my/file.ext    =   /library/path/to/my
        original_source_dirname = os.path.dirname(original_source_path)

        # Fetch a list of all directories in the original directory path
        # Eg. directories = ['library', 'path', 'to', 'my']
        directories = all_parent_directories(original_source_dirname)

        # Append the directory structure to the destination directory
        destination_directory = os.path.join(destination_directory, *directories)

        # Ensure the destination directory structure exists. Create it if it does not
        if not os.path.exists(destination_directory):
            os.makedirs(destination_directory)

    # Get just the file name from of the output file
    file_out_basename = os.path.basename(file_out)

    # Return the output file
    return os.path.join(destination_directory, file_out_basename)


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

    # Get the original file's absolute path
    original_source_path = data.get('source_data', {}).get('abspath')
    if not original_source_path:
        logger.error("Provided 'source_data' is missing the source file abspath data.")
        return data

    unmanic_destination_file = data.get('file_out')

    # Should the plugin remove the source file?
    data['remove_source_file'] = settings.get_setting('remove_source_file')

    # Set the output file
    file_out = get_file_out(original_source_path, os.path.abspath(data.get('file_out')))
    data['file_out'] = file_out

    # Store some required data in a JSON file for the on_postprocessor_task_results runner.
    # If the source needs to be removed, then we will handle that with the other plugin runner. Notes below...
    # For now, save the current file_out (which is Unmanic's destination file once all plugins are run) to a file.
    # We also want to store a checksum of the cache file to ensure that the file movement was completed correctly.
    profile_directory = settings.get_profile_directory()
    # Use the basename of the source path to create a unique file for storing the file_out data.
    # This can then be read and used by the on_postprocessor_task_results function below.
    src_file_hash = hashlib.md5(original_source_path.encode('utf8')).hexdigest()
    plugin_data_file = os.path.join(profile_directory, '{}.json'.format(src_file_hash))
    with open(plugin_data_file, 'w') as f:
        required_data = {
            'file_out':                 file_out,
            'unmanic_destination_file': unmanic_destination_file,
        }
        json.dump(required_data, f, indent=4)

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
    settings = Settings()

    # Get the original file's absolute path
    original_source_path = data.get('source_data', {}).get('abspath')
    if not original_source_path:
        logger.error("Provided 'source_data' is missing the source file abspath data.")
        return data

    # Read the data from the on_postprocessor_file_movement runner
    profile_directory = settings.get_profile_directory()
    # Get the file out and store
    src_file_hash = hashlib.md5(original_source_path.encode('utf8')).hexdigest()
    plugin_data_file = os.path.join(profile_directory, '{}.json'.format(src_file_hash))
    if not os.path.exists(plugin_data_file):
        logger.error("Plugin data file is missing.")
        raise Exception("Plugin data file is missing.")
    with open(plugin_data_file) as infile:
        file_movement_data = json.load(infile)

    # Ensure the file was correctly moved as required
    if not data.get('file_move_processes_success'):
        # A plugin failed in its file movements. It may not have been this one... Check file
        if not file_movement_data.get('file_out') in data.get('destination_files'):
            # The file that this plugin requested that Unmanic move to does not exist in the 'destination_files' list
            # This means that the file did not successfully copy
            logger.error(
                "Detected that the file movement did not complete correctly. Dont do anything with the source file.")
            return data
    # If the above check was fine, then the file movement that this plugin requested was successful

    # If the source file and destination file are named the exact same thing (including extension), then the file
    #   may already be removed by setting 'remove_source_file' in the on_postprocessor_file_movement function.
    # However, if the file's name had changed at all, then the "source" file will have been replaced by the
    #   newly named file. Unmanic's default process is to replace the file with the processed one. This section
    #   ensures that these replaced files are cleaned up if the plugin is configured to remove the source files.
    if settings.get_setting('remove_source_file'):
        # Plugin configured to remove the source file.
        unmanic_destination_file = os.path.abspath(file_movement_data.get('unmanic_destination_file'))
        if os.path.exists(unmanic_destination_file):
            logger.debug("Plugin is configured to ensure the original file is removed. Removing file '{}'".format(
                unmanic_destination_file))
            os.remove(unmanic_destination_file)
        else:
            logger.debug("Plugin is configured to ensure the original file is removed. File has already been removed.")

    # Clean up plugin's data file
    os.remove(plugin_data_file)

    return data
