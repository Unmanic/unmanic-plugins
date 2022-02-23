#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
    Written by:               Josh.5 <jsunnex@gmail.com>
    Date:                     23 March 2021, (8:06 PM)
 
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

from reorder_audio_streams_by_language.lib.ffmpeg import StreamMapper, Probe, Parser

# Configure plugin logger
logger = logging.getLogger("Unmanic.Plugin.reorder_audio_streams_by_language")


class Settings(PluginSettings):
    settings = {
        "Search String": "en",
    }


class PluginStreamMapper(StreamMapper):
    def __init__(self):
        # Check all streams (only the desired stream type will matter when tested)
        super(PluginStreamMapper, self).__init__(logger, ['video', 'audio', 'subtitle', 'data', 'attachment'])
        self.settings = None

        # The stream type we are considering as streams of interest
        self.stream_type = 'audio'

        # Flag to say if a search string has matched a stream of interest
        self.found_search_string_streams = False

        # First streams are ones found before the search string was found on a stream of interest
        self.first_stream_mapping = []
        # Last streams are ones found after the search string was found on a stream of interest
        self.last_stream_mapping = []

        # Search string streams of interest are streams that contain the search string
        self.search_string_stream_mapping = []
        # Unmatched streams of interest are streams that do not contain the search string
        self.unmatched_stream_mapping = []

    def set_settings(self, settings):
        self.settings = settings

    def test_tags_for_search_string(self, stream_tags):
        if stream_tags and True in list(k.lower() in ['title', 'language'] for k in stream_tags):
            search_string = self.settings.get_setting('Search String')
            # Check if tag matches the "Search String"
            if search_string.lower() in stream_tags.get('language', '').lower():
                # Found a matching stream in language tag
                return True
            elif search_string in stream_tags.get('title', '').lower():
                # Found a matching stream in title tag
                return True
        return False

    def test_stream_needs_processing(self, stream_info: dict):
        # Always return true here.
        # All streams will use the custom stream mapping method below
        return True

    def custom_stream_mapping(self, stream_info: dict, stream_id: int):
        ident = {
            'video':      'v',
            'audio':      'a',
            'subtitle':   's',
            'data':       'd',
            'attachment': 't'
        }
        codec_type = stream_info.get('codec_type').lower()

        if codec_type == self.stream_type:
            # Process streams of interest
            self.found_search_string_streams = True
            if self.test_tags_for_search_string(stream_info.get('tags')):
                self.search_string_stream_mapping += ['-map', '0:{}:{}'.format(ident.get(codec_type), stream_id)]
            else:
                self.unmatched_stream_mapping += ['-map', '0:{}:{}'.format(ident.get(codec_type), stream_id)]
        else:
            # Process streams not of interest
            if not self.found_search_string_streams:
                self.first_stream_mapping += ['-map', '0:{}:{}'.format(ident.get(codec_type), stream_id)]
            else:
                self.last_stream_mapping += ['-map', '0:{}:{}'.format(ident.get(codec_type), stream_id)]

        # Do not map any streams using the default method
        return {
            'stream_mapping':  [],
            'stream_encoding': []
        }

    def streams_to_be_reordered(self):
        result = False

        # Start by mapping streams
        self.streams_need_processing()

        # Test if there were any matches against the search string
        if self.search_string_stream_mapping and self.unmatched_stream_mapping:
            logger.info("Streams were found matching the search string")
            # Test if the mapping is already in the correct order
            counter = 0
            for item in self.search_string_stream_mapping + self.unmatched_stream_mapping:
                if '-map' in item:
                    continue
                original_position = item.split(':')[-1]
                if int(original_position) != int(counter):
                    logger.info("The new order for the mapped streams will differ from the source file")
                    result = True
                    break
                counter += 1

        return result

    def order_stream_mapping(self):
        args = ['-c', 'copy']
        args += self.first_stream_mapping
        args += self.search_string_stream_mapping
        args += self.unmatched_stream_mapping
        args += self.last_stream_mapping
        self.advanced_options += args


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

    # Configure settings object (maintain compatibility with v1 plugins)
    if data.get('library_id'):
        settings = Settings(library_id=data.get('library_id'))
    else:
        settings = Settings()

    # Get stream mapper
    mapper = PluginStreamMapper()
    mapper.set_settings(settings)
    mapper.set_probe(probe)

    if mapper.streams_to_be_reordered():
        # Mark this file to be added to the pending tasks
        data['add_file_to_pending_tasks'] = True
        logger.debug("File '{}' should be added to task list. Probe found streams require processing.".format(abspath))
    else:
        logger.debug("File '{}' does not contain streams require processing.".format(abspath))

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

    # Configure settings object (maintain compatibility with v1 plugins)
    if data.get('library_id'):
        settings = Settings(library_id=data.get('library_id'))
    else:
        settings = Settings()

    # Get stream mapper
    mapper = PluginStreamMapper()
    mapper.set_settings(settings)
    mapper.set_probe(probe)

    if mapper.streams_to_be_reordered():
        # Set the input file
        mapper.set_input_file(abspath)

        # Set the output file
        # Do not remux the file. Keep the file out in the same container
        mapper.set_output_file(data.get('file_out'))

        # Set the custom mapping order with the advanced options
        mapper.order_stream_mapping()

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
