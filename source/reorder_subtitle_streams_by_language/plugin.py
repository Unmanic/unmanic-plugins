#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
    Written by:               Josh.5 <jsunnex@gmail.com>
    Date:                     24 March 2021, (9:34 PM)
 
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
import mimetypes
import os

from unmanic.libs import unffmpeg
from unmanic.libs.unplugins.settings import PluginSettings

# Configure plugin logger
logger = logging.getLogger("Unmanic.Plugin.reorder_subtitle_streams_by_language")


class Settings(PluginSettings):
    settings = {
        "Search String": "en",
    }


def get_file_probe(file_path):
    # Ensure file exists
    if not os.path.exists(file_path):
        return {}

    # Only run this check against video/audio/image MIME types
    mimetypes.init()
    file_type = mimetypes.guess_type(file_path)[0]
    # If the file has no MIME type then it cannot be tested
    if file_type is None:
        return {}
    # Make sure the MIME type is either audio, video or image
    file_type_category = file_type.split('/')[0]
    if file_type_category not in ['audio', 'video', 'image']:
        return {}

    try:
        # Get the file probe info
        return unffmpeg.Info().file_probe(file_path)
    except unffmpeg.exceptions.ffprobe.FFProbeError as e:
        return {}
    except Exception as e:
        return {}


def check_stream_contains_search_string(probe_stream, search_string):
    # Check if tags exist in streams with the key "title" or "language"
    stream_tags = probe_stream.get('tags')
    if stream_tags and True in list(k.lower() in ['title', 'language'] for k in stream_tags):
        # Check if tag matches the "Search String"
        if search_string.lower() in stream_tags.get('language', '').lower():
            # Found a matching stream in language tag
            return True
        elif search_string in stream_tags.get('title', '').lower():
            # Found a matching stream in title tag
            return True
    return False


def get_stream_mapping(file_probe_streams):
    # Read plugin settings
    settings = Settings()
    search_string = settings.get_setting('Search String')

    # Map the streams into four arrays that will be placed to gether in the correct order.
    first_stream_mapping = []
    search_string_stream_mapping = []
    unmatched_stream_mapping = []
    last_stream_mapping = []

    video_stream_count = 0
    audio_stream_count = 0
    subtitle_stream_count = 0

    found_search_string_streams = False
    for probe_stream in file_probe_streams:
        # Map the video stream
        if probe_stream.get('codec_type').lower() == "video":
            if not found_search_string_streams:
                first_stream_mapping += ['-map', '0:v:{}'.format(video_stream_count)]
            else:
                last_stream_mapping += ['-map', '0:v:{}'.format(video_stream_count)]
            video_stream_count += 1
            continue

        # Map the audio streams
        if probe_stream.get('codec_type').lower() == "audio":
            if not found_search_string_streams:
                first_stream_mapping += ['-map', '0:a:{}'.format(audio_stream_count)]
            else:
                last_stream_mapping += ['-map', '0:a:{}'.format(audio_stream_count)]
            audio_stream_count += 1
            continue

        # Map the subtitle streams in their correct lists
        if probe_stream.get('codec_type').lower() == "subtitle":
            found_search_string_streams = True
            if check_stream_contains_search_string(probe_stream, search_string):
                search_string_stream_mapping += ['-map', '0:s:{}'.format(subtitle_stream_count)]
            else:
                unmatched_stream_mapping += ['-map', '0:s:{}'.format(subtitle_stream_count)]
            subtitle_stream_count += 1
            continue

    return {
        'first_stream_mapping':         first_stream_mapping,
        'search_string_stream_mapping': search_string_stream_mapping,
        'unmatched_stream_mapping':     unmatched_stream_mapping,
        'last_stream_mapping':          last_stream_mapping
    }


