#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
    plugins.plugin.py

    Written by:               Josh.5 <jsunnex@gmail.com>
    Date:                     10 May 2022, (7:57 AM)

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
import mimetypes
import shutil

from unmanic.libs.unplugins.settings import PluginSettings

# Configure plugin logger
logger = logging.getLogger("Unmanic.Plugin.auto_rotate_images")


class Settings(PluginSettings):
    settings = {}

    def __init__(self, *args, **kwargs):
        super(Settings, self).__init__(*args, **kwargs)


def dependencies_installed():
    result = True
    dep_list = ['jhead', 'jpegtran']
    for dep in dep_list:
        if not shutil.which(dep):
            logger.error("Missing dependency '{}'. Please install this before running again.".format(dep))
            result = False
    return result


def check_file_is_image(file_path):
    """

    :param file_path:
    :return:
    """
    # Init (reset) our mimetype list
    mimetypes.init()
    # Only run this check against video/audio/image MIME types
    file_type = mimetypes.guess_type(file_path)[0]
    # If the file has no MIME type then it cannot be tested
    if file_type is None:
        logger.debug("Unable to fetch file MIME type - '{}'".format(file_path))
        return False
    # Make sure the MIME type is either audio, video or image
    file_type_category = file_type.split('/')[0]
    if file_type_category not in ['image']:
        logger.debug("File MIME type is not 'image' - '{}'".format(file_path))
        return False

    return True


def build_command(file_path):
    """
    Generate a command to be executed against the file

    Credit: 
        - https://gist.github.com/ljm42/02b54ce9cc36f992515b
            (jhead -autorot -ft "/mnt/user/MediaPictures/"*.[jJ][pP][gG])

    :param file_path:
    :return:
    """
    command = [
        'jhead',
        '-autorot',
        '-ft',
        file_path,
    ]
    return command


def check_if_work_required(file_path):
    """
    Check if the file is an image and needs rotating

    Credit for check:
        - https://stackoverflow.com/questions/13872331/rotating-an-image-with-orientation-specified-in-exif-using-python-without-pil-in

    :param file_path:
    :return:
    """
    if not check_file_is_image(file_path):
        return False

    from PIL import Image, ExifTags

    try:
        image = Image.open(file_path)

        for orientation in ExifTags.TAGS.keys():
            if ExifTags.TAGS[orientation] == 'Orientation':
                break

        exif = image._getexif()
        if exif[orientation] == 1:
            # Image is correctly rotated
            return False
        # Image does require rotation
        return True

    except (TypeError, AttributeError, KeyError, IndexError):
        logger.debug("File contains no Exif data to determine rotation - '{}'".format(file_path))
        return False


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
    # Get the path to the file
    abspath = data.get('path')

    if not dependencies_installed():
        return

    if check_if_work_required(abspath):
        data['add_file_to_pending_tasks'] = True
        logger.debug("File '{}' should be added to task list. Rotation needs fixing.".format(abspath))


def on_worker_process(data):
    """
    Runner function - enables additional configured processing jobs during the worker stages of a task.

    The 'data' object argument includes:
        worker_log              - Array, the log lines that are being tailed by the frontend. Can be left empty.
        library_id              - Number, the library that the current task is associated with.
        exec_command            - Array, a subprocess command that Unmanic should execute. Can be empty.
        command_progress_parser - Function, a function that Unmanic can use to parse the STDOUT of the command to collect progress stats. Can be empty.
        file_in                 - String, the source file to be processed by the command.
        file_out                - String, the destination that the command should output (may be the same as the file_in if necessary).
        original_file_path      - String, the absolute path to the original file.
        repeat                  - Boolean, should this runner be executed again once completed with the same variables.

    :param data:
    :return:
    
    """
    # Get the path to the file
    abspath = data.get('file_in')

    if not dependencies_installed():
        return

    if check_if_work_required(abspath):
        data['exec_command'] = build_command(abspath)
