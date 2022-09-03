#!/usr/bin/env python3
# -*- coding:utf-8 -*-
###
# File: global_settings.py
# Project: lib
# File Created: Friday, 26th August 2022 5:06:41 pm
# Author: Josh.5 (jsunnex@gmail.com)
# -----
# Last Modified: Monday, 29th August 2022 10:34:26 pm
# Modified By: Josh.5 (jsunnex@gmail.com)
###
# !/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
    plugins.global_settings.py

    Written by:               Josh.5 <jsunnex@gmail.com>
    Date:                     10 Jun 2022, (6:52 PM)

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


class GlobalSettings:

    def __init__(self, settings):
        self.settings = settings

    @staticmethod
    def options():
        # Global and main config options
        return {
            "main_options":           {
                "mode": "basic",
            },
            "encoder_selection":      {
                "audio_codec":     "mp3",
                "force_transcode": False,
                "audio_encoder":   "libmp3lame",
            },
            "advanced_input_options": {
                "main_options":     "",
                "advanced_options": "-strict -2\n",
                "custom_options":   "libmp3lame\n"
                                    "-b:a 192k\n",
            },
            "output_settings":        {
            },
            "filter_settings":        {
            },
        }

    def __set_default_option(self, select_options, key, default_option=None):
        """
        Sets the default option if the currently set option is not available

        :param select_options:
        :param key:
        :return:
        """
        available_options = []
        for option in select_options:
            available_options.append(option.get("value"))
            if not default_option:
                default_option = option.get("value")
        if self.settings.get_setting(key) not in available_options:
            self.settings.set_setting(key, default_option)

    def get_mode_form_settings(self):
        return {
            "label":          "Config mode",
            "input_type":     "select",
            "select_options": [
                {
                    "value": "basic",
                    "label": "Basic (Not sure what I am doing. Configure most of it for me.)",
                },
                {
                    "value": "standard",
                    "label": "Standard (I know how to transcode some audio. Let me tweak some settings.)",
                },
                {
                    "value": "advanced",
                    "label": "Advanced (Dont tell me what to do, I write FFmpeg commands in my sleep.)",
                },
            ],
        }

    def get_audio_codec_form_settings(self):
        values = {
            "label":          "Audio Codec",
            "input_type":     "select",
            "select_options": [
                {
                    "value": "aac",
                    "label": "AAC",
                },
                {
                    "value": "mp3",
                    "label": "MP3",
                },
            ],
        }
        if self.settings.get_setting('mode') not in ['basic', 'standard', 'advanced']:
            values["display"] = 'hidden'
        return values

    def get_force_transcode_form_settings(self):
        values = {
            "label":       "Force transcoding even if the file is already using the desired audio codec",
            "description": "Will force a transcode of the audio file even if it matches the selected audio codec.\n"
                           "A file will only be forced to be transcoded once.\n"
                           "After that it is flagged to prevent it being added to the pending tasks list in a loop.",
            "sub_setting": True,
        }
        if self.settings.get_setting('mode') not in ['basic', 'standard', 'advanced']:
            values["display"] = 'hidden'
        return values

    def get_audio_encoder_form_settings(self):
        values = {
            "label":          "Audio Encoder",
            "input_type":     "select",
            "select_options": [],
        }
        if self.settings.get_setting('audio_codec') == 'aac':
            # TODO: Add libfdk_aac encoder
            #   {
            #       "value": "libfdk_aac",
            #       "label": "Fraunhofer FDK AAC",
            #   },
            values['select_options'] = [
                {
                    "value": "aac",
                    "label": "Native FFmpeg AAC encoder",
                },
            ]
        elif self.settings.get_setting('audio_codec') == 'mp3':
            values['select_options'] = [
                {
                    "value": "libmp3lame",
                    "label": "LAME - libmp3lame",
                },
            ]
        self.__set_default_option(values['select_options'], 'audio_encoder')
        if self.settings.get_setting('mode') not in ['basic', 'standard']:
            values["display"] = 'hidden'
        return values

    def get_main_options_form_settings(self):
        values = {
            "label":      "Write your own custom main options",
            "input_type": "textarea",
        }
        if self.settings.get_setting('mode') not in ['advanced']:
            values["display"] = 'hidden'
        return values

    def get_advanced_options_form_settings(self):
        values = {
            "label":      "Write your own custom advanced options",
            "input_type": "textarea",
        }
        if self.settings.get_setting('mode') not in ['advanced']:
            values["display"] = 'hidden'
        return values

    def get_custom_options_form_settings(self):
        values = {
            "label":      "Write your own custom audio options (starting with the encoder to use)",
            "input_type": "textarea",
        }
        if self.settings.get_setting('mode') not in ['advanced']:
            values["display"] = 'hidden'
        return values
