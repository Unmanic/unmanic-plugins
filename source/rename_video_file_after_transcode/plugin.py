#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
    plugins.__init__.py

    Written by:               Josh.5 <jsunnex@gmail.com>, senorsmartypants@gmail.com
    Date:                     20 Sep 2021, (10:45 PM)

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
import os
import re
import logging

from unmanic.libs.unplugins.settings import PluginSettings

from rename_video_file_after_transcode.lib.ffmpeg import Probe

# Configure plugin logger
logger = logging.getLogger("Unmanic.Plugin.rename_video_file_after_transcode")


class Settings(PluginSettings):
    settings = {}

    def __init__(self, *args, **kwargs):
        super(Settings, self).__init__(*args, **kwargs)


STANDARD_RESOLUTIONS = [
    ("4320p", 7680 * 4320),
    ("2160p", 3840 * 2160),
    ("1440p", 2560 * 1440),
    ("1080p", 1920 * 1080),
    ("720p", 1280 * 720),
    ("576p", 720 * 576),
    ("480p", 640 * 480),
]

# Known codec names and their preferred display tokens
CODEC_ALIASES = {
    "hevc": "h265",
    "h265": "h265",
    "hvc1": "h265",
    "hev1": "h265",
    "avc": "h264",
    "h264": "h264",
    "avc1": "h264",
    "xvid": "xvid",
    "vp9": "vp9",
    "vp09": "vp9",
    "vp8": "vp8",
    "av1": "av1",
    "mpeg2video": "mpeg2",
    "mpeg2": "mpeg2",
    "mpeg4": "mpeg4",
    "vc1": "vc1",
}

# Patterns to find tokens in filenames. All are case-insensitive and keep non-alphanumeric separators intact.
CODEC_TOKEN_PATTERN = re.compile(
    r"(?i)(?<![A-Za-z0-9])(x265|h265|h\.265|hevc|x264|h264|h\.264|avc|av1|vp9|vp09|vp8|mpeg2|mpeg-2|mpeg4|mpeg-4|mpeg2video|vc1|xvid)(?![A-Za-z0-9])"
)
RESOLUTION_TOKEN_PATTERN = re.compile(
    r"(?i)(?<![A-Za-z0-9])(4320p|2160p|1440p|1080p|720p|576p|480p|4k|uhd|ultra[- ]?hd|fhd|hd|sd)(?![A-Za-z0-9])"
)
BIT_DEPTH_TOKEN_PATTERN = re.compile(r"(?i)(?<![A-Za-z0-9])(\d{1,2})\s*-?\s*bit(?![A-Za-z0-9])")
RANGE_TOKEN_PATTERN = re.compile(r"(?i)(?<![A-Za-z0-9])(HDR|SDR)(?![A-Za-z0-9])")


def _safe_int(value):
    try:
        return int(value)
    except Exception:
        return None


def _get_resolution_bucket(width, height):
    """
    Bucket non-standard resolutions to the closest well-known format using pixel area.
    """
    if not width or not height:
        return None
    area = width * height

    closest = None
    smallest_delta = None
    for label, reference_area in STANDARD_RESOLUTIONS:
        delta = abs(reference_area - area)
        if smallest_delta is None or delta < smallest_delta:
            smallest_delta = delta
            closest = label
    return closest


def _detect_bit_depth(stream):
    bit_depth = _safe_int(stream.get("bits_per_raw_sample"))
    if bit_depth:
        return bit_depth

    pix_fmt = stream.get("pix_fmt") or ""
    match = re.search(r"p(10|12|14|16)", pix_fmt)
    if match:
        return _safe_int(match.group(1))

    if pix_fmt:
        return 8
    return None


def _codec_label(stream):
    codec_name = (stream.get("codec_name") or "").lower()
    if not codec_name:
        return None
    return CODEC_ALIASES.get(codec_name, codec_name)


def _replace_with_token(pattern, new_token, name):
    """
    Replace all occurrences of pattern in name with new_token.
    Returns the updated name and a bool indicating if a change was made.
    """
    if not new_token:
        return name, False
    updated, count = pattern.subn(new_token, name)
    return updated, bool(count)


def _rename_file(file_path, probe):
    """
    Compute and apply a new filename reflecting the probed codec/resolution/bit-depth/range.
    Returns the updated path if renamed, otherwise None.
    """
    stream = probe.get_first_video_stream()
    if not stream:
        logger.warning("No video stream found in '%s'; skipping rename.", file_path)
        return None

    width = _safe_int(stream.get("width"))
    height = _safe_int(stream.get("height"))
    target_resolution = _get_resolution_bucket(width, height)

    target_codec = _codec_label(stream)
    target_bit_depth = _detect_bit_depth(stream)
    hdr_source = probe.is_hdr_source()

    dirpath, filename = os.path.split(file_path)
    name, ext = os.path.splitext(filename)

    updated_name = name
    changes = []

    if target_resolution:
        updated_name, changed = _replace_with_token(RESOLUTION_TOKEN_PATTERN, target_resolution, updated_name)
        if changed:
            changes.append(f"resolution -> {target_resolution}")

    if target_codec:
        updated_name, changed = _replace_with_token(CODEC_TOKEN_PATTERN, target_codec, updated_name)
        if changed:
            changes.append(f"codec -> {target_codec}")

    if target_bit_depth:
        bit_depth_label = f"{target_bit_depth}bit"
        updated_name, changed = _replace_with_token(BIT_DEPTH_TOKEN_PATTERN, bit_depth_label, updated_name)
        if changed:
            changes.append(f"bit depth -> {bit_depth_label}")

    if hdr_source is not None:
        range_label = "HDR" if hdr_source else "SDR"
        updated_name, changed = _replace_with_token(RANGE_TOKEN_PATTERN, range_label, updated_name)
        if changed:
            changes.append(f"range -> {range_label}")

    if updated_name == name:
        logger.debug("No filename tokens to update for '%s'.", filename)
        return None

    new_filename = "{}{}".format(updated_name, ext)
    new_path = os.path.join(dirpath, new_filename)
    if new_path == file_path:
        return None

    if os.path.exists(new_path):
        logger.warning("Target filename already exists. Skipping rename '%s' -> '%s'.", file_path, new_path)
        return None

    try:
        os.rename(file_path, new_path)
        logger.info("Renamed file to reflect media properties (%s): '%s' -> '%s'.",
                    ", ".join(changes), file_path, new_path)
        return new_path
    except Exception as error:
        logger.error("Failed to rename '%s' -> '%s': %s", file_path, new_path, error)
        return None


def on_postprocessor_task_results(data):
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
    # Skip if the task did not complete cleanly
    if not data.get("task_processing_success") or not data.get("file_move_processes_success"):
        logger.debug("Skipping rename - task processing or file move did not complete successfully.")
        return

    destination_files = data.get("destination_files") or []
    if not destination_files:
        logger.error("No destination files found for rename processing.")
        return

    updated_destinations = []
    for file_path in destination_files:
        if not os.path.isfile(file_path):
            logger.warning("Destination file does not exist; skipping rename. (%s)", file_path)
            updated_destinations.append(file_path)
            continue

        try:
            probe = Probe(logger, allowed_mimetypes=["video"])
        except Exception as error:
            logger.error("Unable to initialise ffprobe for '%s': %s", file_path, error)
            updated_destinations.append(file_path)
            continue

        if not probe.file(file_path):
            logger.warning("Unable to probe destination file; skipping rename. (%s)", file_path)
            updated_destinations.append(file_path)
            continue

        new_path = _rename_file(file_path, probe)
        updated_destinations.append(new_path or file_path)

    data["destination_files"] = updated_destinations
