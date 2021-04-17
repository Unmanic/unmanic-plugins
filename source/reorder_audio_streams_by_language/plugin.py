#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import os

from unmanic.libs.unplugins.settings import PluginSettings


class Settings(PluginSettings):
    settings = {
        "Search String": "en",
    }


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
    # Read plugin settings
    settings = Settings()
    search_string = settings.get_setting('Search String')

    # Default to run FFMPEG command unless no stream is found matching the "Search String"
    data['exec_ffmpeg'] = True

    # Check file probe for title metadata in the video
    file_probe = data.get('file_probe')
    file_probe_streams = file_probe.get('streams')

    # Map the streams into four arrays that will be placed to gether in the correct order.
    first_stream_mapping = []
    search_string_stream_mapping = []
    other_stream_mapping = []
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

        # Map the subtitle streams
        if probe_stream.get('codec_type').lower() == "subtitle":
            if not found_search_string_streams:
                first_stream_mapping += ['-map', '0:s:{}'.format(subtitle_stream_count)]
            else:
                last_stream_mapping += ['-map', '0:s:{}'.format(subtitle_stream_count)]
            subtitle_stream_count += 1
            continue

        # Map the audio streams in their correct lists
        if probe_stream.get('codec_type').lower() == "audio":
            found_search_string_streams = True
            if check_stream_contains_search_string(probe_stream, search_string):
                search_string_stream_mapping += ['-map', '0:a:{}'.format(audio_stream_count)]
            else:
                other_stream_mapping += ['-map', '0:a:{}'.format(audio_stream_count)]
            audio_stream_count += 1
            continue

    # Ensure we found some streams matching our search
    if not search_string_stream_mapping:
        # Prevent FFMPEG command from running on this file from this plugin
        data['exec_ffmpeg'] = False

    # TODO Check if the streams are already in order

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
        data['ffmpeg_args'] += other_stream_mapping
        data['ffmpeg_args'] += last_stream_mapping

        # Do not remux the file. Keep the file out in the same container
        split_file_in = os.path.splitext(data.get('file_in'))
        split_file_out = os.path.splitext(data.get('file_out'))
        data['file_out'] = "{}{}".format(split_file_out[0], split_file_in[1])

        data['ffmpeg_args'] += ['-y', data.get('file_out')]

    return data
