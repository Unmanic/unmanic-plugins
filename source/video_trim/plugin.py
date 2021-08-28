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

from unmanic.libs.unplugins.settings import PluginSettings

from video_trim.lib.ffmpeg import StreamMapper, Probe, Parser

# Configure plugin logger
logger = logging.getLogger("Unmanic.Plugin.video_trim")


class Settings(PluginSettings):
    settings = {
        "start_seconds": 0,
        "end_seconds":   0,
    }
    form_settings = {
        "start_seconds": {
            "label": "Seconds to trim off the start of the files",
        },
        "end_seconds":   {
            "label": "Seconds to trim off the end of the files",
        },
    }


class PluginStreamMapper(StreamMapper):
    def __init__(self):
        super(PluginStreamMapper, self).__init__(logger, 'video')

    def test_stream_needs_processing(self, stream_info: dict):
        if stream_info.get('codec_name').lower() in ['h264']:
            return False
        return True

    def custom_stream_mapping(self, stream_info: dict, stream_id: int):
        settings = Settings()

        if settings.get_setting('advanced'):
            stream_encoding = ['-c:v:{}'.format(stream_id), 'libx264']
            stream_encoding += settings.get_setting('custom_options').split()
        else:
            stream_encoding = [
                '-c:v:{}'.format(stream_id), 'libx264',
                '-preset', str(settings.get_setting('preset')),
                '-crf', str(settings.get_setting('crf')),
            ]

        return {
            'stream_mapping':  ['-map', '0:v:{}'.format(stream_id)],
            'stream_encoding': stream_encoding,
        }


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
    settings = Settings()

    # Default to not run the FFMPEG command unless streams are found to be converted
    data['exec_command'] = []
    data['repeat'] = False

    # Get the path to the file
    abspath = data.get('file_in')

    # Get file probe
    probe = Probe(logger)
    probe.file(abspath)

    # Fetch duration from file probe...
    file_probe_format = probe.get('format', {})
    duration = file_probe_format.get('duration')
    if not duration:
        # DEPRECIATED: 'exec_ffmpeg' kept for legacy Unmanic versions
        data['exec_ffmpeg'] = False
        # Without duration, we cannot set the start or end cut points
        return data

    start_point = []
    start_seconds = settings.get_setting('start_seconds')
    if start_seconds and float(start_seconds) > 0:
        # Ensure the start trim is less than the duration of the file
        if float(start_seconds) > float(duration):
            # The configured value is larger than the duration of the file.
            # Skip this file for now...
            # DEPRECIATED: 'exec_ffmpeg' kept for legacy Unmanic versions
            data['exec_ffmpeg'] = False
            return data
        # Build the start trim args
        start_point = [
            '-ss', str(settings.get_setting('start_seconds')),
        ]

    # Reduce duration by X seconds less the start_seconds
    end_point = []
    end_seconds = settings.get_setting('end_seconds')
    if end_seconds and float(end_seconds) > 0:
        # Ensure the end trim is less than the duration of the file
        if float(end_seconds) > float(duration):
            # The configured value is larger than the duration of the file.
            # Skip this file for now...
            # DEPRECIATED: 'exec_ffmpeg' kept for legacy Unmanic versions
            data['exec_ffmpeg'] = False
            return data
        # Build the end trim args
        duration = str(float(duration) - float(end_seconds))
        end_point = [
            '-to', str(duration),
        ]

    # Build ffmpeg args and add them to the return data
    ffmpeg_args = [
        '-i',
        data.get('file_in'),
        '-hide_banner',
        '-loglevel', 'info',
        '-strict', '-2',
        '-max_muxing_queue_size', '4096',
    ]
    ffmpeg_args += start_point
    ffmpeg_args += end_point
    ffmpeg_args += [
        '-c', 'copy',
        '-map', '0',
        '-y',
        data.get('file_out'),
    ]
    # DEPRECIATED: 'ffmpeg_args' kept for legacy Unmanic versions
    data['ffmpeg_args'] = ffmpeg_args

    data['exec_command'] = ['ffmpeg']
    data['exec_command'] += ffmpeg_args

    # Set the parser
    parser = Parser(logger)
    parser.set_probe(probe)
    data['command_progress_parser'] = parser.parse_progress

    return data