def file_should_be_processed(search_string_stream_mapping, unmatched_stream_mapping):
    """
    Ensure we found some streams matching our search and that we are actually going to reorder them...
    If we found both a list of matching streams AND a list of streams that were unmatched,
      then the streams in this file will be reordered.
    If only matched streams were found, then the list of streams will remain the same as all streams matched the
      search string.
    If only unmatched streams were found, then the list of streams will remain the same as nothing matched the
      search string.
    If matches were found for both, but the new mapped order of streams will be the same as the original streams,
      then this file will not be reordered.

    :param search_string_stream_mapping:
    :param unmatched_stream_mapping:
    :return:
    """
    result = False
    # Test if there were any matches against the search string
    if search_string_stream_mapping and unmatched_stream_mapping:
        logger.info("Streams were found matching the search string")
        # Test if the mapping is already in the correct order
        counter = 0
        for item in search_string_stream_mapping + unmatched_stream_mapping:
            if '-map' in item:
                continue
            original_position = item.split(':')[-1]
            if int(original_position) != int(counter):
                logger.info("The new order for the mapped streams will differ from the source file")
                result = True
                break
            counter += 1
    return result


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
    # Get file probe
    file_probe = get_file_probe(data.get('path'))
    if not file_probe:
        # File probe failed, skip the rest of this test
        return data

    # Get stream mapping
    stream_mapping = get_stream_mapping(file_probe.get('streams'))
    search_string_stream_mapping = stream_mapping.get('search_string_stream_mapping', [])
    unmatched_stream_mapping = stream_mapping.get('unmatched_stream_mapping', [])

    if file_should_be_processed(search_string_stream_mapping, unmatched_stream_mapping):
        # Mark this file to be added to the pending tasks
        data['add_file_to_pending_tasks'] = True
        logger.debug("File '{}' should be added to task list. Audio streams are not in the correct order".format(
            data.get('path')))

    return data


def on_worker_process(data):
    """
    Runner function - carries out additional processing during the worker stages of a task.

    The 'data' object argument includes:
        exec_ffmpeg             - Boolean, should Unmanic run FFMPEG with the data returned from this plugin.
        file_probe              - A dictionary object containing the current file probe state.
        ffmpeg_args             - A list of Unmanic's default FFMPEG args.
        file_in                 - The source file to be processed by the FFMPEG command.
        file_out                - The destination that the FFMPEG command will output.

    :param data:
    :return:
    """
    # Default to run FFMPEG command unless no stream is found matching the "Search String"
    data['exec_ffmpeg'] = True

    # Check file probe for title metadata in the video
    file_probe = data.get('file_probe')
    file_probe_streams = file_probe.get('streams')

    # Get stream mapping
    stream_mapping = get_stream_mapping(file_probe_streams)
    first_stream_mapping = stream_mapping.get('first_stream_mapping', [])
    search_string_stream_mapping = stream_mapping.get('search_string_stream_mapping', [])
    unmatched_stream_mapping = stream_mapping.get('unmatched_stream_mapping', [])
    last_stream_mapping = stream_mapping.get('last_stream_mapping', [])

    # Ensure we found some streams matching our search and we need to process the file to reorder them
    if not file_should_be_processed(search_string_stream_mapping, unmatched_stream_mapping):
        # Prevent FFMPEG command from running on this file from this plugin
        data['exec_ffmpeg'] = False

    if data['exec_ffmpeg']:
        # Build ffmpeg args and add them to the return data
        data['ffmpeg_args'] = [
            '-i',
            data.get('file_in'),
            '-hide_banner',
            '-loglevel',
            'info',
        ]
        data['ffmpeg_args'] += ['-c', 'copy']
        data['ffmpeg_args'] += first_stream_mapping
        data['ffmpeg_args'] += search_string_stream_mapping
        data['ffmpeg_args'] += unmatched_stream_mapping
        data['ffmpeg_args'] += last_stream_mapping

        # Do not remux the file. Keep the file out in the same container
        split_file_in = os.path.splitext(data.get('file_in'))
        split_file_out = os.path.splitext(data.get('file_out'))
        data['file_out'] = "{}{}".format(split_file_out[0], split_file_in[1])

        data['ffmpeg_args'] += ['-y', data.get('file_out')]

    return data
