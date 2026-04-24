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

from unmanic.libs.unplugins.settings import PluginSettings
from unmanic.libs.directoryinfo import UnmanicDirectoryInfo

from extract_srt_subtitles_to_files.lib.ffmpeg import StreamMapper, Probe, Parser

# Configure plugin logger
logger = logging.getLogger("Unmanic.Plugin.extract_srt_subtitles_to_files")


class Settings(PluginSettings):
    settings = {
        "languages_to_extract": "",
        "include_no_language_subtitles": True,
        "include_title_in_output_file_name": True
    }

    def __init__(self, *args, **kwargs):
        super(Settings, self).__init__(*args, **kwargs)

        self.form_settings = {
            "languages_to_extract": {
                "label": "Subtitle languages to extract (leave empty for all)",
            },
            "include_no_language_subtitles": {
                "label": "Include subtitles with no language tag",
            },
            "include_title_in_output_file_name": {
                "label": "Include title in output file name",
            },
        }

        # Hide 'include_no_language_subtitles' if 'languages_to_extract' is empty
        if not self.get_setting('languages_to_extract'):
            self.form_settings["include_no_language_subtitles"]["display"] = "hidden"


class PluginStreamMapper(StreamMapper):
    def __init__(self):
        super(PluginStreamMapper, self).__init__(logger, ['subtitle'])
        self.sub_streams = []
        self.settings = None
        self.used_tags = {}

    def set_settings(self, settings):
        self.settings = settings

    def _get_language_list(self):
        language_list = self.settings.get_setting('languages_to_extract')
        language_list = re.sub('\s', '-', language_list)
        languages = list(filter(None, language_list.lower().split(',')))

        return [language.strip() for language in languages]

    def test_stream_needs_processing(self, stream_info: dict):
        """Any text based will need to be processed"""

        if stream_info.get('codec_name', '').lower() not in ['srt', 'subrip', 'mov_text']:
            return False

        languages = self._get_language_list()

        # If no languages specified, extract all
        if len(languages) == 0:
            return True

        language_tag = stream_info.get('tags', {}).get('language', '').lower()

        # If there is no language tag, check if we should include it
        if not language_tag:
            return self.settings.get_setting('include_no_language_subtitles')

        return language_tag in languages

    def custom_stream_mapping(self, stream_info: dict, stream_id: int):
        stream_tags = stream_info.get('tags', {})

        # e.g. 'eng', 'fra'
        language_tag = stream_tags.get('language', '').lower()
        # e.g. 'English', 'French'
        title_tag = stream_tags.get('title', '')

        languages = self._get_language_list()

        # Skip stream if it does not match the language list
        if len(languages) > 0 and language_tag not in languages:
            # If there is no language tag, check if we should include it
            if language_tag or not self.settings.get_setting('include_no_language_subtitles'):
                return {
                    'stream_mapping':  [],
                    'stream_encoding': [],
                }

        # Find a tag for this subtitle
        subtitle_tag = ''

        if language_tag:
            subtitle_tag = "{}.{}".format(subtitle_tag, language_tag)

        if title_tag and self.settings.get_setting('include_title_in_output_file_name'):
            subtitle_tag = "{}.{}".format(subtitle_tag, title_tag)

        # If there were no tags, just number the file with prefix `.`
        if not subtitle_tag:
            subtitle_tag = ".{}".format(stream_info.get('index'))
        else:
            # It is possible that there are multiple streams with the same tag
            # If the title is not included, the tags will be the same for all such
            # streams and only the most recently extracted file will survive.
            # We make it unique by adding a `.1` and `.2` to it. However, we do
            # not add a `.1` is the tag is being used for the first time.
            base_tag = subtitle_tag
            if base_tag in self.used_tags:
                self.used_tags[base_tag] += 1
                # Used for the second time, so add 1 to the previous one
                if self.used_tags[base_tag] == 2:
                    for past_stream in self.sub_streams:
                        if past_stream.get('subtitle_tag') == base_tag:
                            past_stream['subtitle_tag'] = "{}.1".format(base_tag)
                            break
                # Add the number to the current tag
                subtitle_tag = "{}.{}".format(base_tag, self.used_tags[base_tag])
            else:
                # First time seeing this tag
                self.used_tags[base_tag] = 1

        # Ensure subtitle tag does not contain whitespace or slashes
        subtitle_tag = re.sub('\s|/|\\\\', '-', subtitle_tag)

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

