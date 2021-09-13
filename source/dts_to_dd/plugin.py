#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
    unmanic-plugins.plugin.py

    Written by:               Josh.5 <jsunnex@gmail.com>
    Date:                     04 Jun 2021, (7:10 PM)

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

from dts_to_dd.lib.ffmpeg import StreamMapper, Probe, Parser

# Configure plugin logger
logger = logging.getLogger("Unmanic.Plugin.dts_to_dd")


class Settings(PluginSettings):
    settings = {
        'downmix_dts_hd_ma': False
    }
    form_settings = {
        "downmix_dts_hd_ma": {
            "label": "Downmix DTS-HD Master Audio (max 6 channels)?",
        },
    }


class PluginStreamMapper(StreamMapper):
    def __init__(self):
        super(PluginStreamMapper, self).__init__(logger, ['audio'])

    @staticmethod
    def should_process_dts_stream(probe_stream):
        settings = Settings()
        if probe_stream.get('profile').lower() == 'dts':
            # Process all DTS tracks
            return True

        if probe_stream.get('profile').lower() == 'dts-hd ma':
            # This stream is DTS-HD Master Audio. Check if configured to downmix Master Audio
            if settings.get_setting('downmix_dts_hd_ma'):
                return True

        # Default to
        return False

    @staticmethod
    def get_ac3_equivalent_bit_rate(dts_profile, dts_bit_rate):
        # If no bit rate is provided, assume the highest for Dolby Digital
        if not dts_bit_rate:
            logger.info("Stream did not contain 'bit_rate'. Setting max Dolby Digital bit rate (640k).")
            return '640k'

        # If this is DTS-HD MA, return max bit rate for Dolby Digital
        if dts_profile == 'DTS-HD MA':
            logger.info("Stream contains DTS-HD Master Audio. Setting max Dolby Digital bit rate (640k).")
            return '640k'

        # Determine bitrate based on source bitrate
        if int(dts_bit_rate) <= 768000:
            logger.info("Stream 'bit_rate' is <= 768kb/s. Setting Dolby Digital bit rate to 448k.")
            return '448k'
        elif int(dts_bit_rate) <= 1536000:
            logger.info("Stream 'bit_rate' is <= 1.5mb/s. Setting max Dolby Digital bit rate (640k).")
            return '640k'

        # Default to best quality
        logger.info("Stream 'bit_rate' could not be matched directly ({}). Setting max Dolby Digital bit rate.".format(
            dts_bit_rate))
        return '640k'

    def test_stream_needs_processing(self, stream_info: dict):
        if stream_info.get('codec_name').lower() == "dts":
            if self.should_process_dts_stream(stream_info):
                return True
        return False

    def custom_stream_mapping(self, stream_info: dict, stream_id: int):
        # Get the equivalent bitrate for a AC3 stream based on the bit rate of the original DTS stream
        bit_rate = self.get_ac3_equivalent_bit_rate(stream_info.get('profile'), stream_info.get('bit_rate'))
        # Add a codec flag for encoding this stream with ac3 encoder
        return {
            'stream_mapping':  ['-map', '0:a:{}'.format(stream_id)],
            'stream_encoding': [
                '-c:a:{}'.format(stream_id), 'ac3',
                '-b:a:{}'.format(stream_id), bit_rate
            ]
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
    probe = Probe(logger)
    if not probe.file(abspath):
        # File probe failed, skip the rest of this test
        return data

    # Get stream mapper
    mapper = PluginStreamMapper()
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
    # DEPRECIATED: 'exec_ffmpeg' kept for legacy Unmanic versions
    data['exec_ffmpeg'] = False

    # Get the path to the file
    abspath = data.get('file_in')

    # Get file probe
    probe = Probe(logger)
    if not probe.file(abspath):
        # File probe failed, skip the rest of this test
        return data

    # Get stream mapper
    mapper = PluginStreamMapper()
    mapper.set_probe(probe)

    if mapper.streams_need_processing():
        # Set the input file
        mapper.set_input_file(abspath)

        # Set the output file
        # Do not remux the file. Keep the file out in the same container
        split_file_in = os.path.splitext(abspath)
        split_file_out = os.path.splitext(data.get('file_out'))
        mapper.set_output_file("{}{}".format(split_file_out[0], split_file_in[1]))

        # Get generated ffmpeg args
        ffmpeg_args = mapper.get_ffmpeg_args()

        # Apply ffmpeg args to command
        data['exec_command'] = ['ffmpeg']
        data['exec_command'] += ffmpeg_args
        # DEPRECIATED: 'ffmpeg_args' kept for legacy Unmanic versions
        data['ffmpeg_args'] = ffmpeg_args

        # Set the parser
        parser = Parser(logger)
        parser.set_probe(probe)
        data['command_progress_parser'] = parser.parse_progress

    return data
