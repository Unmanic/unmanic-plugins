#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
    plugins.__init__.py

    Written by:               Josh.5 <jsunnex@gmail.com>
    Date:                     26 Oct 2021, (9:04 AM)

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
import mimetypes
import os
import shutil
from configparser import NoSectionError, NoOptionError

from unmanic.libs.directoryinfo import UnmanicDirectoryInfo
from unmanic.libs.unplugins.settings import PluginSettings

# Configure plugin logger
logger = logging.getLogger("Unmanic.Plugin.sickbeard_mp4_automator")


class Settings(PluginSettings):

    def __init__(self):
        self.settings = {
            'limit_to_extensions':         False,
            "allowed_extensions":          'mkv,avi,mov,ts,rmvb,mp4',
            "only_run_for_ffmpeg_command": True,
            "process_file_with_hardlink":  False,
            'config':                      self.__read_default_config(),
        }
        self.form_settings = {
            "limit_to_extensions":         {
                "label": "Only run when the original source file matches specified extensions",
            },
            "allowed_extensions":          self.__set_allowed_extensions_form_settings(),
            "only_run_for_ffmpeg_command": {
                "label": "Only run against items that require FFmpeg processing",
            },
            "process_file_with_hardlink":  {
                "label": "Attempt to use Hardlinks when processing the file rather than copying",
            },
            "config":                      {
                "label":      "SMA configuration",
                "input_type": "textarea",
            },
        }

    def __read_default_config(self):
        config_file = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'default.ini')
        with open(config_file) as f:
            config = f.read()
        return config

    def __set_allowed_extensions_form_settings(self):
        values = {
            "label": "Comma separated list of file extensions",
        }
        if not self.get_setting('limit_to_extensions'):
            values["display"] = 'hidden'
        return values


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


def test_valid_mimetype(file_path):
    """
    Test the given file path for its mimetype.
    If the mimetype cannot be detected, it will fail this test.
    If the detected mimetype is not in the configured 'allowed_mimetypes'
        class variable, it will fail this test.

    :param file_path:
    :return:
    """
    # Only run this check against video/audio/image MIME types
    mimetypes.init()
    file_type = mimetypes.guess_type(file_path)[0]

    # Add any missing mimetypes here
    mimetypes.add_type('video/x-m4v', '.m4v')

    # If the file has no MIME type then it cannot be tested
    if file_type is None:
        logger.debug("Unable to fetch file MIME type - '{}'".format(file_path))
        return False

    # Make sure the MIME type is either audio, video or image
    file_type_category = file_type.split('/')[0]
    if file_type_category not in ['video']:
        logger.debug("File MIME type not 'video' - '{}'".format(file_path))
        return False

    return True


def get_file_size(path):
    file_stats = os.stat(os.path.join(path))
    return int(file_stats.st_size)


def file_already_processed(path):
    directory_info = UnmanicDirectoryInfo(os.path.dirname(path))

    try:
        previous_file_size = directory_info.get('sickbeard_mp4_automator', os.path.basename(path))
    except NoSectionError:
        previous_file_size = '0'
    except NoOptionError:
        previous_file_size = '0'
    except Exception as e:
        logger.debug("Unknown exception {}.".format(e))
        previous_file_size = '0'

    # get the checksum of the current file
    file_size = get_file_size(path)

    if int(previous_file_size) == int(file_size):
        logger.debug("File size has not change since previously processed with SMA script - '{}'".format(path))
        # This file already has been processed
        return True

    # Default to...
    return False


def file_requires_processing_by_ffmpeg(abspath):
    import re
    import subprocess

    # Build sma command args
    cmd = build_worker_args(abspath)
    cmd += ['--optionsonly']

    # Exec command
    proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    stdout, stderr = proc.communicate()

    # Parse json output
    raw_output = stdout.decode("utf-8")
    pattern = re.compile('\n{\n(.|\n)*$')
    matches = re.search(pattern, raw_output)
    info = json.loads(matches.group(0))

    # If there is no ffmpeg command created, then SMA will not be transcoding this file
    #   (metadata tagging may still happen)
    if info.get('ffmpeg_commands'):
        logger.debug("SMA has found that this file needs processing - '{}'".format(abspath))
        return True

    return False


