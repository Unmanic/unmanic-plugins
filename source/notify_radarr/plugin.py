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
import pprint

import humanfriendly
from pyarr import RadarrAPI
from unmanic.libs.unplugins.settings import PluginSettings

# Configure plugin logger
logger = logging.getLogger("Unmanic.Plugin.notify_radarr")


class Settings(PluginSettings):
    settings = {
        'host_url':                  'http://localhost:7878',
        'api_key':                   '',
        'mode':                      'update_mode',
        'limit_import_on_file_size': True,
        'minimum_file_size':         '100MB',
    }

    def __init__(self, *args, **kwargs):
        super(Settings, self).__init__(*args, **kwargs)
        self.form_settings = {
            "host_url":                  {
                "label": "Radarr LAN IP Address",
            },
            "api_key":                   {
                "label": "Radarr API Key",
            },
            "mode":                      {
                "label":          "Mode",
                "input_type":     "select",
                "select_options": [
                    {
                        'value': "update_mode",
                        'label': "Trigger movie refresh on task complete",
                    },
                    {
                        'value': "import_mode",
                        'label': "Import movie on task complete",
                    },
                ],
            },
            "limit_import_on_file_size": self.__set_limit_import_on_file_size(),
            "minimum_file_size":         self.__set_minimum_file_size(),
        }

    def __set_limit_import_on_file_size(self):
        values = {
            "label": "Limit file import size",
        }
        if self.get_setting('mode') != 'import_mode':
            values["display"] = 'hidden'
        return values

    def __set_minimum_file_size(self):
        values = {
            "label": "Minimum file size",
        }
        if self.get_setting('mode') != 'import_mode':
            values["display"] = 'hidden'
        if not self.get_setting('limit_import_on_file_size'):
            values["display"] = 'hidden'
        return values


def check_file_size_under_max_file_size(path, minimum_file_size):
    file_stats = os.stat(os.path.join(path))
    if int(humanfriendly.parse_size(minimum_file_size)) < int(file_stats.st_size):
        return False
    return True


def update_mode(api, abspath):
    basename = os.path.basename(abspath)

    # Run lookup search to fetch movie data and ID for rescan
    lookup_results = api.lookup_movie(str(basename))

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
        logger.error("Missing movie ID. Failed to queued refresh of movie for file: '{}'".format(abspath))
        return

    # Run API command for RefreshMovie
    #   - RefreshMovie with a movie ID
    result = api.post_command('RefreshMovie', movieIds=[movie_id])
    if result.get('message'):
        logger.error("Failed to queued refresh of movie ID '{}' for file: '{}'".format(movie_id, abspath))
        return
    logger.info("Successfully queued refreshed the Movie '{}' for file: '{}'".format(movie_title, abspath))


def import_mode(api, source_path, dest_path):
    source_basename = os.path.basename(source_path)
    abspath_string = dest_path.replace('\\', '')

    download_id = None
    movie_title = None

    queue = api.get_queue()
    message = pprint.pformat(queue, indent=1)
    logger.debug("Current queue \n{}".format(message))
    for item in queue.get('records', []):
        item_output_basename = os.path.basename(item.get('outputPath'))
        if item_output_basename == source_basename:
            download_id = item.get('downloadId')
            movie_title = item.get('title')
            break

    # Run import
    if download_id:
        # Run API command for DownloadedMoviesScan
        #   - DownloadedMoviesScan with a path and downloadClientId
        logger.info("Queued import movie '{}' using downloadClientId: '{}'".format(movie_title, download_id))
        result = api.post_command('DownloadedMoviesScan', path=abspath_string, downloadClientId=download_id)
    else:
        # Run API command for DownloadedMoviesScan without passing a downloadClientId
        #   - DownloadedMoviesScan with a path and downloadClientId
        logger.info("Queued import using just the file path '{}'".format(abspath_string))
        result = api.post_command('DownloadedMoviesScan', path=abspath_string)

    # Log results
    message = result
    if isinstance(result, dict) or isinstance(result, list):
        message = pprint.pformat(result, indent=1)
    logger.debug("Queued import result \n{}".format(message))
    if (isinstance(result, dict)) and result.get('message'):
        logger.error("Failed to queued import of file: '{}'".format(dest_path))
        return
    # TODO: Check for other possible outputs
    logger.info("Successfully queued import of file: '{}'".format(dest_path))


def process_files(settings, source_file, destination_files, host_url, api_key):
    api = RadarrAPI(host_url, api_key)

    mode = settings.get_setting('mode')

    # Get the basename of the file
    for dest_file in destination_files:
        if mode == 'update_mode':
            update_mode(api, dest_file)
        elif mode == 'import_mode':
            minimum_file_size = settings.get_setting('minimum_file_size')
            if check_file_size_under_max_file_size(dest_file, minimum_file_size):
                # Ignore this file
                logger.info("Ignoring file as it is under configured minimum size file: '{}'".format(dest_file))
                continue
            import_mode(api, source_file, dest_file)


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

    # Fetch destination and source files
    source_file = data.get('source_data', {}).get('abspath')
    destination_files = data.get('destination_files', [])

    # Setup API
    host_url = settings.get_setting('host_url')
    api_key = settings.get_setting('api_key')
    process_files(settings, source_file, destination_files, host_url, api_key)
