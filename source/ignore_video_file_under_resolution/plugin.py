#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
    plugins.__init__.py

    Written by:               Josh.5 <jsunnex@gmail.com>
    Date:                     02 May 2022, (5:19 PM)

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

from unmanic.libs.unplugins.settings import PluginSettings

from ignore_video_file_under_resolution.lib.ffmpeg import Probe

# Configure plugin logger
logger = logging.getLogger("Unmanic.Plugin.ignore_video_file_under_resolution")

default_resolutions = {
    '480p_sdtv':   {
        'width':  854,
        'height': 480,
        'label':  "480p (SDTV)",
    },
    '576p_sdtv':   {
        'width':  1024,
        'height': 576,
        'label':  "576p (SDTV)",
    },
    '720p_hdtv':   {
        'width':  1280,
        'height': 720,
        'label':  "720p (HDTV)",
    },
    '1080p_hdtv':  {
        'width':  1920,
        'height': 1080,
        'label':  "1080p (HDTV)",
    },
    'dci_2k_hdtv': {
        'width':  2048,
        'height': 1080,
        'label':  "DCI 2K (HDTV)",
    },
    '1440p':       {
        'width':  2560,
        'height': 1440,
        'label':  "1440p (WQHD)",
    },
    '4k_uhd':      {
        'width':  3840,
        'height': 2160,
        'label':  "4K (UHD)",
    },
    'dci_4k':      {
        'width':  4096,
        'height': 2160,
        'label':  "DCI 4K",
    },
    '8k_uhd':      {
        'width':  8192,
        'height': 4608,
        'label':  "8k (UHD)",
    },
}


class Settings(PluginSettings):
    settings = {
        "target_resolution":  '720p_hdtv',
        "custom_resolutions": False,
        '480p_sdtv_width':    default_resolutions.get('480p_sdtv', {}).get('width'),
        '480p_sdtv_height':   default_resolutions.get('480p_sdtv', {}).get('height'),
        '576p_sdtv_width':    default_resolutions.get('576p_sdtv', {}).get('width'),
        '576p_sdtv_height':   default_resolutions.get('576p_sdtv', {}).get('height'),
        '720p_hdtv_width':    default_resolutions.get('720p_hdtv', {}).get('width'),
        '720p_hdtv_height':   default_resolutions.get('720p_hdtv', {}).get('height'),
        '1080p_hdtv_width':   default_resolutions.get('1080p_hdtv', {}).get('width'),
        '1080p_hdtv_height':  default_resolutions.get('1080p_hdtv', {}).get('height'),
        'dci_2k_hdtv_width':  default_resolutions.get('dci_2k_hdtv', {}).get('width'),
        'dci_2k_hdtv_height': default_resolutions.get('dci_2k_hdtv', {}).get('height'),
        '1440p_width':        default_resolutions.get('1440p', {}).get('width'),
        '1440p_height':       default_resolutions.get('1440p', {}).get('height'),
        '4k_uhd_width':       default_resolutions.get('4k_uhd', {}).get('width'),
        '4k_uhd_height':      default_resolutions.get('4k_uhd', {}).get('height'),
        'dci_4k_width':       default_resolutions.get('dci_4k', {}).get('width'),
        'dci_4k_height':      default_resolutions.get('dci_4k', {}).get('height'),
        '8k_uhd_width':       default_resolutions.get('8k_uhd', {}).get('width'),
        '8k_uhd_height':      default_resolutions.get('8k_uhd', {}).get('height'),
    }

    def __init__(self, *args, **kwargs):
        super(Settings, self).__init__(*args, **kwargs)
        self.form_settings = {
            "target_resolution":  self.__set_target_resolution_form_settings(),
            "custom_resolutions": {
                "label": "Customise resolution values",
            },
        }
        for key in self.settings:
            if '_width' not in key and '_height' not in key:
                continue
            res_key = key[:-len('_width')]
            axis = 'width'
            if '_height' in key:
                res_key = key[:-len('_height')]
                axis = 'height'
            title_prefix = default_resolutions.get(res_key, {}).get('label')
            current_val = default_resolutions.get(res_key, {}).get(axis)
            min_val = int(int(current_val) / 2)
            max_val = int(int(current_val) * 2)
            self.form_settings[key] = self.__set_custom_resolution_form_settings(title_prefix, axis,
                                                                                 min_val=min_val, max_val=max_val)

    def __set_custom_resolution_form_settings(self, title_prefix, axis, min_val=0, max_val=999999, step=1):
        values = {
            "label":          "{} - {}".format(title_prefix, axis.capitalize()),
            "input_type":     "slider",
            "slider_options": {
                "min":    min_val,
                "max":    max_val,
                "step":   step,
                "suffix": "px"
            },
        }
        if not self.get_setting('custom_resolutions'):
            values["display"] = 'hidden'
        return values

    def __set_target_resolution_form_settings(self):
        def generate_label_resolution(key):
            return "{} - {}x{}".format(default_resolutions.get(key, {}).get('label'),
                                       default_resolutions.get(key, {}).get('width'),
                                       default_resolutions.get(key, {}).get('height'))

        values = {
            "label":          "Resolution",
            "input_type":     "select",
            "select_options": [
                {
                    'value': '480p_sdtv',
                    'label': generate_label_resolution('480p_sdtv'),
                },
                {
                    'value': '576p_sdtv',
                    'label': generate_label_resolution('576p_sdtv'),
                },
                {
                    'value': '720p_hdtv',
                    'label': generate_label_resolution('720p_hdtv'),
                },
                {
                    'value': '1080p_hdtv',
                    'label': generate_label_resolution('1080p_hdtv'),
                },
                {
                    'value': 'dci_2k_hdtv',
                    'label': generate_label_resolution('dci_2k_hdtv'),
                },
                {
                    'value': '1440p',
                    'label': generate_label_resolution('1440p'),
                },
                {
                    'value': '4k_uhd',
                    'label': generate_label_resolution('4k_uhd'),
                },
                {
                    'value': 'dci_4k',
                    'label': generate_label_resolution('dci_4k'),
                },
                {
                    'value': '8k_uhd',
                    'label': generate_label_resolution('8k_uhd'),
                },
            ],
        }
        return values