def srt_already_extracted(settings, path):
    directory_info = UnmanicDirectoryInfo(os.path.dirname(path))

    try:
        already_extracted = directory_info.get('extract_srt_subtitles_to_files', os.path.basename(path))
    except NoSectionError as e:
        already_extracted = ''
    except NoOptionError as e:
        already_extracted = ''
    except Exception as e:
        logger.debug("Unknown exception {}.".format(e))
        already_extracted = ''

    if already_extracted:
        logger.debug("File's srt subtitle streams were previously extracted with {}.".format(already_extracted))
        return True

    # Default to...
    return False

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
    # Configure settings object (maintain compatibility with v1 plugins)
    if data.get('library_id'):
        settings = Settings(library_id=data.get('library_id'))
    else:
        settings = Settings()

    # Get the path to the file
    abspath = data.get('path')

    # Get file probe
    probe = Probe(logger, allowed_mimetypes=['video'])
    if 'ffprobe' in data.get('shared_info', {}):
        if not probe.set_probe(data.get('shared_info', {}).get('ffprobe')):
            # Failed to set ffprobe from shared info.
            # Probably due to it being for an incompatible mimetype declared above
            return
    elif not probe.file(abspath):
        # File probe failed, skip the rest of this test
        return
    # Set file probe to shared infor for subsequent file test runners
    if 'shared_info' in data:
        data['shared_info'] = {}
    data['shared_info']['ffprobe'] = probe.get_probe()

    # Get stream mapper
    mapper = PluginStreamMapper()
    mapper.set_settings(settings)
    mapper.set_probe(probe)

    if mapper.streams_need_processing():
        if not srt_already_extracted(settings, abspath):
            # Mark this file to be added to the pending tasks
            data['add_file_to_pending_tasks'] = True
            logger.debug("File '{}' should be added to task list. File has text subtitles that have not previously been extract to SRT files.".format(abspath))
        else:
            logger.debug("File '{}' has previously had text subtitles extracted as SRT files.".format(abspath))
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

    # Get the path to the file
    abspath = data.get('file_in')

    # Get file probe
    probe = Probe(logger, allowed_mimetypes=['video'])
    if not probe.file(abspath):
        # File probe failed, skip the rest of this test
        return

    if data.get('library_id'):
        settings = Settings(library_id=data.get('library_id'))
    else:
        settings = Settings()

    if not srt_already_extracted(settings, data.get('file_in')):
        # Get stream mapper
        mapper = PluginStreamMapper()

        mapper.set_settings(settings)
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

def on_postprocessor_task_results(data):
    """
    Runner function - provides a means for additional postprocessor functions based on the task success.

    The 'data' object argument includes:
        task_processing_success         - Boolean, did all task processes complete successfully.
        file_move_processes_success     - Boolean, did all postprocessor movement tasks complete successfully.
        destination_files               - List containing all file paths created by postprocessor file movements.
        source_data                     - Dictionary containing data pertaining to the original source file.

    :param data:
    :return:

    """
    # We only care that the task completed successfully.
    # If a worker processing task was unsuccessful, dont mark the file streams as kept
    # TODO: Figure out a way to know if a file's streams were kept but another plugin was the
    #   cause of the task processing failure flag
    if not data.get('task_processing_success'):
        return data

    # Configure settings object (maintain compatibility with v1 plugins)
    if data.get('library_id'):
        settings = Settings(library_id=data.get('library_id'))
    else:
        settings = Settings()

    abspath = data.get('source_data').get('abspath')
    probe_data=Probe(logger, allowed_mimetypes=['video'])
    if probe_data.file(abspath):
        probe_streams=probe_data.get_probe()["streams"]
    else:
        probe_streams=[]

    # Loop over the destination_files list and update the directory info file for each one
    for destination_file in data.get('destination_files'):
        langs = ""
        langs = settings.get_setting('languages_to_extract')
        if probe_streams:
            subs = [probe_streams[i]["tags"]["language"] for i in range(len(probe_streams)) if probe_streams[i]["codec_type"] == "subtitle" and "tags" in probe_streams[i] and "language" in probe_streams[i]["tags"]]
            if langs:
                subs = [i for i in subs if i in langs]
            subs = ' '.join(subs)
        else:
            subs="true"
        directory_info = UnmanicDirectoryInfo(os.path.dirname(destination_file))
        directory_info.set('extract_srt_subtitles_to_files', os.path.basename(destination_file), subs)
        directory_info.save()
        logger.info("SRT subtitles processed for '{}' and recorded in .unmanic file.".format(destination_file))

    return data
