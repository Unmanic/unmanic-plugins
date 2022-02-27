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

from pyarr import RadarrAPI
from unmanic.libs.unplugins.settings import PluginSettings

# Configure plugin logger
logger = logging.getLogger("Unmanic.Plugin.notify_radarr")


class Settings(PluginSettings):
    settings = {
        'host_url': 'http://localhost:7878',
        'api_key':  '',
    }
    form_settings = {
        "host_url": {
            "label": "Radarr LAN IP Address",
        },
        "api_key":  {
            "label": "Radarr API Key",
        },
    }

    def __init__(self, *args, **kwargs):
        super(Settings, self).__init__(*args, **kwargs)


def process_files(destination_files, host_url, api_key):
    radarr_api = RadarrAPI(host_url, api_key)

    # Get the basename of the file
    for dest_file in destination_files:
        basename = os.path.basename(dest_file)

        # Run lookup search to fetch movie data and ID for rescan
        lookup_results = radarr_api.lookup_movie(str(basename))

        # Loop over search results and just use the first result (best thing I can think of)
        movie_data = {}
        for result in lookup_results:
            if result.get('id'):
                movie_data = result
                break

        # Parse movie data
        movie_title = movie_data.get('title')
        movie_id = movie_data.get('id')
        if not movie_id:
            logger.error("Missing movie ID. Failed to queued refresh of movie for file: '{}'".format(dest_file))
            continue

        # Run API command for RefreshMovie
        #   - RefreshMovie with a movie ID
        result = radarr_api.post_command('RefreshMovie', movieIds=[movie_id])
        if result.get('message'):
            logger.error("Failed to queued refresh of movie ID '{}' for file: '{}'".format(movie_id, dest_file))
            continue
        logger.info("Successfully queued refreshed the Movie '{}' for file: '{}'".format(movie_title, dest_file))


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
