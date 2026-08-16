#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Copyright (C) Josh Sunnex

SPDX-License-Identifier: GPL-3.0-only
"""

import datetime
import json
import logging
import os
from configparser import NoOptionError, NoSectionError

from normalise_aac.lib.ffmpeg import Parser, Probe, StreamMapper
from unmanic.libs.directoryinfo import UnmanicDirectoryInfo
from unmanic.libs.unplugins.settings import PluginSettings

# Configure plugin logger
logger = logging.getLogger("Unmanic.Plugin.normalise_aac")


class Settings(PluginSettings):
    settings = {
        "I": "-24.0",
        "LRA": "7.0",
        "TP": "-2.0",
        "ignore_previously_processed": True,
    }
    form_settings = {
        "I": {
            "label": "Integrated loudness target",
            "input_type": "slider",
            "slider_options": {
                "min": -70.0,
                "max": -5.0,
                "step": 0.1,
            },
        },
        "LRA": {
            "label": "Loudness range",
            "input_type": "slider",
            "slider_options": {
                "min": 1.0,
                "max": 20.0,
                "step": 0.1,
            },
        },
        "TP": {
            "label": "The maximum true peak",
            "input_type": "slider",
            "slider_options": {
                "min": -9.0,
                "max": 0,
                "step": 0.1,
            },
        },
        "ignore_previously_processed": {
            "label": "Ignore all files previously normalised with this plugin regardless of the settings above.",
        },
    }


class PluginStreamMapper(StreamMapper):
    def __init__(self):
        super(PluginStreamMapper, self).__init__(logger, ["audio"])
        self.settings = None

    def set_settings(self, settings):
        self.settings = settings

    def test_stream_needs_processing(self, stream_info: dict):
        # Only process AAC audio streams
        if stream_info.get("codec_name", "").lower() in ["aac"]:
            return True
        return False

    def custom_stream_mapping(self, stream_info: dict, stream_id: int):
        channels = int(stream_info.get("channels", 2))
        original_sample_rate = stream_info.get("sample_rate", "48000")  # Default to 48kHz if not found
        return {
            "stream_mapping": ["-map", "0:a:{}".format(stream_id)],
            "stream_encoding": [
                "-c:a:{}".format(stream_id),
                "aac",
                "-ac:a:{}".format(stream_id),
                "{}".format(channels),
                "-ar:a:{}".format(stream_id),
                original_sample_rate,  # Use the original sample rate
                "-filter:a:{}".format(stream_id),
                audio_filtergraph(self.settings),
            ],
        }


def audio_filtergraph(settings):
    i = settings.get_setting("I")
    if not i:
        i = settings.settings.get("I")

    lra = settings.get_setting("LRA")
    if not lra:
        lra = settings.settings.get("LRA")

    tp = settings.get_setting("TP")
    if not tp:
        tp = settings.settings.get("TP")

    return "loudnorm=I={}:LRA={}:TP={}".format(i, lra, tp)


def migrate_legacy_marker_to_file_metadata(path, raw_marker):
    """
    Migrate legacy UnmanicDirectoryInfo marker into database-backed FileMetadata.
    """
    try:
        from unmanic.libs import common
        from unmanic.libs.metadata import UnmanicFileMetadata
        from unmanic.libs.unmodels.filemetadata import FileMetadata
        from unmanic.libs.unmodels.filemetadatapaths import FileMetadataPaths

        marker_filtergraph = ""
        if isinstance(raw_marker, str) and raw_marker.startswith("{"):
            try:
                marker_json = json.loads(raw_marker)
                if isinstance(marker_json, dict):
                    marker_filtergraph = marker_json.get("filtergraph", "")
            except Exception:
                pass
        if not marker_filtergraph:
            marker_filtergraph = raw_marker

        fingerprint, algo = common.get_file_fingerprint(path)
        payload = {
            "normalise_aac": {
                "normalised": True,
                "status": "normalised",
                "filtergraph": marker_filtergraph,
            }
        }

        row, created = FileMetadata.get_or_create(
            fingerprint=fingerprint,
            defaults={
                "fingerprint_algo": algo,
                "metadata_json": json.dumps(payload),
                "created_at": datetime.datetime.now(),
                "updated_at": datetime.datetime.now(),
            },
        )
        if not created:
            existing = UnmanicFileMetadata._load_json_dict(row.metadata_json)
            existing.update(payload)
            row.metadata_json = json.dumps(existing)
            row.fingerprint_algo = algo
            row.updated_at = datetime.datetime.now()
            row.save()

        # Record path in FileMetadataPaths
        FileMetadataPaths.get_or_create(
            file_metadata_id=row.id,
            path=path,
            defaults={
                "path_type": "source",
                "created_at": datetime.datetime.now(),
                "updated_at": datetime.datetime.now(),
            },
        )
        # Invalidate path cache in UnmanicFileMetadata so immediate get() calls pick it up
        UnmanicFileMetadata._invalidate_cached_fingerprint(fingerprint, paths=[path])
        logger.info("Migrated legacy DirectoryInfo marker to UnmanicFileMetadata for '%s'.", path)
    except Exception as e:
        logger.debug("Failed to migrate legacy DirectoryInfo marker to FileMetadata for '%s': %s", path, e)


def file_already_normalised(settings, path, file_metadata=None):
    # Check database-backed UnmanicFileMetadata first
    if file_metadata:
        try:
            metadata = file_metadata.get()
            if metadata.get("normalised") is True or metadata.get("status") == "normalised":
                if settings.get_setting("ignore_previously_processed"):
                    logger.debug("Plugin configured to ignore previously normalised streams.")
                    return True
                stored_filtergraph = metadata.get("filtergraph", "")
                if stored_filtergraph and audio_filtergraph(settings) in stored_filtergraph:
                    logger.debug("Stream was previously normalised with the same settings as currently configured.")
                    return True
                return False
        except Exception as e:
            logger.debug("Unable to read UnmanicFileMetadata for '%s': %s", path, e)

    # Fallback check for legacy UnmanicDirectoryInfo markers
    directory_info = UnmanicDirectoryInfo(os.path.dirname(path))
    try:
        raw_marker = directory_info.get("normalise_aac", os.path.basename(path))
    except (NoSectionError, NoOptionError):
        raw_marker = ""
    except Exception as e:
        logger.debug("Unknown exception checking directory info: %s", e)
        raw_marker = ""

    if raw_marker:
        # Migrate legacy marker to database-backed UnmanicFileMetadata
        migrate_legacy_marker_to_file_metadata(path, raw_marker)

        marker_filtergraph = ""
        if isinstance(raw_marker, str) and raw_marker.startswith("{"):
            try:
                marker_json = json.loads(raw_marker)
                if isinstance(marker_json, dict):
                    marker_filtergraph = marker_json.get("filtergraph", "")
            except Exception:
                pass
        if not marker_filtergraph:
            marker_filtergraph = raw_marker

        if settings.get_setting("ignore_previously_processed"):
            logger.debug("Plugin configured to ignore previously normalised streams (legacy marker).")
            return True
        elif marker_filtergraph and audio_filtergraph(settings) in marker_filtergraph:
            logger.debug("Stream was previously normalised with the same settings (legacy marker).")
            return True

    return False


def on_library_management_file_test(data, task_data_store=None, file_metadata=None):
    """
    Runner function - enables additional actions during the library management file tests.

    The 'data' object argument includes:
        path                            - String containing the full path to the file being tested.
        issues                          - List of currently found issues for not processing the file.
        add_file_to_pending_tasks       - Boolean, is the file currently marked to be added to the queue for processing.

    :param data:
    :param task_data_store:
    :param file_metadata:
    :return:
    """
    # Get the path to the file
    abspath = data.get("path")

    # Get file probe
    probe = Probe(logger, allowed_mimetypes=["video", "audio"])
    if not probe.file(abspath):
        # File probe failed, skip the rest of this test
        return data

    # Configure settings object (maintain compatibility with v1 plugins)
    if data.get("library_id"):
        settings = Settings(library_id=data.get("library_id"))
    else:
        settings = Settings()

    # Get stream mapper
    mapper = PluginStreamMapper()
    mapper.set_settings(settings)
    mapper.set_probe(probe)

    if not file_already_normalised(settings, abspath, file_metadata=file_metadata):
        # Mark this file to be added to the pending tasks
        data["add_file_to_pending_tasks"] = True
        logger.debug("File '%s' should be added to task list. File has not been previously normalised.", abspath)
    else:
        logger.debug("File '%s' has been previously normalised.", abspath)

    return data


def on_worker_process(data, task_data_store=None, file_metadata=None):
    """
    Runner function - enables additional configured processing jobs during the worker stages of a task.

    The 'data' object argument includes:
        exec_command            - A command that Unmanic should execute. Can be empty.
        command_progress_parser - A function that Unmanic can use to parse STDOUT to collect progress stats.
        file_in                 - The source file to be processed by the command.
        file_out                - The destination that the command should output (may be the same as file_in).
        original_file_path      - The absolute path to the original file.
        repeat                  - Boolean, should this runner be executed again once completed.

    :param data:
    :param task_data_store:
    :param file_metadata:
    :return:
    """
    # Default to no FFMPEG command required. This prevents the FFMPEG command from running if it is not required
    data["exec_command"] = []
    data["repeat"] = False

    # Get the path to the file
    abspath = data.get("file_in")

    # Get file probe
    probe = Probe(logger, allowed_mimetypes=["video", "audio"])
    if not probe.file(abspath):
        # File probe failed, skip the rest of this test
        return data

    # Configure settings object (maintain compatibility with v1 plugins)
    if data.get("library_id"):
        settings = Settings(library_id=data.get("library_id"))
    else:
        settings = Settings()

    if not file_already_normalised(settings, data.get("file_in"), file_metadata=file_metadata):
        # Get stream mapper
        mapper = PluginStreamMapper()
        mapper.set_settings(settings)
        mapper.set_probe(probe)

        if mapper.streams_need_processing():
            # Set the input file
            mapper.set_input_file(abspath)

            # Do not remux the file. Keep the file out in the same container
            mapper.set_output_file(data.get("file_out"))

            # Get generated ffmpeg args
            ffmpeg_args = mapper.get_ffmpeg_args()

            # Apply ffmpeg args to command
            data["exec_command"] = ["ffmpeg"]
            data["exec_command"] += ffmpeg_args

            # Set the parser
            parser = Parser(logger)
            parser.set_probe(probe)
            data["command_progress_parser"] = parser.parse_progress

    return data


def on_postprocessor_task_results(data, task_data_store=None, file_metadata=None):
    """
    Runner function - provides a means for additional postprocessor functions based on the task success.

    The 'data' object argument includes:
        task_processing_success         - Boolean, did all task processes complete successfully.
        file_move_processes_success     - Boolean, did all postprocessor file movements complete successfully.
        destination_files               - List containing all file paths created by file movements.
        source_data                     - Dictionary containing data pertaining to the original source file.

    :param data:
    :param task_data_store:
    :param file_metadata:
    :return:
    """
    # We only care that the task completed successfully.
    # If a worker processing task was unsuccessful, do not mark the file as normalised
    if not data.get("task_processing_success"):
        return data

    # Configure settings object (maintain compatibility with v1 plugins)
    if data.get("library_id"):
        settings = Settings(library_id=data.get("library_id"))
    else:
        settings = Settings()

    # Record normalisation metadata in Unmanic's central file metadata system
    if file_metadata:
        file_metadata.set(
            {
                "normalised": True,
                "status": "normalised",
                "filtergraph": audio_filtergraph(settings),
            }
        )
        logger.debug("Normalise AAC file metadata recorded.")
    else:
        # Fallback to legacy DirectoryInfo if file_metadata helper is unavailable
        for destination_file in data.get("destination_files", []):
            directory_info = UnmanicDirectoryInfo(os.path.dirname(destination_file))
            directory_info.set("normalise_aac", os.path.basename(destination_file), audio_filtergraph(settings))
            directory_info.save()
            logger.debug("Normalise AAC info written for '%s'.", destination_file)

    return data
