#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
    Written by:               Josh.5 <jsunnex@gmail.com>
    Date:                     17 March 2021, (10:36 PM)
 
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

    :param data:
    :return:

    """
    # Default to no FFMPEG command required. This prevents the FFMPEG command from running if it is not required
    data['exec_ffmpeg'] = False

    # Check file probe for title metadata in the video
    file_probe = data.get('file_probe')

    video_stream_count = 0
    audio_stream_count = 0
    subtitle_stream_count = 0

    streams_to_map = []
    streams_to_copy = []

    probe_streams = file_probe.get('streams')
    for probe_stream in probe_streams:
        # Check if a video stream exists with a codec name in ["mjpeg"]
        codec_type = probe_stream.get('codec_type')
        codec_name = probe_stream.get('codec_name')
        if codec_type.lower() == 'video' and codec_name in ['mjpeg']:
            # Found a stream with an image!
            # Set the exec_ffmpeg param to True to run the ffmpeg command once the plugin completes
            data['exec_ffmpeg'] = True
            continue
        else:
            # Handle anything that is not an image video stream
            index = probe_stream.get('index')

            # Map this video stream to be processed
            streams_to_map = streams_to_map + [
                "-map", "0:{}".format(index)
            ]

            # Copy the stream to the new file
            if codec_type.lower() == 'video':
                streams_to_copy += [
                    "-c:v:{}".format(video_stream_count), "copy"
                ]
                video_stream_count += 1
                continue
            elif codec_type.lower() == 'audio':
                streams_to_copy += [
                    "-c:a:{}".format(audio_stream_count), "copy"
                ]
                audio_stream_count += 1
                continue
            elif codec_type.lower() == 'subtitle':
                streams_to_copy += [
                    "-c:s:{}".format(subtitle_stream_count), "copy"
                ]
                subtitle_stream_count += 1
                continue

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
        data['ffmpeg_args'] += streams_to_copy

        # Do not remux the file. Keep the file out in the same container
        split_file_in = os.path.splitext(data.get('file_in'))
        split_file_out = os.path.splitext(data.get('file_out'))
        data['file_out'] = "{}{}".format(split_file_out[0], split_file_in[1])

        data['ffmpeg_args'] += ['-y', data.get('file_out')]

    return data
