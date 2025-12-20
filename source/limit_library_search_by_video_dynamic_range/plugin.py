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
import logging
import re

from unmanic.libs.unplugins.settings import PluginSettings

from limit_library_search_by_video_dynamic_range.lib.ffmpeg import Probe

# Configure plugin logger
logger = logging.getLogger("Unmanic.Plugin.limit_library_search_by_video_dynamic_range")


class Settings(PluginSettings):
    settings = {
        "allowed_dynamic_range": "HDR",
        "limit_hdr_format":      False,
        "allowed_hdr_format":    "HDR10",
    }
    form_settings = {}

    def __init__(self, *args, **kwargs):
        super(Settings, self).__init__(*args, **kwargs)
        self.form_settings = self.__build_form_settings_object()

    def __build_form_settings_object(self):
        allowed_range = (self.get_setting("allowed_dynamic_range") or "HDR").upper()
        limit_hdr = bool(self.get_setting("limit_hdr_format"))

        return {
            "allowed_dynamic_range": {
                "label":          "Allow only HDR or SDR files",
                "input_type":     "select",
                "select_options": [
                    {
                        "value": "HDR",
                        "label": "HDR",
                    },
                    {
                        "value": "SDR",
                        "label": "SDR",
                    },
                ],
                "description":    "Choose which dynamic range to allow through library scanning. "
                                  "Files that do not match are ignored by this plugin.",
            },
            "limit_hdr_format":      {
                "label":       "Limit to a specific HDR format (only applies when HDR is allowed)",
                "description": "Enable this to restrict HDR to one or more specific formats (eg. HDR10, HDR10+, Dolby Vision, HLG).",
                "input_type":  "checkbox",
                "display":     "visible" if allowed_range == "HDR" else "hidden",
                "sub_setting": True,
            },
            "allowed_hdr_format":    {
                "label":          "Allowed HDR formats",
                "input_type":     "text",
                "placeholder":    "HDR10, HDR10+, Dolby Vision, HLG, HDR",
                "description":    "Comma-separated list. Supported values: HDR, HDR10, HDR10+, Dolby Vision, HLG.",
                "display":        "visible" if allowed_range == "HDR" and limit_hdr else "hidden",
                "sub_setting":    True,
            },
        }


def __get_probe(data):
    """
    Fetch or create a Probe instance for the current file.
    Prefer an existing ffprobe entry in shared_info to avoid repeated probes.
    """
    abspath = data.get("path")
    shared_info = data.get("shared_info") or {}
    try:
        probe = Probe(logger, allowed_mimetypes=["video"])
    except Exception as exc:
        logger.error("Unable to initialise ffprobe for '%s': %s", abspath, exc)
        return

    ffprobe_data = shared_info.get("ffprobe")
    if ffprobe_data:
        if probe.set_probe(ffprobe_data):
            logger.debug("Using cached ffprobe data from shared_info for '%s'.", abspath)
            return probe
        logger.debug("Existing ffprobe data in shared_info is not usable for '%s'. Re-running ffprobe.", abspath)

    if not probe.file(abspath):
        return

    # Persist ffprobe data for subsequent plugins
    if "shared_info" not in data or not isinstance(data.get("shared_info"), dict):
        data["shared_info"] = {}
    data["shared_info"]["ffprobe"] = probe.get_probe()
    return probe


def __get_bit_depth(pix_fmt):
    """
    Best-effort parse of pixel format bit depth. Defaults to 8-bit if unknown.
    """
    match = re.search(r"p(\d+)", pix_fmt or "")
    if match:
        try:
            return int(match.group(1))
        except (TypeError, ValueError):
            return 8
    return 8


def __parse_allowed_hdr_formats(settings):
    """
    Parse the user-supplied comma-separated list of HDR formats.
    Normalises common variants (eg. HDR10+ -> HDR10_PLUS).
    """
    raw = settings.get_setting("allowed_hdr_format") or ""
    allowed = set()
    valid_values = {"HDR", "HDR10", "HDR10_PLUS", "DOLBY_VISION", "HLG"}
    for val in raw.split(","):
        token = val.strip().upper()
        if not token:
            continue
        token = token.replace(" ", "_")
        if token == "HDR10+":
            token = "HDR10_PLUS"
        if token == "DOLBYVISION":
            token = "DOLBY_VISION"
        if token == "DOLBY_VISION":
            token = "DOLBY_VISION"
        if token not in valid_values:
            logger.warning("Configured HDR format '%s' is not supported; supported values: %s",
                           token, ", ".join(sorted(valid_values)))
            continue
        allowed.add(token)
    if not allowed:
        allowed.add("HDR10")
    return allowed


