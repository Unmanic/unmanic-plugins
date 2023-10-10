#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
    unmanic-plugins.plugin.py

    Written by:               lbenedetto <larsbenedetto@gmail.com>
    Date:                     10 Oct 2023, (23:09 PM)

    Copyright:
        Copyright (C) 2023 Lars Benedetto

        This program is free software: you can redistribute it and/or modify it under the terms of the GNU General
        Public License as published by the Free Software Foundation, version 3.

        This program is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the
        implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License
        for more details.

        You should have received a copy of the GNU General Public License along with this program.
        If not, see <https://www.gnu.org/licenses/>.

"""
import json
import os
from enum import Enum

import humanfriendly
import subprocess
import logging
from unmanic.libs.unplugins.settings import PluginSettings

# Configure plugin logger
logger = logging.getLogger("Unmanic.Plugin.ignore_under_size")


class Settings(PluginSettings):
    settings = {
        "minimum_file_size": '0GB/h',
    }
    form_settings = {
        "minimum_file_size": {
            "label": "Minimum file size (assuming 1080p)",
        }
    }


class TimeUnit(Enum):
    HOUR = ["h", "hour", "Hour"]
    MINUTE = ["m", "minute", "Minute"]
    SECOND = ["s", "second", "Second"]


def select_time_unit(time_unit: str) -> TimeUnit:
    """Match the given string to a TimeUnit"""
    for unit in TimeUnit:
        if time_unit in unit.value:
            return unit
    raise AssertionError(f"Unknown unit {time_unit}")


def get_size_per_second_threshold(threshold_string: str) -> float:
    """Get the threshold in bytes/second"""
    threshold = threshold_string.split("/")
    size: float = float(humanfriendly.parse_size(threshold[0]))
    time_unit: TimeUnit = select_time_unit(threshold[1])

    logger.debug("Requested bytes/%s is %s", time_unit, size)

    # Normalize to seconds
    if time_unit == TimeUnit.HOUR:
        return size / 3600
    if time_unit == TimeUnit.MINUTE:
        return size / 60

    return size


class VideoData:
    def __init__(self, data: str):
        self.width = None
        self.height = None
        self.duration = None
        for stream_data in json.loads(data)["streams"]:
            if "width" in stream_data:
                self.width = stream_data["width"]
            if "height" in stream_data:
                self.height = stream_data["height"]
            if "duration" in stream_data:
                self.duration = float(stream_data["duration"])

        if not self.width:
            raise AssertionError("Unable to determine video width")
        if not self.height:
            raise AssertionError("Unable to determine video height")
        if not self.duration:
            raise AssertionError("Unable to determine video duration")


def get_video_data(path: str) -> VideoData:
    """Get the duration of the video in seconds"""
    data = subprocess.check_output(
        args=[
            "ffprobe",
            "-v", "error",
            "-show_entries", "stream=duration,width,height",
            "-print_format", "json",
            path
        ],
        text=True).strip()

    video_data = VideoData(data)
    logger.debug("Video has resolution of %sx%s and a duration of %s seconds",
                 video_data.width, video_data.height, video_data.duration)
    return video_data


def normalize_by_resolution(threshold: float, video_data: VideoData) -> float:
    """Scale the threshold based on the actual resolution, assuming 1080p as a baseline"""
    default_resolution = 1920 * 1080
    actual_resolution = video_data.width * video_data.height

    ratio = actual_resolution/default_resolution
    logger.debug("Scaling threshold by ratio %s to compensate for resolution difference", ratio)
    new_threshold = threshold * ratio
    logger.debug("Requested (resolution normalized) bytes/second is %s",new_threshold)
    return new_threshold


def get_time_normalized_file_size(path: str, video_data: VideoData) -> float:
    """Return the file size in bytes/second"""
    file_size = int(os.stat(os.path.join(path)).st_size)
    file_size_per_second = file_size / video_data.duration
    logger.debug("Video has a size/second of %s", file_size_per_second)
    return file_size_per_second


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
    # Configure settings object (maintain compatibility with v1 plugins)
    if data.get('library_id'):
        settings = Settings(library_id=data.get('library_id'))
    else:
        settings = Settings()

    threshold_string = settings.get_setting("minimum_file_size")

    minimum_file_size_per_second = get_size_per_second_threshold(threshold_string)
    logger.debug("Requested (time normalized) bytes/second is %s",
                 minimum_file_size_per_second)

    if minimum_file_size_per_second == 0:
        return data

    file_path = data.get('path')
    video_data = get_video_data(file_path)
    actual_file_size_per_second = get_time_normalized_file_size(file_path, video_data)
    minimum_file_size_per_second = normalize_by_resolution(minimum_file_size_per_second, video_data)

    if actual_file_size_per_second < minimum_file_size_per_second:
        # Ignore this file
        data['add_file_to_pending_tasks'] = False
        data['issues'].append({
            'id':      'Ignore video files by size on disk',
            'message': f"File '{file_path}' should be ignored because it is under the configured "
                       f"minimum size/hour '{threshold_string}'.",
        })

    return data
