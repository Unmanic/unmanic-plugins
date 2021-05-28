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
import os
import re

from unmanic.libs.unplugins.settings import PluginSettings


class Settings(PluginSettings):
    settings = {}


def on_worker_process(data):
    """
    Runner function - enables additional configured processing jobs during the worker stages of a task.

    The 'data' object argument includes:
        exec_ffmpeg             - Boolean, should Unmanic run FFMPEG with the data returned from this plugin.
        file_probe              - A dictionary object containing the current file probe state.
        ffmpeg_args             - A list of Unmanic's default FFMPEG args.
        file_in                 - The source file to be processed by the FFMPEG command.
        file_out                - The destination that the FFMPEG command will output.
        original_file_path      - The absolute path to the original library file.

    :param data:
    :return:

    """
    # Default to no FFMPEG command required. This prevents the FFMPEG command from running if it is not required
    data['exec_ffmpeg'] = False

    # Set the file out as the file in (the source file is not modified with this plugin)
    data['file_out'] = data.get("file_in")

    # Check file probe for title metadata in the video
    file_probe = data.get('file_probe')

    split_original_file_path = os.path.splitext(data.get('original_file_path'))
    original_file_directory = os.path.dirname(data.get('original_file_path'))

    streams_to_map = []
    probe_streams = file_probe.get('streams')
    for probe_stream in probe_streams:
        # Check if a video stream exists with a codec name in ["mjpeg"]
        codec_type = probe_stream.get('codec_type')
        codec_name = probe_stream.get('codec_name')
        if codec_type.lower() == 'subtitle' and codec_name in ['srt', 'subrip', 'mov_text']:
            # Found a stream with an supported subtitle!
            # Set the exec_ffmpeg param to True to run the ffmpeg command once the plugin completes
            data['exec_ffmpeg'] = True

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

    if data['exec_ffmpeg']:
        # Build ffmpeg args and add them to the return data
        data['ffmpeg_args'] = [
            '-i',
            data.get('file_in'),
            '-hide_banner',
            '-loglevel',
            'info',
        ]
        data['ffmpeg_args'] += streams_to_map

    return data