def generate_mock_path(original_file_path, input_file_path, output_file_path):
    """
    Generate mock path which will be used

    This will:
        EITHER: Move current cache file to this new cache directory
        OR: Copy file from the source directory to this new cache file directory
    It will then find and copy in all files in the original source directory that are smaller than 10MB

    :param original_file_path:
    :param input_file_path:
    :param output_file_path:
    :return:
    """
    settings = Settings()

    # Set the Unmanic working cache path
    cache_path = os.path.dirname(os.path.abspath(output_file_path))

    # From the original file, fetch the source parent directory
    src_directory_name = os.path.basename(os.path.dirname(os.path.abspath(original_file_path)))

    # Inside this working cache path, set the temp mock path
    mock_cache_path = os.path.join(cache_path, src_directory_name)

    # Ensure this path exists
    if not os.path.exists(mock_cache_path):
        os.makedirs(mock_cache_path)

    # Move the input file into this mock directory
    # Looks like we need to do this because the subtitle feature will not work without proper naming
    output_file_name = os.path.splitext(os.path.basename(original_file_path))[0]
    file_extension = os.path.splitext(input_file_path)[1].lstrip('.')
    new_file_out = "{}.{}".format(output_file_name, file_extension)
    cached_copy = os.path.join(mock_cache_path, new_file_out)
    if os.path.abspath(input_file_path) == os.path.abspath(original_file_path):
        # If the input file is not a cache file (it is the original file), first create a copy
        if settings.get_setting('process_file_with_hardlink'):
            try:
                os.link(input_file_path, cached_copy)
            except OSError:
                shutil.copyfile(input_file_path, cached_copy)
        else:
            shutil.copyfile(input_file_path, cached_copy)
    else:
        # If the file is a cached file, just move it
        shutil.move(input_file_path, cached_copy)

    # Find and add all subtitle files
    original_file_parent_directory = os.path.dirname(os.path.abspath(original_file_path))
    for file in os.listdir(original_file_parent_directory):
        if not os.path.isfile(os.path.join(original_file_parent_directory, file)):
            continue
        file_size = get_file_size(os.path.join(original_file_parent_directory, file))
        # Copy in any file under 10Mb
        if file_size < 10000000:
            shutil.copyfile(os.path.join(original_file_parent_directory, file), os.path.join(mock_cache_path, file))

    # Return the cached copy created here
    return cached_copy


def sma_config_file():
    # Set config file path
    settings = Settings()
    profile_directory = settings.get_profile_directory()

    # Set the output file
    config = settings.get_setting('config')
    if not config:
        logger.error("Plugin not configured.")

    # Write comskip settings file
    sma_config_file = os.path.join(profile_directory, 'autoProcess.ini')
    with open(sma_config_file, "w") as f:
        f.write(config)
        # Ensure the end of the file has a linebreak
        f.write("\n\n")

    return sma_config_file


def predict_file_out(mock_file_in):
    """
    Predict the SMA script file output.

    The SMA script will potentially remux the file.
    If it does, we will need to predict what it will be remuxed to from the config.

    :param mock_file_in:
    :return:
    """
    # Set config file path
    settings = Settings()
    # Get the output file
    config = settings.get_setting('config')
    if not config:
        logger.error("Plugin not configured.")

    # Get the extension to be configured in the config file (use the current file extension)
    file_name = os.path.splitext(mock_file_in)[0]
    extension = os.path.splitext(mock_file_in)[1].lstrip('.')
    for line in config.split('\n'):
        if line.startswith('output-extension'):
            extension = line.split('=')[1].strip()
    return "{}.{}".format(file_name, extension)


