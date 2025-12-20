#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
    Written by:               Josh.5 <jsunnex@gmail.com>
    Date:                     20 December 2025, (10:00 PM)

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
import requests

from unmanic.libs.unplugins.settings import PluginSettings

# Configure plugin logger
logger = logging.getLogger("Unmanic.Plugin.notify_pushbullet")


class Settings(PluginSettings):
    settings = {
        "Pushbullet Access Token": "",
    }

    def __init__(self, *args, **kwargs):
        super(Settings, self).__init__(*args, **kwargs)


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
    settings = Settings(library_id=data.get('library_id'))
    access_token = settings.get_setting("Pushbullet Access Token")

    if not access_token:
        logger.warning("Pushbullet Access Token not set. Skipping notification.")
        return data

    source_file = data["source_data"]["basename"]
    
    if data["task_processing_success"] and data["file_move_processes_success"]:
        title = "Unmanic Task Completed"
        body = f"Successfully processed: {source_file}"
    else:
        title = "Unmanic Task Failed"
        body = f"Failed to process: {source_file}"

    # Pushbullet API
    url = "https://api.pushbullet.com/v2/pushes"
    headers = {
        "Access-Token": access_token,
        "Content-Type": "application/json"
    }
    payload = {
        "type": "note",
        "title": title,
        "body": body
    }

    try:
        response = requests.post(url, headers=headers, json=payload)
        response.raise_for_status()
        logger.info(f"Pushbullet notification sent: {response.status_code}")
    except requests.exceptions.RequestException as e:
        logger.error(f"Failed to send Pushbullet notification: {e}")

    return data