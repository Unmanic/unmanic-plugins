#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
    Written by:               yajrendrag <yajdude@gmail.com>
    Date:                     26 January 2023, (10:00 AM)

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
import requests
from unmanic.libs.unplugins.settings import PluginSettings

# Configure plugin logger
logger = logging.getLogger("Unmanic.Plugin.notify_jellyfin")


class Settings(PluginSettings):
    settings = {
        'Jellyfin URL':                'http://localhost:8096',
        'Jellyfin API Key':              '',
        'Notify on Task Failure?': False,
    }


def update_jellyfin(jellyfin_url, jellyfin_apikey):
    headers = {'X-MediaBrowser-Token': jellyfin_apikey}
    try:
        r = requests.post(jellyfin_url + "/Library/Refresh", headers=headers)
    except (ConnectionRefusedError, requests.exceptions.ConnectionError) as error:
        logger.error("Error Connecting to Jellyfin - unable to reach or unauthorized")
        
    if r.status_code == 204:
        logger.info("Notifying Jellyfin ('{}') to update its library.".format(jellyfin_url))
    else:
        logger.error("Error notifying Jellyfin - Error Code:('{}').".format(r.status_code))

def on_postprocessor_task_results(data):
    """
    Runner function - provides a means for additional postprocessor functions based on the task success.

    The 'data' object argument includes:
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

    if not data.get('task_processing_success') and not settings.get_setting('Notify on Task Failure?'):
        return data

    jellyfin_url = settings.get_setting('Jellyfin URL')
    jellyfin_apikey = settings.get_setting('Jellyfin API Key')
    update_jellyfin(jellyfin_url, jellyfin_apikey)

    return data
