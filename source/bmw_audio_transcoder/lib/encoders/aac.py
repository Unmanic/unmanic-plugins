#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
    plugins.libfdk.py

    Written by:               Josh.5 <jsunnex@gmail.com>
    Date:                     03 Sep 2022, (12:08 PM)

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


class AacEncoder:
    encoders = [
        "aac",
    ]

    def __init__(self, settings):
        self.settings = settings

    @staticmethod
    def options():
        return {
            "aac_encoder_ratecontrol_method": "CBR",
            "aac_constant_quality_scale":     "2",
            "aac_average_bitrate":            "96",
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
        if encoder == "aac":
            return "m4a"
        return ""

    def args(self, stream_id):
        stream_encoding = []

        # Use defaults for basic mode
        if self.settings.get_setting('mode') in ['basic']:
            defaults = self.options()
            stream_encoding += [
                '-qscale:a', str(self.settings.get_setting('aac_constant_quality_scale')),
            ]
            return stream_encoding

        if self.settings.get_setting('aac_encoder_ratecontrol_method') in ['VBR']:
            # Set values for constant quantizer scale
            stream_encoding += [
                '-q:a', str(self.settings.get_setting('aac_constant_quality_scale')),
            ]
        elif self.settings.get_setting('aac_encoder_ratecontrol_method') in ['CBR']:
            # Set values for constant quantizer scale
            stream_encoding += [
                '-b:a', "{}k".format(self.settings.get_setting('aac_average_bitrate')),
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

    def get_aac_encoder_ratecontrol_method_form_settings(self):
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
        self.__set_default_option(values['select_options'], 'aac_encoder_ratecontrol_method', default_option='VBR')
        if self.settings.get_setting('mode') not in ['standard']:
            values["display"] = "hidden"
        return values

    def get_aac_constant_quality_scale_form_settings(self):
        # Lower is better
        values = {
            "label":          "Quality scale",
            "description":    "",
            "sub_setting":    True,
            "input_type":     "slider",
            "slider_options": {
                "min":  0.1,
                "max":  2,
                "step": 0.1,
            },
        }
        if self.settings.get_setting('mode') not in ['basic', 'standard']:
            values["display"] = "hidden"
        if self.settings.get_setting('aac_encoder_ratecontrol_method') not in ['VBR']:
            values["display"] = "hidden"
        if self.settings.get_setting('audio_encoder') in ['aac']:
            values["description"] = "Note: This VBR is experimental and likely to get even worse results than the CBR."
        return values

    def get_aac_average_bitrate_form_settings(self):
        values = {
            "label":          "Bitrate",
            "sub_setting":    True,
            "input_type":     "select",
            "select_options": [
                {
                    "value": "10",
                    "label": "10kbps",
                },
                {
                    "value": "12",
                    "label": "12kbps",
                },
                {
                    "value": "14",
                    "label": "14kbps",
                },
                {
                    "value": "16",
                    "label": "16kbps",
                },
                {
                    "value": "20",
                    "label": "20kbps",
                },
                {
                    "value": "24",
                    "label": "24kbps",
                },
                {
                    "value": "28",
                    "label": "28kbps",
                },
                {
                    "value": "32",
                    "label": "32kbps",
                },
                {
                    "value": "40",
                    "label": "40kbps",
                },
                {
                    "value": "48",
                    "label": "48kbps",
                },
                {
                    "value": "56",
                    "label": "56kbps",
                },
                {
                    "value": "64",
                    "label": "64kbps",
                },
                {
                    "value": "80",
                    "label": "80kbps",
                },
                {
                    "value": "96",
                    "label": "96kbps",
                },
                {
                    "value": "112",
                    "label": "112kbps",
                },
                {
                    "value": "128",
                    "label": "128kbps",
                },
                {
                    "value": "160",
                    "label": "160kbps",
                },
                {
                    "value": "192",
                    "label": "192kbps",
                },
                {
                    "value": "224",
                    "label": "224kbps",
                },
                {
                    "value": "256",
                    "label": "256kbps",
                },
                {
                    "value": "320",
                    "label": "320kbps",
                },
                {
                    "value": "384",
                    "label": "384kbps",
                },
                {
                    "value": "448",
                    "label": "448kbps",
                },
                {
                    "value": "512",
                    "label": "512kbps",
                },
                {
                    "value": "576",
                    "label": "576kbps",
                },
            ]
        }
        if self.settings.get_setting('mode') not in ['standard']:
            values["display"] = "hidden"
        if self.settings.get_setting('aac_encoder_ratecontrol_method') not in ['CBR']:
            values["display"] = "hidden"
        return values
