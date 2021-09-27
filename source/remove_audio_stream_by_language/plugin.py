#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
    plugins.__init__.py

    Written by:               Josh.5 <jsunnex@gmail.com>
    Date:                     20 Sep 2021, (10:45 PM)

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

from unmanic.libs.unplugins.settings import PluginSettings

from remove_audio_stream_by_language.lib.ffmpeg import StreamMapper, Probe, Parser

# Configure plugin logger
logger = logging.getLogger("Unmanic.Plugin.remove_audio_stream_by_language")


class Settings(PluginSettings):
    settings = {
        "languages": ''
    }
    form_settings = {
        "languages": {
            "label": "Languages to remove",
        },
    }


class PluginStreamMapper(StreamMapper):
    def __init__(self):
        super(PluginStreamMapper, self).__init__(logger, ['audio'])

    def test_tags_for_search_string(self, stream_tags, stream_id):
        # TODO: Check if we need to add 'title' tags
        if stream_tags and True in list(k.lower() in ['language'] for k in stream_tags):
            settings = Settings()
            language_list = settings.get_setting('languages')
            languages = list(filter(None, language_list.split(',')))
            for language in languages:
                language = language.strip()
                if language and language.lower() in stream_tags.get('language', '').lower():
                    # Found a matching language. Process this stream to remove it
                    return True
        else:
            logger.warning(
                "Audio stream #{} in file '{}' has no 'language' tag. Ignoring".format(stream_id, self.input_file))
        return False

    def test_stream_needs_processing(self, stream_info: dict):
        """Only add streams that have language task that match our list"""
        if self.test_tags_for_search_string(stream_info.get('tags'), stream_info.get('index')):
            return True
        return False

    def custom_stream_mapping(self, stream_info: dict, stream_id: int):
        """Remove this stream"""
        return {
            'stream_mapping':  [],
            'stream_encoding': [],
        }


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
    # Get the list of configured extensions to search for
    settings = Settings()

    # If the config is empty (not yet configured) ignore everything
    if not settings.get_setting('languages'):
        logger.debug("Plugin has not yet been configured with a list of file extensions to allow. Blocking everything.")
        return False

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

    if mapper.streams_need_processing():
        # Mark this file to be added to the pending tasks
        data['add_file_to_pending_tasks'] = True
        logger.debug("File '{}' should be added to task list. Probe found streams require processing.".format(abspath))
    else:
        logger.debug("File '{}' does not contain streams that require processing.".format(abspath))

    del mapper

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

    if mapper.streams_need_processing():
        # Set the output file
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
