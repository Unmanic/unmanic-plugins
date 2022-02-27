#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
    unmanic-plugins.plugin.py

    Written by:               Josh.5 <jsunnex@gmail.com>
    Date:                     27 Feb 2022, (12:22 PM)

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

from pyarr import SonarrAPI
from unmanic.libs.unplugins.settings import PluginSettings

# Configure plugin logger
logger = logging.getLogger("Unmanic.Plugin.notify_sonarr")


class Settings(PluginSettings):
    settings = {
        'host_url': 'http://localhost:8989',
        'api_key':  '',
    }
    form_settings = {
        "host_url": {
            "label": "Sonarr LAN IP Address",
        },
        "api_key":  {
            "label": "Sonarr API Key",
        },
    }

    def __init__(self, *args, **kwargs):
        super(Settings, self).__init__(*args, **kwargs)


def process_files(destination_files, host_url, api_key):
    sonarr_api = SonarrAPI(host_url, api_key)

    # Get the basename of the file
    for dest_file in destination_files:
        basename = os.path.basename(dest_file)

        episode_data = sonarr_api.get_parsed_title(basename)

        # Fetch a series ID from Sonarr
        series_title = episode_data.get('series', {}).get('title')
        series_id = episode_data.get('series', {}).get('id')
        if not series_id:
            logger.error("Missing series ID. Failed to queued refresh of series for file: '{}'".format(dest_file))
            continue

        # Run API command for RescanSeries
        #   - RescanSeries with a series ID
        result = sonarr_api.post_command('RescanSeries', seriesId=series_id)
        if result.get('message'):
            logger.error("Failed to queued refresh of series ID '{}' for file: '{}'".format(series_id, dest_file))
            continue
        logger.info("Successfully queued refreshed the Series '{}' for file: '{}'".format(series_title, dest_file))


def on_postprocessor_task_results(data):
    """
    Runner function - provides a means for additional postprocessor functions based on the task success.

    The 'data' object argument includes:
        library_id                      - The library that the current task is associated with
        task_processing_success         - Boolean, did all task processes complete successfully.
        file_move_processes_success     - Boolean, did all postprocessor movement tasks complete successfully.
        destination_files               - List containing all file paths created by postprocessor file movements.
        source_data                     - Dictionary containing data pertaining to the original source file.

    :param data:
    :return:
    
    """
    # Configure settings object (maintain compatibility with v1 plugins)
    if data.get('library_id'):
        settings = Settings(library_id=data.get('library_id'))
    else:
        settings = Settings()

    # Fetch destination files
    destination_files = data.get('destination_files', [])

    # Setup API
    host_url = settings.get_setting('host_url')
    api_key = settings.get_setting('api_key')
    process_files(destination_files, host_url, api_key)
