#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
    Written by:               Josh.5 <jsunnex@gmail.com>
    Date:                     18 April 2021, (1:41 AM)
 
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
import re

from extract_srt_subtitles_to_files.lib.ffmpeg import StreamMapper, Probe, Parser

# Configure plugin logger
logger = logging.getLogger("Unmanic.Plugin.extract_srt_subtitles_to_files")


class PluginStreamMapper(StreamMapper):
    def __init__(self):
        super(PluginStreamMapper, self).__init__(logger, ['subtitle'])
        self.sub_streams = []

    def test_stream_needs_processing(self, stream_info: dict):
        """Any text based will need to be processed"""
        if stream_info.get('codec_name').lower() in ['srt', 'subrip', 'mov_text']:
            return True
        return False

    def custom_stream_mapping(self, stream_info: dict, stream_id: int):
        # Find a tag for this subtitle
        subtitle_tag = ''
        stream_tags = stream_info.get('tags', {})
        if stream_tags.get('language'):
            subtitle_tag = "{}.{}".format(subtitle_tag, stream_tags.get('language'))
        if stream_tags.get('title'):
            subtitle_tag = "{}.{}".format(subtitle_tag, stream_tags.get('title'))

        # If there were no tags, just number the file
        if not subtitle_tag:
            subtitle_tag = "{}.{}".format(subtitle_tag, stream_info.get('index'))

        # Ensure subtitle tag does not contain whitespace
        subtitle_tag = re.sub('\s', '-', subtitle_tag)

        self.sub_streams.append(
            {
                'stream_id':      stream_id,
                'subtitle_tag':   subtitle_tag,
                'stream_mapping': ['-map', '0:s:{}'.format(stream_id)],
            }
        )

        # Copy the streams to the destination. This will actually do nothing...
        return {
            'stream_mapping':  ['-map', '0:s:{}'.format(stream_id)],
            'stream_encoding': ['-c:s:{}'.format(stream_id), 'copy'],
        }

    def get_ffmpeg_args(self):
        """
        Overwrite default function. We only need the first lot of args.

        :return:
        """
        args = []

        # Add generic options first
        args += self.generic_options

        # Add the input file
        # This class requires at least one input file specified with the input_file attribute
        if not self.input_file:
            raise Exception("Input file has not been set")
        args += ['-i', self.input_file]

        # Add other main options
        args += self.main_options

        # Add advanced options. This includes the stream mapping and the encoding args
        args += self.advanced_options

        return args


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
    probe = Probe(logger, allowed_mimetypes=['video'])
    if not probe.file(abspath):
        # File probe failed, skip the rest of this test
        return data

    # Get stream mapper
    mapper = PluginStreamMapper()
    mapper.set_probe(probe)

    split_original_file_path = os.path.splitext(data.get('original_file_path'))
    original_file_directory = os.path.dirname(data.get('original_file_path'))

    if mapper.streams_need_processing():
        # Set the input file
        mapper.set_input_file(abspath)

        # Get generated ffmpeg args
        ffmpeg_args = mapper.get_ffmpeg_args()

        # Append STR extract args
        for sub_stream in mapper.sub_streams:
            stream_mapping = sub_stream.get('stream_mapping', [])
            subtitle_tag = sub_stream.get('subtitle_tag')

            ffmpeg_args += stream_mapping
            ffmpeg_args += [
                "-y",
                os.path.join(original_file_directory, "{}{}.srt".format(split_original_file_path[0], subtitle_tag)),
            ]

        # Apply ffmpeg args to command
        data['exec_command'] = ['ffmpeg']
        data['exec_command'] += ffmpeg_args

        # Set the parser
        parser = Parser(logger)
        parser.set_probe(probe)
        data['command_progress_parser'] = parser.parse_progress

    return data
