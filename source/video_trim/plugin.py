#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from unmanic.libs.unplugins.settings import PluginSettings


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


def on_worker_process(data):
    """
    Runner function - enables additional configured processing jobs during the worker stages of a task.

    The 'data' object argument includes:
        exec_ffmpeg             - Boolean, should Unmanic run FFMPEG with the data returned from this plugin.
        file_probe              - A dictionary object containing the current file probe state.
        ffmpeg_args             - A list of Unmanic's default FFMPEG args.
        file_in                 - The source file to be processed by the FFMPEG command.
        file_out                - The destination that the FFMPEG command will output.
        original_file_path      - The absolute path to the original library file.

    :param data:
    :return:
    
    """
    settings = Settings()

    # Fetch duration from file probe...
    file_probe = data.get('file_probe', {})
    file_probe_format = file_probe.get('format', {})
    duration = file_probe_format.get('duration')
    if not duration:
        data['exec_ffmpeg'] = False
        return data

    start_point = []
    start_seconds = settings.get_setting('start_seconds')
    if start_seconds and float(start_seconds) > 0:
        # Ensure the start trim is less than the duration of the file
        if float(start_seconds) > float(duration):
            # The configured value is larger than the duration of the file.
            # Skip this file for now...
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
            data['exec_ffmpeg'] = False
            return data
        # Build the end trim args
        duration = str(float(duration) - float(end_seconds))
        end_point = [
            '-to', str(duration),
        ]

    # Build ffmpeg args and add them to the return data
    data['ffmpeg_args'] = [
        '-i',
        data.get('file_in'),
        '-hide_banner',
        '-loglevel', 'info',
        '-strict', '-2',
        '-max_muxing_queue_size', '4096',
    ]
    data['ffmpeg_args'] += start_point
    data['ffmpeg_args'] += end_point
    data['ffmpeg_args'] += [
        '-c', 'copy',
        '-map', '0',
        '-y',
        data.get('file_out'),
    ]

    return data
