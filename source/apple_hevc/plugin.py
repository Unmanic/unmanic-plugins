#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
    unmanic-plugins.plugin.py

    Written by:               k29t59dh <chapels.rill_0h@icloud.com>
    Date:                     9 Aug 2023, (4:06 PM)

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
from apple_hevc.lib.ffmpeg import StreamMapper, Probe, Parser

# Configure plugin logger
logger = logging.getLogger("Unmanic.Plugin.apple_hevc")

class Settings(PluginSettings):
    settings = {
        "faststart":      True,
    }
    form_settings = {
        "faststart": {
            "label": "Moov atom at head (-movflags +faststart)",
        },
    }
    
class PluginStreamMapper(StreamMapper):
    def __init__(self):
        super(PluginStreamMapper, self).__init__(logger, ['video'])
        self.settings = None

    def set_settings(self, settings):
        self.settings = settings

    def test_stream_needs_processing(self, stream_info: dict):
        """Check if file has hevc hev1 stream"""
        hev1_stream_types = [
            'video',
        ]

        hev1_stream_codecs = [
            'hevc',
            'h265',
        ]

        hev1_stream_codec_tags = [
            'hev1',
        ]

        if stream_info.get('codec_type', '').lower() in hev1_stream_types and \
           stream_info.get('codec_name', '').lower() in hev1_stream_codecs and \
           stream_info.get('codec_tag_string', '').lower() in hev1_stream_codec_tags:
            return True
        return False


    def custom_stream_mapping(self, stream_info: dict, stream_id: int):
        stream_encoding = ['-c:v:{}'.format(stream_id), 'copy', '-tag:v:{}'.format(stream_id), 'hvc1']
        if self.settings.get_setting('faststart'):
            stream_encoding += ['-movflags', '+faststart']
            
        return {
            'stream_mapping':  ['-map', '0:v:{}'.format(stream_id)],
            'stream_encoding': stream_encoding,
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
    # Get the path to the file
    abspath = data.get('path')

    # Get file probe
    probe = Probe.init_probe(data, logger)
    if not probe.file(abspath):
        # File probe failed, skip the rest of this test
        return data

    if not 'mp4' in probe.get('format', {}).get('format_name', [ ]):
        logger.debug("File '{}' is type '{}' - plugin requires mp4.".format(abspath, probe.get('format', {}).get('format_name', [ ])))
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

    if mapper.streams_need_processing():
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

    if mapper.streams_need_processing():
        # Set the input file
        mapper.set_input_file(abspath)
        mapper.set_output_file(data.get('file_out'))

        # Get generated ffmpeg args
        ffmpeg_args = mapper.get_ffmpeg_args()
        
        # Apply ffmpeg args to command
        data['exec_command'] = ['ffmpeg']
        data['exec_command'] += ffmpeg_args

        #logger.debug("command: '{}'".format(data['exec_command']))
        
        # Set the parser
        parser = Parser(logger)
        parser.set_probe(probe)
        data['command_progress_parser'] = parser.parse_progress

    return data
