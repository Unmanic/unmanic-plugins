#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
    unmanic-plugins.plugin.py

    Written by:               yajrendrag <yajdude@gmail.com>
    Date:                     16 Feb 2023, (12:02 AM)

    Copyright:
        Copyright (C) 2023 Jay Gardner

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

from unmanic.libs.unplugins.settings import PluginSettings

from ignore_files_based_on_metadata.lib.ffmpeg import Probe

# Configure plugin logger
logger = logging.getLogger("Unmanic.Plugin.ignore_files_based_on_metadata")


class Settings(PluginSettings):
    settings = {
        "disallowed_metadata":          '',
        "metadata_value":               '',
        "process_if_does_not_have_matching_metadata": False,
    }
    form_settings = {
        "disallowed_metadata":          {
            "label":       "metadata field name to search for",
            "description": "Metadata field to test; do not process file if this field contains metadata_value per below."
        },
        "metadata_value":          {
            "label":       "do not process files containing this string",
            "description": "A unique, key phrase in the metadata value that inidicates path should not be processed."
        },
        "process_if_does_not_have_matching_metadata": {
            "label":       "Add any files that do not have matching metadata to pending tasks list",
            "description": "If this option is enabled and the file does not contain matching metadata,\n"
                           "this plugin will add the file to Unmanic's pending task list straight away\n"
                           "without executing any subsequent file test plugins.",
        }
    }


def file_has_disallowed_metadata(path, disallowed_metadata, metadata_value):
    """
    Check if the file contains disallowed search metadata

    :return:
    """

    # initialize Probe
    probe_data=Probe(logger, allowed_mimetypes=['video'])

    # Get stream data from probe
    if probe_data.file(path):
        probe_streams=probe_data.get_probe()["streams"]
        probe_format = probe_data.get_probe()["format"]
    else:
        logger.debug("Probe data failed - Blocking everything.")
        return True

    # If the config is empty (not yet configured) ignore everything
    if not disallowed_metadata:
        logger.debug("Plugin has not yet been configured with disallowed metadata. Blocking everything.")
        return True

    # Check if stream or format components contain disallowed metadata
    streams = [probe_streams[i] for i in range(0, len(probe_streams)) if "codec_type" in probe_streams[i] and probe_streams[i]["codec_type"] == "video"]
    file_has_disallowed_metadata = [streams[i] for i in range(0, len(streams)) if disallowed_metadata in streams[i] and metadata_value in streams[i][disallowed_metadata]]
    probe_format_d = {k:v for  (k, v) in probe_format.items() if type(v) is dict}
    probe_format_kv = {k:v for  (k, v) in probe_format.items() if type(v) is not dict}
    for v in probe_format_d.values():
        probe_format_kv.update(v)
    file_has_disallowed_metadata_fmt = [(k, v) for (k, v) in probe_format_kv.items() if (disallowed_metadata in k.lower() and metadata_value in v)]

    # Check if video, audio, or attachement stream tags contain disallowed metadata
    attachment_streams = [probe_streams[i] for i in range(0, len(probe_streams)) if "codec_type" in probe_streams[i] and probe_streams[i]["codec_type"] == "attachment"]
    try:
        probe_as_tags_kv = {k:v for i in range(0, len(attachment_streams)) for (k, v) in attachment_streams[i]["tags"].items() if type(v) is not dict}
        file_has_disallowed_metadata_ast = [(k, v) for (k, v) in probe_as_tags_kv.items() if (disallowed_metadata in k.lower() and metadata_value in v)]
    except KeyError:
        file_has_disallowed_metadata_ast = ""

    video_streams = [probe_streams[i] for i in range(0, len(probe_streams)) if "codec_type" in probe_streams[i] and probe_streams[i]["codec_type"] == "video"]
    try:
        probe_vs_tags_kv = {k:v for i in range(0, len(video_streams)) for (k, v) in video_streams[i]["tags"].items() if type(v) is not dict}
        file_has_disallowed_metadata_vst = [(k, v) for (k, v) in probe_vs_tags_kv.items() if (disallowed_metadata in k.lower() and metadata_value in v)]
    except KeyError:
        file_has_disallowed_metadata_vst = ""

    audio_streams = [probe_streams[i] for i in range(0, len(probe_streams)) if "codec_type" in probe_streams[i] and probe_streams[i]["codec_type"] == "audio"]
    try:
        probe_aus_tags_kv = {k:v for i in range(0, len(audio_streams)) for (k, v) in audio_streams[i]["tags"].items() if type(v) is not dict}
        file_has_disallowed_metadata_aust = [(k, v) for (k, v) in probe_aus_tags_kv.items() if (disallowed_metadata in k.lower() and metadata_value in v)]
    except KeyError:
        file_has_disallowed_metadata_aust = ""

    if file_has_disallowed_metadata or file_has_disallowed_metadata_fmt or file_has_disallowed_metadata_ast or file_has_disallowed_metadata_vst or file_has_disallowed_metadata_aust:
        logger.debug("File '{}' contains disallowed metadata '{}': '{}'.".format(path, disallowed_metadata, metadata_value))
        return True

    logger.debug("File '{}' does not contain disallowed metadata '{}': '{}'.".format(path, disallowed_metadata, metadata_value))
    return False


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

    # Configure settings object
    settings = Settings(library_id=data.get('library_id'))

    # Get the list of configured metadata to search for
    disallowed_metadata = settings.get_setting('disallowed_metadata')
    metadata_value = settings.get_setting('metadata_value')

    has_disallowed_metadata = file_has_disallowed_metadata(abspath, disallowed_metadata, metadata_value)

    if has_disallowed_metadata:
        # Ignore this file
        data['add_file_to_pending_tasks'] = False
    elif not has_disallowed_metadata and settings.get_setting('process_if_does_not_have_matching_metadata'):
        # Force this file to have a pending task created
        data['add_file_to_pending_tasks'] = True
        logger.debug(
            "File '{}' should be added to task list. " \
            "File does not contain disallowed metadata and plugin is configured to add all non-matching files.".format(abspath))
