#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
    plugins.__init__.py

    Written by:               Josh.5 <jsunnex@gmail.com>
    Date:                     23 Aug 2021, (20:38 PM)

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

from add_extra_stereo_audio.lib.ffmpeg import Probe, Parser

# Configure plugin logger
logger = logging.getLogger("Unmanic.Plugin.add_extra_stereo_audio")


class Settings(PluginSettings):
    settings = {
        "stream_language":       '',
        "channels":              '',
        "codec_name":            '',
        "use_libfdk_aac":         False,
    }

    def __init__(self, *args, **kwargs):
        super(Settings, self).__init__(*args, **kwargs)
        self.form_settings = {
            "stream_language":              {
                "label": "find stream in specified language to duplicate",
            },
            "channels":                     {
                "label": "number of channels in source stream",
            },
            "codec_name":                   {
                "label": "enter name of codec used in source stream",
            },
            "use_libfdk_aac":               {
                "label": "check if you want to use libfdk_aac (requires ffmpeg 5), otherwise aac is used",
            }
        }

def stream_to_stereo_encode(stream_language, channels, codec_name, probe_streams):
    audio_stream = -1
    stream = audio_stream
    for  i in range(0, len(probe_streams)):
        if "codec_type" in probe_streams[i] and probe_streams[i]["codec_type"] == "audio":
            if probe_streams[i]["codec_name"] == "aac" and probe_streams[i]["channels"] == 2 and probe_streams[i]["channel_layout"] == "stereo": return stream


    for i in range(0, len(probe_streams)):
        if "codec_type" in probe_streams[i] and probe_streams[i]["codec_type"] == "audio":
            if stream_language == '' or channels == '' or codec_name == '':
                if  int(probe_streams[i]["channels"]) > 4:
                    audio_stream += 1
                    stream = audio_stream
                    break
            else:
                if str(probe_streams[i]["channels"]) == channels and probe_streams[i]["tags"]["language"] == stream_language and probe_streams[i]["codec_name"] == codec_name:
                    audio_stream += 1
                    stream = audio_stream
                    break

    return stream


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
    probe_data = Probe(logger, allowed_mimetypes=['audio', 'video'])

    # Get stream data from probe
    if probe_data.file(abspath):
        probe_streams = probe_data.get_probe()["streams"]
        probe_format = probe_data.get_probe()["format"]
    else:
        logger.debug("Probe data failed - Blocking everything.")
        data['add_file_to_pending_tasks'] = False
        return data

    # Configure settings object (maintain compatibility with v1 plugins)
    if data.get('library_id'):
        settings = Settings(library_id=data.get('library_id'))
    else:
        settings = Settings()

    stream_language = settings.get_setting('stream_language').lower()
    channels = settings.get_setting('channels')
    codec_name = settings.get_setting('codec_name').lower()

    stream = stream_to_stereo_encode(stream_language, channels, codec_name, probe_streams)
    if stream >= 0:
        data['add_file_to_pending_tasks'] = True
        logger.debug("Audio stream '{}' is '{}' and has '{}' channels and is encoded with '{}'".format(stream, stream_language, channels, codec_name))
    else:
        data['add_file_to_pending_tasks'] = False
        logger.debug("do not add file '{}' to task list - no matching streams".format(abspath))

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
    outpath = data.get('file_out')

    # Get file probe
    probe_data = Probe(logger, allowed_mimetypes=['audio', 'video'])

    if probe_data.file(abspath):
        probe_streams = probe_data.get_probe()["streams"]
        probe_format = probe_data.get_probe()["format"]
    else:
        logger.debug("Probe data failed - Nothing to encode - '{}'".format(abspath))
        return data

    total_audio_streams = -1
    for i in range(0,len(probe_streams)):
        if "codec_type" in probe_streams[i] and probe_streams[i]["codec_type"] == "audio":
            total_audio_streams += 1
    new_audio_stream = total_audio_streams + 1

    # Configure settings object (maintain compatibility with v1 plugins)
    if data.get('library_id'):
        settings = Settings(library_id=data.get('library_id'))
    else:
        settings = Settings()

    stream_language = settings.get_setting('stream_language').lower()
    channels = settings.get_setting('channels')
    codec_name = settings.get_setting('codec_name').lower()
    encoder = 'aac'
    if settings.get_setting('use_libfdk_aac'): encoder = 'libfdk_aac'

    stream = stream_to_stereo_encode(stream_language, channels, codec_name, probe_streams)
    if stream >= 0:

        # Get generated ffmpeg args
        ffmpeg_args = ['-hide_banner', '-loglevel', 'info', '-i', str(abspath), '-max_muxing_queue_size', '9999', '-map', '0', '-c', 'copy', '-map', '0:a:'+str(stream), '-c:a:'+str(new_audio_stream), encoder, '-ac', '2', '-b:a:'+str(new_audio_stream), '128k', '-y', str(outpath)]

        logger.debug("ffmpeg args: '{}'".format(ffmpeg_args))

        # Apply ffmpeg args to command
        data['exec_command'] = ['ffmpeg']
        data['exec_command'] += ffmpeg_args

        # Set the parser
        parser = Parser(logger)
        parser.set_probe(probe_data)
        data['command_progress_parser'] = parser.parse_progress
