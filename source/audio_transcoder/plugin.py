#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
    plugins.plugin.py

    Written by:               Josh.5 <jsunnex@gmail.com>
    Date:                     31 August 2022, (9:55 AM)

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
from configparser import NoOptionError, NoSectionError

from audio_transcoder.lib import plugin_stream_mapper, tools
from audio_transcoder.lib.encoders.ac3 import Ac3Encoder
from audio_transcoder.lib.encoders.aac import AacEncoder
from audio_transcoder.lib.encoders.eac3 import Eac3Encoder
from audio_transcoder.lib.encoders.flac import FlacEncoder
from audio_transcoder.lib.encoders.lame import LameEncoder
from audio_transcoder.lib.encoders.opus import OpusEncoder
from audio_transcoder.lib.ffmpeg import Parser, Probe
from audio_transcoder.lib.global_settings import GlobalSettings
from unmanic.libs.directoryinfo import UnmanicDirectoryInfo
from unmanic.libs.unplugins.settings import PluginSettings

# Configure plugin logger
logger = logging.getLogger("Unmanic.Plugin.audio_transcoder")

class Settings(PluginSettings):
    def __init__(self, *args, **kwargs):
        self.apply_default_fallbacks = kwargs.pop('apply_default_fallbacks', True)
        super(Settings, self).__init__(*args, **kwargs)
        self.settings = self.__build_settings_object()
        self.global_settings = GlobalSettings(self)
        self.form_settings = self.__build_form_settings_object()

    def __build_form_settings_object(self):
        return_values = {}
        for setting in self.settings:
            selected_encoder = tools.available_encoders(settings=self).get(self.get_setting('audio_encoder'))
            setting_form_settings = {
                "display": "hidden"
            }
            if hasattr(selected_encoder, 'get_{}_form_settings'.format(setting)):
                getter = getattr(selected_encoder, 'get_{}_form_settings'.format(setting))
                if callable(getter):
                    setting_form_settings = getter()
            elif hasattr(self.global_settings, 'get_{}_form_settings'.format(setting)):
                getter = getattr(self.global_settings, 'get_{}_form_settings'.format(setting))
                if callable(getter):
                    setting_form_settings = getter()
            return_values[setting] = setting_form_settings
        return return_values

    def __encoder_settings_object(self):
        encoder_settings = {}
        encoder_libs = [
            LameEncoder(self),
            AacEncoder(self),
            FlacEncoder(self),
            OpusEncoder(self),
            Ac3Encoder(self),
            Eac3Encoder(self),
        ]
        for encoder_lib in encoder_libs:
            encoder_settings.update(encoder_lib.options())
        return encoder_settings

    def __build_settings_object(self):
        global_settings = GlobalSettings.options()
        main_options = global_settings.get('main_options')
        encoder_selection = global_settings.get('encoder_selection')
        encoder_settings = self.__encoder_settings_object()
        advanced_input_options = global_settings.get('advanced_input_options')
        output_settings = global_settings.get('output_settings')
        filter_settings = global_settings.get('filter_settings')
        smart_output_target = global_settings.get('smart_output_target')
        return {
            **main_options,
            **encoder_selection,
            **encoder_settings,
            **advanced_input_options,
            **output_settings,
            **filter_settings,
            **smart_output_target,
        }


def file_marked_as_force_transcoded(path, file_metadata=None):
    if file_metadata:
        try:
            metadata = file_metadata.get()
            if metadata.get('force_transcoded') is True or metadata.get('status') == 'force_transcoded':
                return True
        except Exception as e:
            logger.debug("Unable to read UnmanicFileMetadata for '%s': %s", path, e)

    directory_info = UnmanicDirectoryInfo(os.path.dirname(path))
    try:
        has_been_force_transcoded = directory_info.get('audio_transcoder', os.path.basename(path))
    except NoSectionError:
        has_been_force_transcoded = ''
    except NoOptionError:
        has_been_force_transcoded = ''
    except Exception as e:
        logger.debug("Unknown exception %s.", e)
        has_been_force_transcoded = ''

    if has_been_force_transcoded == 'force_transcoded':
        return True
    return False


def on_library_management_file_test(data, task_data_store=None, file_metadata=None):
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
    settings = Settings(library_id=data.get('library_id'), apply_default_fallbacks=False)
    abspath = data.get('path')

    probe = Probe.init_probe(data, logger, allowed_mimetypes=['audio', 'video'])
    if not probe or not probe.file(abspath):
        return

    mapper = plugin_stream_mapper.PluginStreamMapper()
    mapper.set_default_values(settings, abspath, probe)

    if mapper.streams_need_processing():
        if file_marked_as_force_transcoded(abspath, file_metadata=file_metadata) and mapper.forced_encode:
            logger.debug(
                "File '%s' has been previously marked as forced transcoded. Plugin found streams require processing, but will ignore this file.",
                abspath)
            return
        data['add_file_to_pending_tasks'] = True
        logger.debug("File '%s' should be added to task list. Plugin found streams require processing.", abspath)
    else:
        logger.debug("File '%s' does not contain streams require processing.", abspath)


