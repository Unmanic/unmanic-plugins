#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
    unmanic-plugins.plugin.py

    Written by:               Josh.5 <jsunnex@gmail.com>
    Date:                     01 Jul 2021, (12:22 PM)

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

from normalise_aac.lib.ffmpeg import StreamMapper, Probe, Parser

# Configure plugin logger
logger = logging.getLogger("Unmanic.Plugin.normalise_aac")


class Settings(PluginSettings):
    settings = {
        'I':                           '-24.0',
        'LRA':                         '7.0',
        'TP':                          '-2.0',
        'ignore_previously_processed': True,
    }
    form_settings = {
        "I":                           {
            "label":          "Integrated loudness target",
            "input_type":     "slider",
            "slider_options": {
                "min":  -70.0,
                "max":  -5.0,
                "step": 0.1,
            },
        },
        "LRA":                         {
            "label":          "Loudness range",
            "input_type":     "slider",
            "slider_options": {
                "min":  1.0,
                "max":  20.0,
                "step": 0.1,
            },
        },
        "TP":                          {
            "label":          "The maximum true peak",
            "input_type":     "slider",
            "slider_options": {
                "min":  -9.0,
                "max":  0,
                "step": 0.1,
            },
        },
        "ignore_previously_processed": {
            "label": "Ignore all files previously normalised with this plugin regardless of the settings above.",
        },
    }


class PluginStreamMapper(StreamMapper):
    def __init__(self):
        super(PluginStreamMapper, self).__init__(logger, ['audio'])
        self.settings = None

    def set_settings(self, settings):
        self.settings = settings

    def test_stream_needs_processing(self, stream_info: dict):
        # Only process AAC audio streams
        if stream_info.get('codec_name').lower() in ['aac']:
            return True
        return False

    def custom_stream_mapping(self, stream_info: dict, stream_id: int):
        return {
            'stream_mapping':  ['-map', '0:a:{}'.format(stream_id)],
            'stream_encoding': [
                '-c:a:{}'.format(stream_id), 'aac',
                '-filter:a:{}'.format(stream_id), audio_filtergraph(self.settings),
            ]
        }


def audio_filtergraph(settings):
    i = settings.get_setting('I')
    if not i:
        i = settings.settings.get('I')
    lra = settings.get_setting('LRA')
    if not lra:
        i = settings.settings.get('LRA')
    tp = settings.get_setting('TP')
    if not tp:
        i = settings.settings.get('TP')

    return 'loudnorm=I={}:LRA={}:TP={}'.format(i, lra, tp)


def file_already_normalised(settings, path):
    directory_info = UnmanicDirectoryInfo(os.path.dirname(path))

    try:
        previous_loudnorm_filtergraph = directory_info.get('normalise_aac', os.path.basename(path))
    except NoSectionError as e:
        previous_loudnorm_filtergraph = ''
    except NoOptionError as e:
        previous_loudnorm_filtergraph = ''
    except Exception as e:
        logger.debug("Unknown exception {}.".format(e))
        previous_loudnorm_filtergraph = ''

    if previous_loudnorm_filtergraph:
        logger.debug("File's stream was previously normalised with {}.".format(previous_loudnorm_filtergraph))
        # This stream already has been normalised
        if settings.get_setting('ignore_previously_processed'):
            logger.debug("Plugin configured to ignore previously normalised streams")
            return True
        elif audio_filtergraph(settings) in previous_loudnorm_filtergraph:
            # The previously normalised stream matches what is already configured
            logger.debug(
                "Stream was previously normalised with the same settings as what the plugin is currently configured")
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

    # Configure settings object (maintain compatibility with v1 plugins)
    if data.get('library_id'):
        settings = Settings(library_id=data.get('library_id'))
    else:
        settings = Settings()

    # Get stream mapper
    mapper = PluginStreamMapper()
    mapper.set_settings(settings)
    mapper.set_probe(probe)

    if not file_already_normalised(settings, abspath):
        # Mark this file to be added to the pending tasks
        data['add_file_to_pending_tasks'] = True
        logger.debug("File '{}' should be added to task list. File has not been previously normalised.".format(abspath))
    else:
        logger.debug("File '{}' has been previously normalised.".format(abspath))

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

    # Get file probe
    probe = Probe(logger, allowed_mimetypes=['video', 'audio'])
    if not probe.file(abspath):
        # File probe failed, skip the rest of this test
        return data

    # Configure settings object (maintain compatibility with v1 plugins)
    if data.get('library_id'):
        settings = Settings(library_id=data.get('library_id'))
    else:
        settings = Settings()

    if not file_already_normalised(settings, data.get('file_in')):
        # Get stream mapper
        mapper = PluginStreamMapper()
        mapper.set_settings(settings)
        mapper.set_probe(probe)

        if mapper.streams_need_processing():
            # Set the input file
            mapper.set_input_file(abspath)

            # Do not remux the file. Keep the file out in the same container
            mapper.set_output_file(data.get('file_out'))

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

    # Configure settings object (maintain compatibility with v1 plugins)
    if data.get('library_id'):
        settings = Settings(library_id=data.get('library_id'))
    else:
        settings = Settings()

    # Loop over the destination_files list and update the directory info file for each one
    for destination_file in data.get('destination_files'):
        directory_info = UnmanicDirectoryInfo(os.path.dirname(destination_file))
        directory_info.set('normalise_aac', os.path.basename(destination_file), audio_filtergraph(settings))
        directory_info.save()
        logger.debug("Normalise AAC info written for '{}'.".format(destination_file))

    return data
