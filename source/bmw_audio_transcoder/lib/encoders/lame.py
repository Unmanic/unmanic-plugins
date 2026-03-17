#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
    plugins.libx.py

    Written by:               Josh.5 <jsunnex@gmail.com>
    Date:                     12 Jun 2022, (9:48 AM)

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


class LameEncoder:
    encoders = [
        "libmp3lame",
    ]

    def __init__(self, settings):
        self.settings = settings

    @staticmethod
    def options():
        return {
            "encoder_ratecontrol_method": "VBR",
            "constant_quality_scale":     "4",
            "average_bitrate":            "192",
        }

    @staticmethod
    def generate_default_args(settings):
        """
        Generate a list of args for using a lib decoder

        :param settings:
        :return:
        """
        # No default args required
        generic_kwargs = {}
        advanced_kwargs = {}
        return generic_kwargs, advanced_kwargs

    @staticmethod
    def generate_filtergraphs():
        """
        Generate the required filter for this encoder
        No filters are required for lib encoders

        :return:
        """
        return []

    @staticmethod
    def get_output_file_extension(encoder):
        """
        Given an encoder, return the required file extension for that codec
        :param encoder:
        :return:
        """
        if encoder == "libmp3lame":
            return "mp3"
        return ""

    def args(self, stream_id):
        stream_encoding = []

        # Use defaults for basic mode
        if self.settings.get_setting('mode') in ['basic']:
            defaults = self.options()
            stream_encoding += [
                '-qscale:a', str(self.settings.get_setting('constant_quality_scale')),
            ]
            return stream_encoding

        if self.settings.get_setting('encoder_ratecontrol_method') in ['VBR']:
            # Set values for constant quantizer scale
            stream_encoding += [
                '-q:a', str(self.settings.get_setting('constant_quality_scale')),
            ]
        elif self.settings.get_setting('encoder_ratecontrol_method') in ['CBR']:
            # Set values for constant quantizer scale
            stream_encoding += [
                '-b:a', "{}k".format(self.settings.get_setting('average_bitrate')),
            ]

        return stream_encoding

    def __set_default_option(self, select_options, key, default_option=None):
        """
        Sets the default option if the currently set option is not available

        :param select_options:
        :param key:
        :return:
        """
        available_options = []
        for option in select_options:
            available_options.append(option.get('value'))
            if not default_option:
                default_option = option.get('value')
        if self.settings.get_setting(key) not in available_options:
            self.settings.set_setting(key, default_option)

    def get_encoder_ratecontrol_method_form_settings(self):
        # TODO: Add Two-Pass
        values = {
            "label":          "Encoder ratecontrol method",
            "sub_setting":    True,
            "input_type":     "select",
            "select_options": []
        }
        common_select_options = [
            {
                "value": "VBR",
                "label": "VBR - Constant Quality Variable Bitrate",
            },
        ]
        if self.settings.get_setting('mode') in ['standard']:
            values["select_options"] = common_select_options + [
                {
                    "value": "CBR",
                    "label": "CBR - Constant Bitrate",
                },
            ]
        self.__set_default_option(values['select_options'], 'encoder_ratecontrol_method', default_option='VBR')
        if self.settings.get_setting('mode') not in ['standard']:
            values["display"] = "hidden"
        return values

    def get_constant_quality_scale_form_settings(self):
        # Lower is better
        values = {
            "label":          "Quality scale",
            "description":    "",
            "sub_setting":    True,
            "input_type":     "slider",
            "slider_options": {
                "min": 0,
                "max": 9,
            },
        }
        if self.settings.get_setting('mode') not in ['basic', 'standard']:
            values["display"] = "hidden"
        if self.settings.get_setting('encoder_ratecontrol_method') not in ['VBR']:
            values["display"] = "hidden"
        if self.settings.get_setting('audio_encoder') in ['libmp3lame']:
            values["description"] = "Default value for libmp3lame = 4.\n" \
                                    "Setting this to 0-3 will normally produce transparent results,\n" \
                                    "4 (default) should be close to perceptual transparency,\n" \
                                    "and 6 produces an 'acceptable' quality."
        return values

    def get_average_bitrate_form_settings(self):
        values = {
            "label":          "Bitrate",
            "sub_setting":    True,
            "input_type":     "select",
            "select_options": [
                {
                    "value": "8",
                    "label": "8Kbit/s",
                },
                {
                    "value": "16",
                    "label": "16Kbit/s",
                },
                {
                    "value": "24",
                    "label": "24Kbit/s",
                },
                {
                    "value": "32",
                    "label": "32Kbit/s",
                },
                {
                    "value": "40",
                    "label": "40Kbit/s",
                },
                {
                    "value": "48",
                    "label": "48Kbit/s",
                },
                {
                    "value": "64",
                    "label": "64Kbit/s",
                },
                {
                    "value": "80",
                    "label": "80Kbit/s",
                },
                {
                    "value": "96",
                    "label": "96Kbit/s",
                },
                {
                    "value": "112",
                    "label": "112Kbit/s",
                },
                {
                    "value": "128",
                    "label": "128Kbit/s",
                },
                {
                    "value": "160",
                    "label": "160Kbit/s",
                },
                {
                    "value": "192",
                    "label": "192Kbit/s",
                },
                {
                    "value": "224",
                    "label": "224Kbit/s",
                },
                {
                    "value": "256",
                    "label": "256Kbit/s",
                },
                {
                    "value": "320",
                    "label": "320Kbit/s",
                },
            ]
        }
        if self.settings.get_setting('mode') not in ['standard']:
            values["display"] = "hidden"
        if self.settings.get_setting('encoder_ratecontrol_method') not in ['CBR']:
            values["display"] = "hidden"
        if self.settings.get_setting('audio_encoder') in ['libmp3lame']:
            values["description"] = "NOTE: Using -b:a 320k is generally considered wasteful because\n" \
                                    "setting VBR to 0-3 will normally produce transparent results\n" \
                                    "and MP3 is lossy anyway, so if you really want the highest quality\n" \
                                    "use a lossless format such as FLAC."
        return values
