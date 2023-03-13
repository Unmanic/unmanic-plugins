#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import logging

from unmanic.libs.unplugins.settings import PluginSettings

from remove_streams_by_codec.lib.ffmpeg import StreamMapper, Probe, Parser

# Configure plugin logger
logger = logging.getLogger("Unmanic.Plugin.remove_streams_by_codec")


class Settings(PluginSettings):
    settings = {
        "Codecs": "",
    }

    form_settings = {
        "Codecs": {
            "input_type": "textarea",
            "label":      "Codecs to remove (comma seperated)",
        },
    }

    def __init__(self, *args, **kwargs):
        super(Settings, self).__init__(*args, **kwargs)



class PluginStreamMapper(StreamMapper):
    def __init__(self, codecs):
        self.codecs = codecs
        super(PluginStreamMapper, self).__init__(logger, ['video', 'audio', 'subtitle', 'data', 'attachment'])

    def test_stream_needs_processing(self, stream_info: dict):
        """Check if this stream matches configured codecs."""
        return stream_info.get('codec_name').lower() in self.codecs

    def custom_stream_mapping(self, stream_info: dict, stream_id: int):
        """Do not map the streams matched above"""
        return {
            'stream_mapping':  [],
            'stream_encoding': [],
        }

def on_library_management_file_test(data):
    """
    Runner function - enables additional actions during the library management file tests.
    The 'data' object argument includes:
        library_id                      - The library that the current task is associated with
        path                            - String containing the full path to the file being tested.
        issues                          - List of currently found issues for not processing the file.
        add_file_to_pending_tasks       - Boolean, is the file currently marked to be added to the queue for processing.
        priority_score                  - Integer, an additional score that can be added to set the position of the new task in the task queue.
        shared_info                     - Dictionary, information provided by previous plugin runners. This can be appended to for subsequent runners.
    :param data:
    :return:
    """

    # Get codecs configured to remove
    settings = Settings(library_id=data.get('library_id'))
    codecs = settings.get_setting('Codecs').split(',')

    # Get the path to the file
    filepath = data.get('path')

    # Get file probe
    probe = Probe(logger, allowed_mimetypes=['video'])
    if not probe.file(filepath):
        # File probe failed, skip the rest of this test
        return data

    # Get stream mapper
    mapper = PluginStreamMapper(codecs)
    mapper.set_probe(probe)

    if mapper.streams_need_processing():
        # Mark this file to be added to the pending tasks
        data['add_file_to_pending_tasks'] = True
        logger.debug("File '{}' should be added to task list. Probe found streams require processing.".format(filepath))
    else:
        logger.debug("File '{}' does not contain streams require processing.".format(filepath))

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

    # Get codecs configured to remove
    settings = Settings(library_id=data.get('library_id'))
    codecs = settings.get_setting('Codecs').split(',')

    # Default to no FFMPEG command required. This prevents the FFMPEG command from running if it is not required
    data['exec_command'] = []
    data['repeat'] = False

    # Get the path to the file
    filepath = data.get('file_in')

    # Get file probe
    probe = Probe(logger, allowed_mimetypes=['video'])
    if not probe.file(filepath):
        # File probe failed, skip the rest of this test
        return data

    # Get stream mapper
    mapper = PluginStreamMapper(codecs)
    mapper.set_probe(probe)

    if mapper.streams_need_processing():
        # Set the input file
        mapper.set_input_file(filepath)

        # Set the output file
        # Do not remux the file. Keep the file out in the same container
        mapper.set_output_file(data.get('file_out'))

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
