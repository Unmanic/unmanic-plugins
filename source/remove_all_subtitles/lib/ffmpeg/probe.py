#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
    plugins.probe.py

    Written by:               Josh.5 <jsunnex@gmail.com>
    Date:                     12 Aug 2021, (9:20 AM)

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
import json
import mimetypes
import os
import subprocess
from logging import Logger


class FFProbeError(Exception):
    """
    FFProbeError
    Custom exception for errors encountered while executing the ffprobe command.
    """

    def __init___(self, path, info):
        Exception.__init__(self, "Unable to fetch data from file {}. {}".format(path, info))
        self.path = path
        self.info = info


def ffprobe_cmd(params):
    """
    Execute a ffprobe command subprocess and read the output

    :param params:
    :return:
    """
    command = ["ffprobe"] + params

    pipe = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    out, err = pipe.communicate()

    # Check for results
    try:
        raw_output = out.decode("utf-8")
    except Exception as e:
        raise FFProbeError(command, str(e))
    if pipe.returncode == 1 or 'error' in raw_output:
        raise FFProbeError(command, raw_output)
    if not raw_output:
        raise FFProbeError(command, 'No info found')

    return raw_output


def ffprobe_file(vid_file_path):
    """
    Returns a dictionary result from ffprobe command line prove of a file

    :param vid_file_path: The absolute (full) path of the video file, string.
    :return:
    """
    if type(vid_file_path) != str:
        raise Exception('Give ffprobe a full file path of the video')

    params = [
        "-loglevel", "quiet",
        "-print_format", "json",
        "-show_format",
        "-show_streams",
        "-show_error",
        vid_file_path
    ]

    # Check result
    results = ffprobe_cmd(params)
    try:
        info = json.loads(results)
    except Exception as e:
        raise FFProbeError(vid_file_path, str(e))

    return info


class Probe(object):
    """
    Probe
    """

    probe_info = {}

    def __init__(self, logger: Logger, allowed_mimetypes=None):
        self.logger = logger
        if allowed_mimetypes is None:
            allowed_mimetypes = ['audio', 'video', 'image']
        self.allowed_mimetypes = allowed_mimetypes

    def __test_valid_mimetype(self, file_path):
        """
        Test the given file path for its mimetype.
        If the mimetype cannot be detected, it will fail this test.
        If the detected mimetype is not in the configured 'allowed_mimetypes'
            class variable, it will fail this test.

        :param file_path:
        :return:
        """
        # Only run this check against video/audio/image MIME types
        mimetypes.init()
        file_type = mimetypes.guess_type(file_path)[0]

        # If the file has no MIME type then it cannot be tested
        if file_type is None:
            self.logger.debug("Unable to fetch file MIME type - '{}'".format(file_path))
            return False

        # Make sure the MIME type is either audio, video or image
        file_type_category = file_type.split('/')[0]
        if file_type_category not in self.allowed_mimetypes:
            self.logger.debug("File MIME type not in 'audio', 'video' or 'image' - '{}'".format(file_path))
            return False

        return True

    def file(self, file_path):
        """
        Sets the 'probe' dict by probing the given file path.
        Files that are not able to be probed will not set the 'probe' dict.

        :param file_path:
        :return:
        """
        self.probe_info = {}

        # Ensure file exists
        if not os.path.exists(file_path):
            self.logger.debug("File does not exist - '{}'".format(file_path))
            return

        if not self.__test_valid_mimetype(file_path):
            return

        try:
            # Get the file probe info
            self.probe_info = ffprobe_file(file_path)
            return True
        except FFProbeError:
            # This will only happen if it was not a file that could be probed.
            self.logger.debug("File unable to be probed by FFProbe - '{}'".format(file_path))
            return
        except Exception as e:
            # The process failed for some unknown reason. Log it.
            self.logger.debug("Failed to set file probe - ".format(str(e)))
            return

    def get_probe(self):
        """Return the probe dictionary"""
        return self.probe_info

    def get(self, key, default=None):
        """Return the value of the given key from the probe dictionary"""
        return self.probe_info.get(key, default)
