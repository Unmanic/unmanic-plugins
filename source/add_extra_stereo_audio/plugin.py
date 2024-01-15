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
import iso639

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
        "remove_original_multichannel_audio": False,
        "make_xtra_stereo_default": True,
        "move_to_first"           : True,
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
            },
            "remove_original_multichannel_audio":               {
                "label": "check if you want to remove the original multichannel audio stream",
            },
            "make_xtra_stereo_default":      {
                "label": "check if you want the new stereo audio to be the default audio upon playing",
            },
            "move_to_first":                 {
                "label": "check if you want to move the stereo audio to first audio stream"
            }
        }

def stream_to_stereo_encode(stream_language, channels, codec_name, probe_streams):
    audio_stream = -1

    # first loop skips any streams that have 'commentary' (any capitalization) in the stream's tag title and skips all further testing if a 2 channel, stereo aac stream exists with language matching configured language
    for  i in range(0, len(probe_streams)):
        if "codec_type" in probe_streams[i] and probe_streams[i]["codec_type"] == "audio":
            if "tags" in probe_streams[i] and "title" in probe_streams[i]["tags"] and 'commentary' in probe_streams[i]["tags"]["title"].lower():
                continue
            try:
                if probe_streams[i]["codec_name"] == "aac" and probe_streams[i]["channels"] == 2 and probe_streams[i]["channel_layout"] == "stereo" and probe_streams[i]["tags"]["language"] == stream_language: return -1
            except KeyError:
                continue

    # if not skipped per above, find the first multichannel audio stream with language matching the configured language OR
    # if all config parameters entered find the first multichannel audio with language, # channels, and codec_name matching configuration settings
    for i in range(0, len(probe_streams)):
        if "codec_type" in probe_streams[i] and probe_streams[i]["codec_type"] == "audio":
            audio_stream += 1
            if "tags" in probe_streams[i] and "language" in probe_streams[i]["tags"]:
                logger.debug("i '{}', probe_streams[i][codec_type]: '{}', probe_streams[i][channels]: '{}', probe_streams[i][tags][language]: '{}', probe_streams[i][codec_name]: '{}'".format(i, probe_streams[i]["codec_type"], probe_streams[i]["channels"], probe_streams[i]["tags"]["language"], probe_streams[i]["codec_name"]))
            else:
                logger.debug("i '{}', probe_streams[i][codec_type]: '{}', probe_streams[i][channels]: '{}', probe_streams[i][codec_name]: '{}', No audio language tags".format(i, probe_streams[i]["codec_type"], probe_streams[i]["channels"], probe_streams[i]["codec_name"]))
                continue
            if channels == '' or codec_name == '':
                if probe_streams[i]["tags"]["language"] == stream_language and int(probe_streams[i]["channels"]) > 4:
                    return audio_stream
            else:
                try:
                    if str(probe_streams[i]["channels"]) == channels and probe_streams[i]["tags"]["language"] == stream_language and probe_streams[i]["codec_name"] == codec_name:
                        return audio_stream
                except KeyError:
                    logger.debug("Should not get here and generate a KeyError - probe_streams[i]: '{}'".format(probe_streams[i]))
                    continue

    logger.debug("No audio stream selected.  audio_stream counter: '{}'".format(audio_stream))
    return -1


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
    logger.debug("stream to stereo encode: '{}'".format(stream))
    if stream >= 0:
        data['add_file_to_pending_tasks'] = True
        if stream_language == '' or channels == '' or codec_name == '':
            logger.debug("Audio stream '{}' is multichannel audio - convert stream".format(stream))
        else:
            logger.debug("Audio stream '{}' is '{}' and has '{}' channels and is encoded with '{}' - convert stream".format(stream, stream_language, channels, codec_name))
    else:
#        data['add_file_to_pending_tasks'] = False
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
    remove_original = settings.get_setting('remove_original_multichannel_audio')
    set_default_audio_to_new_stream = settings.get_setting('make_xtra_stereo_default')
    move_to_first = settings.get_setting('move_to_first')

    stream = stream_to_stereo_encode(stream_language, channels, codec_name, probe_streams)
    if stream >= 0:

        # initialize ffmpeg_args
        ffmpeg_args = ['-hide_banner', '-loglevel', 'info', '-i', str(abspath), '-max_muxing_queue_size', '9999']

        # Get generated ffmpeg args
        if not remove_original and not move_to_first:
            ffmpeg_args += ['-map', '0', '-c', 'copy', '-map', '0:a:'+str(stream), '-c:a:'+str(new_audio_stream), encoder, '-ac', '2', '-b:a:'+str(new_audio_stream), '128k']
        elif remove_original and not move_to_first:
            ffmpeg_args += ['-map', '0:s?', '-c:s', 'copy', '-map', '0:d?', '-c:d', 'copy', '-map', '0:t?', '-c:t', 'copy', '-map', '0:v', '-c:v', 'copy']
            for astream in range(0, total_audio_streams+1):
                if astream ==  stream:
                    ffmpeg_args += ['-map', '0:a:'+str(stream), '-c:a:'+str(stream), encoder, '-ac', '2', '-b:a:'+str(stream), '128k']
                    new_audio_stream = astream
                else:
                    ffmpeg_args += ['-map', '0:a:'+str(astream), '-c:a:'+str(astream), 'copy']
        elif move_to_first:
            new_audio_stream = 0
            ffmpeg_args += ['-map', '0:s?', '-c:s', 'copy', '-map', '0:d?', '-c:d', 'copy', '-map', '0:t?', '-c:t', 'copy', '-map', '0:v', '-c:v', 'copy']

            # place stream_to_stereo_encode as 1st audio:
            ffmpeg_args += ['-map', '0:a:'+str(stream), '-c:a:0', encoder, '-ac', '2', '-b:a:0', '128k']

            # iterate over remaining streams and copy unless it's to be removed
            skip_original = 0
            for astream in range(0, total_audio_streams+1):
                if astream == stream and remove_original:
                    skip_original = 1
                else:
                    ffmpeg_args += ['-map', '0:a:'+str(astream), '-c:a:'+str(astream + 1 - skip_original), 'copy']

        if set_default_audio_to_new_stream:
            ffmpeg_args += ['-disposition:a', '-default', '-disposition:a:'+str(new_audio_stream), 'default']

        logger.debug("stream_language: '{}'".format(stream_language))

        try:
            if len(stream_language) == 2:
                lang = iso639.Language.from_part1(stream_language)
            elif len(stream_language) == 3:
                lang = iso639.Language.from_part3(stream_language)
        except iso639.language.LanguageNotFoundError:
            logger.info("iso 639 exception")
            lang = stream_language

        if lang != stream_language: lang = lang.name

        logger.debug("lang: '{}'".format(lang))
        ffmpeg_args += ['-metadata:s:a:' + str(new_audio_stream), 'title=' + str(lang) + ' (' +str(encoder).upper() + ' Stereo)', '-y', str(outpath)]

        logger.debug("ffmpeg args: '{}'".format(ffmpeg_args))

        # Apply ffmpeg args to command
        data['exec_command'] = ['ffmpeg']
        data['exec_command'] += ffmpeg_args

        # Set the parser
        parser = Parser(logger)
        parser.set_probe(probe_data)
        data['command_progress_parser'] = parser.parse_progress

