#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
    Written by:               Josh.5 <jsunnex@gmail.com>
    Date:                     9 March 2021, (1:09 PM)

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
from configparser import NoSectionError, NoOptionError

from unmanic.libs.unplugins.settings import PluginSettings
from unmanic.libs.directoryinfo import UnmanicDirectoryInfo

from video_trim.lib.ffmpeg import StreamMapper, Probe, Parser

# Configure plugin logger
logger = logging.getLogger("Unmanic.Plugin.video_trim")


class Settings(PluginSettings):
    settings = {
        "start_seconds":               0,
        "end_seconds":                 0,
        'ignore_previously_processed': True,
    }
    form_settings = {
        "start_seconds":               {
            "label": "Seconds to trim off the start of the files",
        },
        "end_seconds":                 {
            "label": "Seconds to trim off the end of the files",
        },
        "ignore_previously_processed": {
            "label": "Ignore all files previously trimmed with this plugin.",
        },
    }


class PluginStreamMapper(StreamMapper):
    def __init__(self):
        super(PluginStreamMapper, self).__init__(logger, ['video', 'audio'])

    def test_stream_needs_processing(self, stream_info: dict):
        # No streams need to be modified with custom mapping. Copy all.
        return False

    def custom_stream_mapping(self, stream_info: dict, stream_id: int):
        # Will not be called as above function returns False every time.
        return {
            'stream_mapping':  [],
            'stream_encoding': [],
        }

    def __gen_start_args(self, settings, duration):
        start_seconds = settings.get_setting('start_seconds')
        main_options = {}
        if start_seconds and float(start_seconds) > 0:
            # Ensure the start trim is less than the duration of the file
            if float(start_seconds) > float(duration):
                # The configured value is larger than the duration of the file.
                # Skip this file for now...
                return main_options
            # Build the start trim args
            main_options = {
                "-ss": str(settings.get_setting('start_seconds')),
            }
            self.set_ffmpeg_main_options(**main_options)

        return main_options

    def __gen_end_args(self, settings, duration):
        # Reduce duration by X seconds less the start_seconds
        end_seconds = settings.get_setting('end_seconds')
        main_options = {}
        if end_seconds and float(end_seconds) > 0:
            # Ensure the end trim is less than the duration of the file
            if float(end_seconds) > float(duration):
                # The configured value is larger than the duration of the file.
                # Skip this file for now...
                return main_options
            # Build the start trim args
            main_options = {
                "-to": str(duration),
            }
            self.set_ffmpeg_main_options(**main_options)

        return main_options

    def gen_trim_args(self):
        """
        Generate a list of args for using a VAAPI decoder
        :return:
        """
        settings = Settings()
        file_probe_format = self.probe.get('format', {})
        duration = file_probe_format.get('duration')
        if not duration:
            # Without duration, we cannot set the start or end cut points
            return ''

        # generate the args
        start_args = self.__gen_start_args(settings, duration)
        end_args = self.__gen_end_args(settings, duration)

        # Create an args string to be used to mark against a file
        args_string = ''
        for key in start_args:
            args_string += "{} {}".format(key, start_args.get(key))
        for key in end_args:
            args_string += "{} {}".format(key, end_args.get(key))
        return args_string

    @staticmethod
    def file_already_trimmed(path):
        settings = Settings()
        directory_info = UnmanicDirectoryInfo(os.path.dirname(path))

        try:
            previous_trim = directory_info.get('video_trim', os.path.basename(path))
        except NoSectionError as e:
            previous_trim = ''
        except NoOptionError as e:
            previous_trim = ''
        except Exception as e:
            logger.debug("Unknown exception {}.".format(e))
            previous_trim = ''

        if previous_trim:
            logger.debug("File was previously trimmed with {}.".format(previous_trim))
            # This stream already has been normalised
            if settings.get_setting('ignore_previously_processed'):
                logger.debug("Plugin configured to ignore previously normalised streams")
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

    # Get file probe
    probe = Probe(logger, allowed_mimetypes=['video', 'audio'])
    if not probe.file(abspath):
        # File probe failed, skip the rest of this test
        return data

    # Get stream mapper
    mapper = PluginStreamMapper()
    mapper.set_probe(probe)

    if not mapper.file_already_trimmed(abspath):
        # Mark this file to be added to the pending tasks
        data['add_file_to_pending_tasks'] = True
        logger.debug("File '{}' should be added to task list. File has not been previously trimmed.".format(abspath))
    else:
        logger.debug("File '{}' has been previously trimmed.".format(abspath))

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

    DEPRECIATED 'data' object args passed for legacy Unmanic versions:
        exec_ffmpeg             - Boolean, should Unmanic run FFMPEG with the data returned from this plugin.
        ffmpeg_args             - A list of Unmanic's default FFMPEG args.

    :param data:
    :return:

    """
    # Default to no FFMPEG command required. This prevents the FFMPEG command from running if it is not required
    data['exec_command'] = []
    data['repeat'] = False

    # Get the path to the file
    abspath = data.get('file_in')

    # Get file probe
    probe = Probe(logger, allowed_mimetypes=['video', 'audio'])
    if not probe.file(abspath):
        # File probe failed, skip the rest of this test
        return data

    # Fetch duration from file probe...
    file_probe_format = probe.get('format', {})
    duration = file_probe_format.get('duration')
    if not duration:
        # Without duration, we cannot set the start or end cut points
        return data

    # Get stream mapper
    mapper = PluginStreamMapper()
    mapper.set_probe(probe)

    if not mapper.file_already_trimmed(abspath):
        # Set the input file
        mapper.set_input_file(abspath)

        # Do not remux the file. Keep the file out in the same container
        mapper.set_output_file(data.get('file_out'))

        # Set the trim args
        mapper.gen_trim_args()

        # Set stream mapping and encoding args
        mapper.get_stream_mapping()
        mapper.get_stream_encoding()

        # Get generated ffmpeg args
        ffmpeg_args = mapper.get_ffmpeg_args()

        # Apply ffmpeg args to command
        data['exec_command'] = ['ffmpeg']
        data['exec_command'] += ffmpeg_args

        # Set the parser
        parser = Parser(logger)
        parser.set_probe(probe)
        data['command_progress_parser'] = parser.parse_progress

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
    # If a worker processing task was unsuccessful, dont mark the file as being normalised
    # TODO: Figure out a way to know if a file was normalised but another plugin was the
    #   cause of the task processing failure flag
    if not data.get('task_processing_success'):
        return data

    # Loop over the destination_files list and update the directory info file for each one
    for destination_file in data.get('destination_files'):

        # Get the original file's absolute path
        if not os.path.exists(destination_file):
            logger.error("Destination file does not exist '{}'.".format(destination_file))
            continue

        # Get file probe
        probe = Probe(logger, allowed_mimetypes=['video', 'audio'])
        if not probe.file(destination_file):
            # File probe failed, skip the rest of this test
            logger.error("Destination file could not be probed! Is it corrupted? '{}'.".format(destination_file))
            continue

        # Get stream mapper
        mapper = PluginStreamMapper()
        mapper.set_probe(probe)

        # Get trim args for the source file
        trim_args = mapper.gen_trim_args()

        directory_info = UnmanicDirectoryInfo(os.path.dirname(destination_file))
        directory_info.set('video_trim', os.path.basename(destination_file), trim_args)
        directory_info.save()
        logger.debug("Video Trim info written for '{}'.".format(destination_file))

    return data
