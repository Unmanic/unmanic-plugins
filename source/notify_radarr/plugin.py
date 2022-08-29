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
import time

import humanfriendly
from pyarr import RadarrAPI
from pyarr.exceptions import (
    PyarrAccessRestricted,
    PyarrBadGateway,
    PyarrConnectionError,
    PyarrResourceNotFound,
    PyarrUnauthorizedError,
)
from unmanic.libs.unplugins.settings import PluginSettings

# Configure plugin logger
logger = logging.getLogger("Unmanic.Plugin.notify_radarr")


class Settings(PluginSettings):
    settings = {
        'host_url':                  'http://localhost:7878',
        'api_key':                   '',
        'mode':                      'update_mode',
        'rename_files':              False,
        'limit_import_on_file_size': True,
        'minimum_file_size':         '100MB',
    }

    def __init__(self, *args, **kwargs):
        super(Settings, self).__init__(*args, **kwargs)
        self.form_settings = {
            "host_url":                  {
                "label":   "Radarr LAN IP Address",
                "tooltip": "Ensure the address starts with 'http'",
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
            "rename_files":              self.__set_rename_files(),
            "limit_import_on_file_size": self.__set_limit_import_on_file_size(),
            "minimum_file_size":         self.__set_minimum_file_size(),
        }

    def __set_rename_files(self):
        values = {
            "label":       "Trigger Radarr file renaming",
            "tooltip":     "Trigger Radarr to re-name files according to the defined naming scheme",
            "sub_setting": True,
        }
        if self.get_setting('mode') != 'update_mode':
            values["display"] = 'hidden'
        return values

    def __set_limit_import_on_file_size(self):
        values = {
            "label":       "Limit file import size",
            "tooltip":     "Enable limiting the Radarr notification on items over a set file size",
            "sub_setting": True,
        }
        if self.get_setting('mode') != 'import_mode':
            values["display"] = 'hidden'
        return values

    def __set_minimum_file_size(self):
        values = {
            "label":       "Minimum file size",
            "description": "Specify the minimum file size of a file that would trigger a notification",
            "sub_setting": True,
        }
        if self.get_setting('mode') != 'import_mode':
            values["display"] = 'hidden'
        elif not self.get_setting('limit_import_on_file_size'):
            values["display"] = 'disabled'
        return values


def check_file_size_under_max_file_size(path, minimum_file_size):
    file_stats = os.stat(os.path.join(path))
    if int(humanfriendly.parse_size(minimum_file_size)) < int(file_stats.st_size):
        return False
    return True


def update_mode(api, abspath, rename_files):
    basename = os.path.basename(abspath)

    # Run lookup search to fetch movie data and ID for rescan
    lookup_results = api.lookup_movie(str(basename))
    logger.debug("lookup results: %s", str(lookup_results))

    # Loop over search results and just use the first result (best thing I can think of)
    movie_data = {}
    for result in lookup_results:
        if result.get('id'):
            movie_data = result
            break

    # Parse movie data
    movie_title = movie_data.get('title')
    logger.debug("Detected movie title: %s", movie_title)
    movie_id = movie_data.get('id')
    if not movie_id:
        logger.error("Missing movie ID. Failed to queue refresh of movie for file: '%s'", abspath)
        return
    logger.debug("Detected movie ID: %s", movie_id)

    try:
        # Run API command for RefreshMovie
        #   - RefreshMovie with a movie ID
        # return on error to ensure rename function is not executed
        result = api.post_command('RefreshMovie', movieIds=[movie_id])
        logger.debug("Received result:\n%s", str(result))

        if result.get('message'):
            logger.error("Failed to queue refresh of movie ID '%s' for file: '%s'", movie_id, abspath)
            logger.error("Response from radarr: %s", result['message'])
            return
        else:
            logger.info("Successfully queued refresh of movie '%s' for file: '%s'", movie_title, abspath)
    except PyarrUnauthorizedError:
        logger.error("Failed to queue refresh of movie '%s' for file: '%s'", movie_title, abspath)
        logger.error("Unauthorized. Please ensure valid API Key is used.")
        return
    except PyarrAccessRestricted:
        logger.error("Failed to queue refresh of movie '%s' for file: '%s'", movie_title, abspath)
        logger.error("Access restricted. Please ensure API Key has correct permissions")
        return
    except PyarrResourceNotFound:
        logger.error("Failed to queue refresh of movie '%s' for file: '%s'", movie_title, abspath)
        logger.error("Resource not found")
        return
    except PyarrBadGateway:
        logger.error("Failed to queue refresh of movie '%s' for file: '%s'", movie_title, abspath)
        logger.error("Bad Gateway. Check your server is accessible")
        return
    except PyarrConnectionError:
        logger.error("Failed to queue refresh of movie '%s' for file: '%s'", movie_title, abspath)
        logger.error("Timeout connecting to radarr. Check your server is accessible")
        return

    if rename_files:
        time.sleep(3)  # Must give time for the refresh to complete before we run the rename.
        try:
            result = api.post_command('RenameMovie', movieIds=[movie_id])
            logger.debug("Received result for 'RenameMovie' command:\n%s", result)
            if isinstance(result, dict):
                logger.info("Successfully triggered rename of movie '%s' for file: '%s'", movie_title, abspath)
            else:
                logger.error("Failed to trigger rename of movie ID '%s' for file: '%s'", movie_id, abspath)
        except PyarrUnauthorizedError:
            logger.error("Failed to trigger rename of movie '%s' for file: '%s'", movie_title, abspath)
            logger.error("Unauthorized. Please ensure valid API Key is used.")
        except PyarrAccessRestricted:
            logger.error("Failed to trigger rename of movie '%s' for file: '%s'", movie_title, abspath)
            logger.error("Access restricted. Please ensure API Key has correct permissions")
        except PyarrResourceNotFound:
            logger.error("Failed to trigger rename of movie '%s' for file: '%s'", movie_title, abspath)
            logger.error("Resource not found")
        except PyarrBadGateway:
            logger.error("Failed to trigger rename of movie '%s' for file: '%s'", movie_title, abspath)
            logger.error("Bad Gateway. Check your server is accessible")
        except PyarrConnectionError:
            logger.error("Failed to trigger rename of movie '%s' for file: '%s'", movie_title, abspath)
            logger.error("Timeout connecting to radarr. Check your server is accessible")


def import_mode(api, source_path, dest_path):
    source_basename = os.path.basename(source_path)
    abspath_string = dest_path.replace('\\', '')

    download_id = None
    movie_title = None

    queue = api.get_queue()
    message = pprint.pformat(queue, indent=1)
    logger.debug("Current queue \n%s", message)
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
        logger.info("Queued import movie '%s' using downloadClientId: '%s'", movie_title, download_id)
        result = api.post_command('DownloadedMoviesScan', path=abspath_string, downloadClientId=download_id)
    else:
        # Run API command for DownloadedMoviesScan without passing a downloadClientId
        #   - DownloadedMoviesScan with a path and downloadClientId
        logger.info("Queued import using just the file path '%s'", abspath_string)
        result = api.post_command('DownloadedMoviesScan', path=abspath_string)

    # Log results
    message = result
    if isinstance(result, dict) or isinstance(result, list):
        message = pprint.pformat(result, indent=1)
    logger.debug("Queued import result \n%s", message)
    if (isinstance(result, dict)) and result.get('message'):
        logger.error("Failed to queued import of file: '%s'", dest_path)
        return
    # TODO: Check for other possible outputs
    logger.info("Successfully queued import of file: '%s'", dest_path)


def process_files(settings, source_file, destination_files, host_url, api_key):
    api = RadarrAPI(host_url, api_key)

    mode = settings.get_setting('mode')
    rename_files = settings.get_setting('rename_files')

    # Get the basename of the file
    for dest_file in destination_files:
        if mode == 'update_mode':
            update_mode(api, dest_file, rename_files)
        elif mode == 'import_mode':
            minimum_file_size = settings.get_setting('minimum_file_size')
            if check_file_size_under_max_file_size(dest_file, minimum_file_size):
                # Ignore this file
                logger.info("Ignoring file as it is under configured minimum size file: '%s'", dest_file)
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