def on_worker_process(data, task_data_store=None, file_metadata=None):
    """
    Runner function - enables additional configured processing jobs during the worker stages of a task.

    The 'data' object argument includes:
        task_id                 - Integer, unique identifier of the task.
        worker_log              - Array, the log lines that are being tailed by the frontend. Can be left empty.
        library_id              - Number, the library that the current task is associated with.
        exec_command            - Array, a subprocess command that Unmanic should execute. Can be empty.
        current_command         - Array, shared list for updating the worker's "current command" text in the UI (last entry wins).
        command_progress_parser - Function, a function that Unmanic can use to parse the STDOUT of the command to collect progress stats. Can be empty.
        file_in                 - String, the source file to be processed by the command.
        file_out                - String, the destination that the command should output (may be the same as the file_in if necessary).
        original_file_path      - String, the absolute path to the original file.
        repeat                  - Boolean, should this runner be executed again once completed with the same variables.

    :param data:
    :return:
    """
    data['exec_command'] = []
    data['repeat'] = False

    worker_log = data.get('worker_log')
    settings = Settings(library_id=data.get('library_id'), apply_default_fallbacks=False)
    abspath = data.get('file_in')

    tools.append_worker_log(worker_log, "Probing file: {}".format(abspath))
    probe = Probe(logger, allowed_mimetypes=['audio', 'video'])
    if not probe.file(abspath):
        tools.append_worker_log(worker_log, "Probe failed - skipping file")
        return

    mapper = plugin_stream_mapper.PluginStreamMapper(worker_log=worker_log)
    mapper.set_default_values(settings, abspath, probe)

    tools.append_worker_log(worker_log, "Checking what streams need processing...")
    needs_processing = mapper.streams_need_processing()
    if needs_processing:
        if file_marked_as_force_transcoded(abspath, file_metadata=file_metadata) and mapper.forced_encode:
            tools.append_worker_log(worker_log, "File previously force transcoded - skipping")
            return

        data['file_out'] = mapper.set_output_file(data.get('file_out'))
        tools.append_worker_log(worker_log, "Output file resolved to: {}".format(data.get('file_out')))

        tools.append_worker_log(worker_log, "Generating FFmpeg command...")
        mapper.enable_execution_stage()
        mapper.streams_need_processing()
        ffmpeg_args = mapper.get_ffmpeg_args()

        data['exec_command'] = ['ffmpeg']
        data['exec_command'] += ffmpeg_args

        parser = Parser(logger)
        parser.set_probe(probe)
        data['command_progress_parser'] = parser.parse_progress

        if settings.get_setting('force_transcode'):
            cache_directory = os.path.dirname(data.get('file_out'))
            if not os.path.exists(cache_directory):
                os.makedirs(cache_directory)
            with open(os.path.join(cache_directory, '.force_transcode'), 'w') as f:
                f.write('')
    else:
        tools.append_worker_log(worker_log, "No streams require processing - no FFmpeg command generated")

    return


def on_postprocessor_task_results(data, task_data_store=None, file_metadata=None):
    """
    Runner function - provides a means for additional postprocessor functions based on the task success.

    The 'data' object argument includes:
        library_id                      - The library that the current task is associated with.
        task_id                         - Integer, unique identifier of the task.
        task_type                       - String, "local" or "remote".
        final_cache_path                - The path to the final cache file that was then used as the source for all destination files.
        task_processing_success         - Boolean, did all task processes complete successfully.
        file_move_processes_success     - Boolean, did all postprocessor movement tasks complete successfully.
        destination_files               - List containing all file paths created by postprocessor file movements.
        source_data                     - Dictionary containing data pertaining to the original source file.
        start_time                      - Float, UNIX timestamp when the task began.
        finish_time                     - Float, UNIX timestamp when the task completed.

    :param data:
    :return:
    """
    settings = Settings(library_id=data.get('library_id'), apply_default_fallbacks=False)

    original_source_path = data.get('source_data', {}).get('abspath')
    if not original_source_path:
        logger.error("Provided 'source_data' is missing the source file abspath data.")
        return

    if not data.get('destination_files'):
        logger.error("No destination files found.")
        return

    transcoded_file_path = data['destination_files'][0]

    if settings.get_setting('force_transcode'):
        cache_directory = os.path.dirname(data.get('final_cache_path'))
        if os.path.exists(os.path.join(cache_directory, '.force_transcode')):
            if file_metadata:
                file_metadata.set({
                    'force_transcoded': True,
                    'status': 'force_transcoded',
                })
            else:
                directory_info = UnmanicDirectoryInfo(os.path.dirname(transcoded_file_path))
                directory_info.set('audio_transcoder', os.path.basename(transcoded_file_path), 'force_transcoded')
                directory_info.save()
            logger.debug("Ignore on next scan written for '%s'.", transcoded_file_path)
