#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
    plugins.__init__.py

    Written by:               Josh.5 <jsunnex@gmail.com>
    Date:                     28 Aug 2021, (11:55 PM)

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

from video_remuxer.lib.ffmpeg import StreamMapper, Probe, Parser

# Configure plugin logger
logger = logging.getLogger("Unmanic.Plugin.video_remuxer")


class Settings(PluginSettings):
    settings = {
        "dest_container": "mkv",
    }

    def __init__(self):
        self.form_settings = {
            "dest_container": {
                "label":          "Set the output container",
                "input_type":     "select",
                "select_options": [
                    {
                        'value': "mkv",
                        'label': ".mkv - Matroska",
                    },
                    {
                        'value': "avi",
                        'label': ".avi - AVI (Audio Video Interleaved)",
                    },
                    {
                        'value': "mov",
                        'label': ".mov - QuickTime / MOV",
                    },
                    {
                        'value': "mp4",
                        'label': ".mp4 - MP4 (MPEG-4 Part 14)",
                    },
                ],
            },
        }


class PluginStreamMapper(StreamMapper):
    def __init__(self):
        super(PluginStreamMapper, self).__init__(logger, ['video', 'audio', 'subtitle', 'data', 'attachment'])

    def test_stream_needs_processing(self, stream_info: dict):
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
    probe = Probe(logger, allowed_mimetypes=['video'])
    if not probe.file(abspath):
        # File probe failed, skip the rest of this test
        return data

    # Get stream mapper
    mapper = PluginStreamMapper()
    mapper.set_probe(probe)

    # Set the input file
    mapper.set_input_file(abspath)

    settings = Settings()
    container_extension = settings.get_setting('dest_container')

    if mapper.container_needs_remuxing(container_extension):
        # Mark this file to be added to the pending tasks
        data['add_file_to_pending_tasks'] = True
        logger.debug("File '{}' should be added to task list. Probe found file needs to be processed.".format(abspath))
    else:
        logger.debug("File '{}' is already the required format.".format(abspath))

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
    probe = Probe(logger, allowed_mimetypes=['video'])
    if not probe.file(abspath):
        # File probe failed, skip the rest of this test
        return data

    # Get stream mapper
    mapper = PluginStreamMapper()
    mapper.set_probe(probe)

    # Set the input file
    mapper.set_input_file(abspath)

    settings = Settings()
    container_extension = settings.get_setting('dest_container')

    if mapper.container_needs_remuxing(container_extension):
        # Map streams (copy from source to destination)
        mapper.streams_need_processing()

        # Set the input file
        mapper.set_input_file(abspath)

        # Set the output file
        split_file_out = os.path.splitext(data.get('file_out'))
        new_file_out = "{}.{}".format(split_file_out[0], container_extension.lstrip('.'))
        mapper.set_output_file(new_file_out)
        data['file_out'] = new_file_out

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