def build_worker_args(abspath):
    config_file = sma_config_file()
    plugin_dir = os.path.dirname(os.path.realpath(__file__))
    sma_manual_script_path = os.path.join(plugin_dir, 'dep', 'sickbeard_mp4_automator', 'manual.py')
    return [
        'python3',
        sma_manual_script_path,
        '--config', config_file,
        '--input', abspath,
        '--auto',
        '--nopost',
        '--nodelete',
    ]


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
    original_file_path = data.get('path')

    # Ensure this is a video file
    if not test_valid_mimetype(original_file_path):
        return data

    # Limit to configured file extensions
    settings = Settings()
    if settings.get_setting('limit_to_extensions'):
        allowed_extensions = settings.get_setting('allowed_extensions')
        if not file_ends_in_allowed_extensions(original_file_path, allowed_extensions):
            return data

    # If the file requires processing (remux, transcode, etc) with ffmpeg, then add it to the list
    if file_requires_processing_by_ffmpeg(original_file_path):
        # Mark this file to be added to the pending tasks
        data['add_file_to_pending_tasks'] = True
        logger.debug(
            "File needs processing with FFmpeg '{}'. It should be added to task list.".format(original_file_path))
        return data

    # If metadata tags, QTFastStart, etc are not a requirement for testing, then ignore the check against the file size
    if settings.get_setting('only_run_for_ffmpeg_command'):
        return data

    # Check if the file has changed size since it was last processed (useful for metadata only)
    if not file_already_processed(original_file_path):
        # Mark this file to be added to the pending tasks
        data['add_file_to_pending_tasks'] = True
        logger.debug(
            "File has not been processed previously '{}'. It should be added to task list.".format(original_file_path))

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
    # TODO:
    #   - Create parser function for progress
    # Default to no FFMPEG command required. This prevents the FFMPEG command from running if it is not required
    data['exec_command'] = []
    data['repeat'] = False

    # Get the file paths
    file_in = data.get('file_in')
    file_out = data.get('file_out')
    original_file_path = data.get('original_file_path')

    # Ensure this is a video file
    if not test_valid_mimetype(file_in):
        return data

    # Limit to configured file extensions
    # Unlike other plugins, this is checked against the original file path, not what is currently cached
    settings = Settings()
    if settings.get_setting('limit_to_extensions'):
        allowed_extensions = settings.get_setting('allowed_extensions')
        if not file_ends_in_allowed_extensions(original_file_path, allowed_extensions):
            return data

    # If we are configured to only run for ffmpeg commands, but sma does not want to run one, then return here
    if settings.get_setting('only_run_for_ffmpeg_command'):
        if not file_requires_processing_by_ffmpeg(original_file_path):
            return data

    # Generate mock path
    mock_file_in = generate_mock_path(original_file_path, file_in, file_out)

    # Build args
    data['exec_command'] = build_worker_args(mock_file_in)

    # Set file_in and file_out
    data['file_in'] = mock_file_in
    data['file_out'] = predict_file_out(mock_file_in)

    # Mark file as being processed for post-processor
    src_file_hash = hashlib.md5(original_file_path.encode('utf8')).hexdigest()
    profile_directory = settings.get_profile_directory()
    plugin_file_lockfile = os.path.join(profile_directory, '{}.lock'.format(src_file_hash))
    with open(plugin_file_lockfile, 'w') as f:
        pass

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
    # We only care that the task completed successfully.
    # If a worker processing task was unsuccessful, dont mark the file as being processed
    if not data.get('task_processing_success'):
        return data

    # Was the processed file one of the ones we worked on...
    settings = Settings()
    original_source_path = data.get('source_data', {}).get('abspath', '_')
    src_file_hash = hashlib.md5(original_source_path.encode('utf8')).hexdigest()
    profile_directory = settings.get_profile_directory()
    plugin_file_lockfile = os.path.join(profile_directory, '{}.lock'.format(src_file_hash))
    if not os.path.exists(plugin_file_lockfile):
        return data
    os.remove(plugin_file_lockfile)

    # Loop over the destination_files list and update the directory info file for each one
    for destination_file in data.get('destination_files'):
        # get the checksum of the current file
        file_size = get_file_size(destination_file)
        directory_info = UnmanicDirectoryInfo(os.path.dirname(destination_file))
        directory_info.set('sickbeard_mp4_automator', os.path.basename(destination_file), str(file_size))
        directory_info.save()
        logger.debug("File size info written for '{}' to prevent re-processing.".format(destination_file))

    return data
