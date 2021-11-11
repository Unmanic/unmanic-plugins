#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
    plugins.__init__.py

    Written by:               Josh.5 <jsunnex@gmail.com>
    Date:                     28 Aug 2021, (11:55 PM)

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
import json
import logging
import mimetypes
import os

from unmanic.libs.unplugins.settings import PluginSettings

from video_remuxer.lib.ffmpeg import StreamMapper, Probe, Parser

# Configure plugin logger
logger = logging.getLogger("Unmanic.Plugin.video_remuxer")


class Settings(PluginSettings):
    settings = {
        "dest_container": "mkv",
    }

    def __init__(self):
        self.form_settings = {
            "dest_container": self.__set_dest_container_form_settings()
        }

    def __set_dest_container_form_settings(self):
        containers_data = self.__read_containers_data()
        select_options = []
        for cd_item in containers_data:
            if cd_item == "template":
                continue
            select_options.append(
                {
                    'value': cd_item,
                    'label': containers_data[cd_item].get('label'),
                }
            )
        values = {
            "label":          "Set the output container",
            "input_type":     "select",
            "select_options": select_options,
        }
        return values

    def __read_containers_data(self):
        containers_file = os.path.join(self.get_plugin_directory(), 'lib', 'containers.json')
        with open(containers_file) as infile:
            containers_data = json.load(infile)
        return containers_data

    def get_configured_container_data(self):
        dest_container = self.get_setting('dest_container')
        containers_data = self.__read_containers_data()
        dest_container = containers_data.get(dest_container)
        if not dest_container:
            # Load defaults - MKV
            dest_container = containers_data.get('mkv')
        return dest_container


class PluginStreamMapper(StreamMapper):
    def __init__(self):
        super(PluginStreamMapper, self).__init__(logger, ['video', 'audio', 'subtitle', 'data', 'attachment'])
        self.settings = None
        self.container_data = None

    def test_stream_needs_processing(self, stream_info: dict):
        if not self.container_data:
            settings = Settings()
            self.container_data = settings.get_configured_container_data()

        # Check if codec type is supported
        codec_type = stream_info.get('codec_type').lower()
        if codec_type not in self.container_data.get('codec_types'):
            return True

        # Check if the codec name is supported for this container
        codec_name = stream_info.get('codec_name').lower()
        if codec_name not in self.container_data.get('codec_names', {}).get(codec_type, []):
            return True

        # Stream will be copied over
        return False

    def custom_stream_mapping(self, stream_info: dict, stream_id: int):
        ident = {
            'video':      'v',
            'audio':      'a',
            'subtitle':   's',
            'data':       'd',
            'attachment': 't'
        }
        if not self.container_data:
            settings = Settings()
            self.container_data = settings.get_configured_container_data()

        # If codec type is not supported, remove it
        codec_type = stream_info.get('codec_type').lower()
        if codec_type not in self.container_data.get('codec_types'):
            return {
                'stream_mapping':  [],
                'stream_encoding': [],
            }

        # If codec is not supported by the container or able to be transcoded, remove it
        # Else if it is not supported by the container but is able to be transcoded, update it to the default
        codec_name = stream_info.get('codec_name').lower()
        if codec_name in self.container_data.get('remove_codec_names', {}).get(codec_type, []):
            return {
                'stream_mapping':  [],
                'stream_encoding': [],
            }
        elif codec_name not in self.container_data.get('codec_names', {}).get(codec_type, []):
            stream_encoding = ['-c:{}:{}'.format(ident.get(codec_type), stream_id)]
            # Fetch the default encoder params
            default_encoder_params = self.container_data.get('default_encoder_params', {}).get(codec_type, [])
            # Append to the stream encoding
            stream_encoding += default_encoder_params
            if not default_encoder_params:
                # This container does not support this stream type and it is not configured to be able to convert it,
                # Remove this stream
                return {
                    'stream_mapping':  [],
                    'stream_encoding': [],
                }
            else:
                return {
                    'stream_mapping':  ['-map', '0:{}:{}'.format(ident.get(codec_type), stream_id)],
                    'stream_encoding': stream_encoding,
                }

        # Code will never get here - throw exception if it did
        raise Exception("Failed to map container remux params for stream - ({},{})".format(codec_type, codec_name))


def correct_mimetypes():
    mimetypes.add_type('video/x-m4v', '.m4v')


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
    correct_mimetypes()
    if not probe.file(abspath):
        # File probe failed, skip the rest of this test
        return data

    # Get stream mapper
    mapper = PluginStreamMapper()
    mapper.set_probe(probe)

    # Set the input file
    mapper.set_input_file(abspath)

    settings = Settings()
    container_data = settings.get_configured_container_data()
    container_extension = container_data.get('extension')

    if mapper.container_needs_remuxing(container_extension):
        # Mark this file to be added to the pending tasks
        data['add_file_to_pending_tasks'] = True
        logger.debug("File '{}' should be added to task list. Probe found file needs to be processed.".format(abspath))
    else:
        logger.debug("File '{}' is already the required format.".format(abspath))

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
    correct_mimetypes()
    if not probe.file(abspath):
        # File probe failed, skip the rest of this test
        return data

    # Get stream mapper
    mapper = PluginStreamMapper()
    mapper.set_probe(probe)

    # Set the input file
    mapper.set_input_file(abspath)

    settings = Settings()
    container_data = settings.get_configured_container_data()
    container_extension = container_data.get('extension')

    if mapper.container_needs_remuxing(container_extension):
        # Map streams (copy from source to destination)
        mapper.streams_need_processing()

        # Set the input file
        mapper.set_input_file(abspath)

        # Set the output file
        split_file_out = os.path.splitext(data.get('file_out'))
        new_file_out = "{}.{}".format(split_file_out[0], container_extension.lstrip('.'))
        mapper.set_output_file(new_file_out)
        data['file_out'] = new_file_out

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