def __detect_dynamic_range_and_format(probe):
    """
    Determine whether the first video stream is HDR or SDR and return detected HDR format.
    Returns (dynamic_range, hdr_format) where hdr_format is only set for HDR.
    dynamic_range may be 'HDR', 'SDR', or 'UNKNOWN'.
    """
    vs = probe.get_first_video_stream()
    if not vs:
        return "UNKNOWN", None

    color_transfer = (vs.get("color_transfer") or vs.get("color_trc") or "").lower()
    color_space = (vs.get("color_space") or vs.get("colorspace") or "").lower()
    color_primaries = (vs.get("color_primaries") or "").lower()
    pix_fmt = (vs.get("pix_fmt") or "").lower()
    bit_depth = __get_bit_depth(pix_fmt)
    side_data = vs.get("side_data_list") or []

    hdr_format = None

    # Dolby Vision detection (stream DV fields or side data)
    if any(key in vs for key in ("dv_profile", "dv_level", "dv_version_major", "dv_version_minor")):
        return "HDR", "DOLBY_VISION"
    for sd in side_data:
        side_type = (sd.get("side_data_type") or "").lower()
        if "dovi" in side_type or "dolby" in side_type:
            return "HDR", "DOLBY_VISION"

    def _has_hdr_metadata():
        for sd in side_data:
            side_type = (sd.get("side_data_type") or "").lower()
            if "dovi" in side_type or "dolby" in side_type:
                return "DOLBY_VISION"
            if "hdr10+" in side_type:
                return "HDR10_PLUS"
            if "hdr" in side_type or "light level" in side_type or "mastering display" in side_type:
                return "HDR"
        return None

    metadata_hint = _has_hdr_metadata()
    if metadata_hint == "DOLBY_VISION":
        return "HDR", "DOLBY_VISION"
    if metadata_hint == "HDR10_PLUS":
        return "HDR", "HDR10_PLUS"

    # HDR10 style (PQ + BT.2020 + 10-bit) first
    if probe.is_hdr_source():
        hdr_format = "HDR10"
        dynamic_range = "HDR"
    elif color_transfer == "arib-std-b67":
        dynamic_range = "HDR"
        hdr_format = "HLG"
    else:
        hdr_transfer_values = {"smpte2084", "arib-std-b67"}
        hdr_spaces = {"bt2020nc", "bt2020ncl", "bt2020c", "bt2020"}
        has_hdr_transfer = color_transfer in hdr_transfer_values
        has_hdr_space = color_space in hdr_spaces or color_primaries in hdr_spaces
        is_high_bit_depth = bit_depth >= 10

        if has_hdr_transfer and (has_hdr_space or is_high_bit_depth or metadata_hint == "HDR"):
            dynamic_range = "HDR"
            hdr_format = "HDR"
        elif metadata_hint == "HDR":
            dynamic_range = "HDR"
            hdr_format = "HDR"
        else:
            return "SDR", None

    if dynamic_range == "HDR" and hdr_format:
        return "HDR", hdr_format

    return "UNKNOWN", None


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
    settings = Settings(library_id=data.get("library_id"))
    abspath = data.get("path")

    probe = __get_probe(data)
    if not probe:
        logger.info("Ignoring '%s' - unable to obtain ffprobe data for this file.", abspath)
        data["add_file_to_pending_tasks"] = False
        return

    dynamic_range, hdr_format = __detect_dynamic_range_and_format(probe)
    if not dynamic_range or dynamic_range == "UNKNOWN":
        logger.warning("Ignoring '%s' - unable to determine SDR/HDR format from ffprobe data.", abspath)
        data["add_file_to_pending_tasks"] = False
        return

    allowed_range = (settings.get_setting("allowed_dynamic_range") or "HDR").upper()

    if dynamic_range != allowed_range:
        logger.info(
            "Ignoring '%s' - detected dynamic range '%s' does not match configured '%s'.",
            abspath,
            dynamic_range,
            allowed_range,
        )
        data["add_file_to_pending_tasks"] = False
        return

    if allowed_range == "HDR" and settings.get_setting("limit_hdr_format"):
        allowed_hdr_formats = __parse_allowed_hdr_formats(settings)
        if not hdr_format:
            logger.info(
                "Ignoring '%s' - HDR format could not be determined but a specific HDR format ('%s') is required.",
                abspath,
                ", ".join(sorted(allowed_hdr_formats)),
            )
            data["add_file_to_pending_tasks"] = False
            return
        if hdr_format not in allowed_hdr_formats:
            logger.info(
                "Ignoring '%s' - detected HDR format '%s' is not in configured list [%s].",
                abspath,
                hdr_format,
                ", ".join(sorted(allowed_hdr_formats)),
            )
            data["add_file_to_pending_tasks"] = False
            return

    if hdr_format:
        logger.debug(
            "Allowing '%s' - matches configured dynamic range '%s' and HDR format '%s'.",
            abspath,
            allowed_range,
            hdr_format,
        )
    else:
        logger.debug("Allowing '%s' - matches configured dynamic range '%s'.", abspath, allowed_range)
