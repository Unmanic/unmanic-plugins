#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
    Written by:               R3dC4p <31379247+R3dC4p@users.noreply.github.com>
    Date:                     25 May 2021, (1:00 AM)
 
    Copyright:
        Copyright (C) 2021 R3dC4p

        This program is free software: you can redistribute it and/or modify it under the terms of the GNU General
        Public License as published by the Free Software Foundation, version 3.

        This program is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the
        implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License
        for more details.

        You should have received a copy of the GNU General Public License along with this program.
        If not, see <https://www.gnu.org/licenses/>.

"""
import os
from unmanic.libs.unplugins.settings import PluginSettings


class Settings(PluginSettings):
    settings = {
        "destination directory": "/library",
    }
    form_settings = {
        "destination directory": {
            "input_type": "browse_directory",
        },
    }


def on_postprocessor_file_movement(data):
    """
    Runner function - configures additional postprocessor file movements during the postprocessor stage of a task.
    The 'data' object argument includes:
        source_data             - Dictionary containing data pertaining to the original source file.
        remove_source_file      - Boolean, should Unmanic remove the original source file after all copy operations are complete.
        copy_file               - Boolean, should Unmanic run a copy operation with the returned data variables.
        file_in                 - The converted cache file to be copied by the postprocessor.
        file_out                - The destination file that the file will be copied to.
    :param data:
    :return:
    """
    settings = Settings()
    destdir = settings.get_setting('destination directory')
    path = data['source_data'].get('abspath')
    # Keep source file
    data['remove_source_file'] = False

    # Get the parent directory of the file
    dirname = os.path.dirname(path)

    # get the base name of that directory path
    subdir = os.path.basename(dirname)

    # Make sub-folder in destination directory
    if not os.path.exists(os.path.join(destdir, subdir)):
        os.makedirs(os.path.join(destdir, subdir))

    # get the basename out of the output file
    b_out = os.path.basename(data['file_out'])

    # output the file
    data['file_out'] = os.path.join(destdir, subdir, b_out)

    return data
