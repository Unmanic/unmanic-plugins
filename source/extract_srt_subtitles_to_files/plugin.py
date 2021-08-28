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

from lib.ffmpeg import Probe, Parser

# Configure plugin logger
logger = logging.getLogger("Unmanic.Plugin.extract_srt_subtitles_to_files")


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
    exec_ffmpeg = False

    # Get the path to the file
    abspath = data.get('file_in')

    # Get file probe
    probe = Probe(logger)
    probe.file(abspath)

    # Set the file out as the file in (the source file is not modified with this plugin)
    data['file_out'] = data.get("file_in")

    split_original_file_path = os.path.splitext(data.get('original_file_path'))
    original_file_directory = os.path.dirname(data.get('original_file_path'))

    streams_to_map = []
    probe_streams = probe.get('streams')
    for probe_stream in probe_streams:
        # Check if a video stream exists with a codec name in ["mjpeg"]
        codec_type = probe_stream.get('codec_type')
        codec_name = probe_stream.get('codec_name')
        if codec_type.lower() == 'subtitle' and codec_name in ['srt', 'subrip', 'mov_text']:
            # Found a stream with an supported subtitle!
            # Set the exec_ffmpeg var to True to run the ffmpeg command once the plugin completes
            exec_ffmpeg = True

            # Find a tag for this subtitle
            subtitle_tag = probe_stream.get('index')
            stream_tags = probe_stream.get('tags', {})
            if stream_tags.get('title'):
                subtitle_tag = stream_tags.get('title')
            elif stream_tags.get('language'):
                subtitle_tag = stream_tags.get('language')

            # Ensure subtitle tag only contains numbers or letters
            subtitle_tag = re.sub('[^0-9a-zA-Z]+', '_', subtitle_tag)

            # Ensure subtitle tag is lower case
            subtitle_tag = subtitle_tag.lower()

            # Map this stream to new subtitle file
            streams_to_map += [
                "-map",
                "0:{}".format(probe_stream.get('index')),
                "-c",
                "copy",
                "-y",
                os.path.join(original_file_directory, "{}-{}.srt".format(split_original_file_path[0], subtitle_tag)),
            ]

    # DEPRECIATED: 'exec_ffmpeg' kept for legacy Unmanic versions
    data['exec_ffmpeg'] = False
    if exec_ffmpeg:
        # Build ffmpeg args and add them to the return data
        ffmpeg_args = [
            '-i',
            data.get('file_in'),
            '-hide_banner',
            '-loglevel',
            'info',
        ]
        ffmpeg_args += streams_to_map

        # DEPRECIATED: 'ffmpeg_args' kept for legacy Unmanic versions
        data['ffmpeg_args'] = ffmpeg_args
        # DEPRECIATED: 'exec_ffmpeg' kept for legacy Unmanic versions
        data['exec_ffmpeg'] = True

        data['exec_command'] = ['ffmpeg']
        data['exec_command'] += ffmpeg_args

        # Set the parser
        parser = Parser(logger)
        parser.set_probe(probe)
        data['command_progress_parser'] = parser.parse_progress

    return data
