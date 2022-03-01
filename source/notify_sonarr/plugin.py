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

import humanfriendly
from pyarr import SonarrAPI
from unmanic.libs.unplugins.settings import PluginSettings

# Configure plugin logger
logger = logging.getLogger("Unmanic.Plugin.notify_sonarr")


class Settings(PluginSettings):
    settings = {
        'host_url':                  'http://localhost:8989',
        'api_key':                   '',
        'mode':                      'update_series',
        'limit_import_on_file_size': True,
        'minimum_file_size':         '100MB',
    }

    def __init__(self, *args, **kwargs):
        super(Settings, self).__init__(*args, **kwargs)
        self.form_settings = {
            "host_url":                  {
                "label": "Sonarr LAN IP Address",
            },
            "api_key":                   {
                "label": "Sonarr API Key",
            },
            "mode":                      {
                "label":          "Mode",
                "input_type":     "select",
                "select_options": [
                    {
                        'value': "update_series",
                        'label': "Trigger series refresh on task complete",
                    },
                    {
                        'value': "import_episode",
                        'label': "Import episode on task complete",
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
        if self.get_setting('mode') != 'import_episode':
            values["display"] = 'hidden'
        return values

    def __set_minimum_file_size(self):
        values = {
            "label": "Minimum file size",
        }
        if self.get_setting('mode') != 'import_episode':
            values["display"] = 'hidden'
        if not self.get_setting('limit_import_on_file_size'):
            values["display"] = 'hidden'
        return values


def check_file_size_under_max_file_size(path, minimum_file_size):
    file_stats = os.stat(os.path.join(path))
    if int(humanfriendly.parse_size(minimum_file_size)) < int(file_stats.st_size):
        return False
    return True


def update_series(api, abspath):
    basename = os.path.basename(abspath)

    # Fetch episode data
    episode_data = api.get_parsed_title(basename)

    # Fetch a series ID from Sonarr
    series_title = episode_data.get('series', {}).get('title')
    series_id = episode_data.get('series', {}).get('id')
    if not series_id:
        logger.error("Missing series ID. Failed to queued refresh of series for file: '{}'".format(abspath))
        return

    # Run API command for RescanSeries
    #   - RescanSeries with a series ID
    result = api.post_command('RescanSeries', seriesId=series_id)
    if result.get('message'):
        logger.error("Failed to queued refresh of series ID '{}' for file: '{}'".format(series_id, abspath))
        return
    logger.info("Successfully queued refreshed the Series '{}' for file: '{}'".format(series_title, abspath))


def import_episode(api, abspath):
    basename = os.path.basename(abspath)
    title = os.path.splitext(basename)[0].replace('\\', '')
    abspath_string = abspath.replace('\\', '')

    download_id = None
    episode_title = None

    queue = api.get_queue()
    for item in queue.get('records', []):
        item_title = item.get('title')
        if item_title == title:
            download_id = item.get('downloadId')
            episode_title = item.get('episode', {}).get('title')

    # Run import
    if download_id:
        # Run API command for DownloadedEpisodesScan
        #   - DownloadedEpisodesScan with a path and downloadClientId
        logger.info("Queued import episode '{}' using downloadClientId: '{}'".format(episode_title, download_id))
        result = api.post_command('DownloadedEpisodesScan', path=abspath_string, downloadClientId=download_id)
    else:
        # Run API command for DownloadedEpisodesScan without passing a downloadClientId
        #   - DownloadedEpisodesScan with a path and downloadClientId
        logger.info("Queued import using just the file path '{}'".format(abspath_string))
        result = api.post_command('DownloadedEpisodesScan', path=abspath_string)

    # Log results
    if result.get('message'):
        logger.error("Failed to queued import of file: '{}'".format(abspath))
        return
    logger.info("Successfully queued import of file: '{}'".format(abspath))


def process_files(settings, destination_files, host_url, api_key):
    api = SonarrAPI(host_url, api_key)

    mode = settings.get_setting('mode')

    # Get the basename of the file
    for dest_file in destination_files:
        if mode == 'update_series':
            update_series(api, dest_file)
        elif mode == 'import_episode':
            minimum_file_size = settings.get_setting('minimum_file_size')
            if check_file_size_under_max_file_size(dest_file, minimum_file_size):
                # Ignore this file
                logger.info("Ignoring file as it is under configured minimum size file: '{}'".format(dest_file))
                continue
            import_episode(api, dest_file)


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
    process_files(settings, destination_files, host_url, api_key)