def get_test_resolution(settings):
    target_resolution = settings.get_setting('target_resolution')
    # Set the target resolution
    custom_resolutions = settings.get_setting('custom_resolutions')
    test_resolution = {
        'width':  default_resolutions.get(target_resolution, {}).get('width'),
        'height': default_resolutions.get(target_resolution, {}).get('height'),
    }
    if custom_resolutions:
        test_resolution = {
            'width':  settings.get_setting('{}_width'.format(target_resolution)),
            'height': settings.get_setting('{}_height'.format(target_resolution)),
        }
    return test_resolution


def get_video_stream_data(streams):
    width = 0
    height = 0
    video_stream_index = 0

    for stream in streams:
        if stream.get('codec_type') == 'video':
            width = stream.get('width', stream.get('coded_width', 0))
            height = stream.get('height', stream.get('coded_height', 0))
            video_stream_index = stream.get('index')
            break

    return width, height, video_stream_index


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

    # Get file probe
    probe = Probe(logger, allowed_mimetypes=['video'])
    if 'ffprobe' in data.get('shared_info', {}):
        if not probe.set_probe(data.get('shared_info', {}).get('ffprobe')):
            # Failed to set ffprobe from shared info.
            # Probably due to it being for an incompatible mimetype declared above
            return
    elif not probe.file(abspath):
        # File probe failed, skip the rest of this test
        return
    # Set file probe to shared infor for subsequent file test runners
    if 'shared_info' in data:
        data['shared_info'] = {}
    data['shared_info']['ffprobe'] = probe.get_probe()

    # Configure settings object (maintain compatibility with v1 plugins)
    if data.get('library_id'):
        settings = Settings(library_id=data.get('library_id'))
    else:
        settings = Settings()

    # Get video width and height
    vid_width, vid_height, video_stream_index = get_video_stream_data(probe.get('streams', []))

    # Get the test resolution
    test_resolution = get_test_resolution(settings)

    limit_label = default_resolutions.get(settings.get_setting('target_resolution'), {}).get('label')
    limit_width = default_resolutions.get(settings.get_setting('target_resolution'), {}).get('width')
    limit_height = default_resolutions.get(settings.get_setting('target_resolution'), {}).get('height')
    if int(vid_width) < int(test_resolution['width']) or int(vid_height) < int(test_resolution['height']):
        # Ignore this file
        data['add_file_to_pending_tasks'] = False
        logger.debug(
            "File '%s' should be ignored - resolution %sx%s is under the set limit of %s %sx%s.",
            abspath,
            vid_width,
            vid_height,
            limit_label,
            limit_width,
            limit_height)
        return
    logger.debug(
        "File '%s' will not be ignored - resolution %sx%s is over the set limit of %s %sx%s.",
        abspath,
        vid_width,
        vid_height,
        limit_label,
        limit_width,
        limit_height)
