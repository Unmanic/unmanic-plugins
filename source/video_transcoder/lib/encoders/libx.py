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


class LibxEncoder:
    encoders = [
        "libx264",
        "libx265",
    ]

    def __init__(self, settings):
        self.settings = settings

    @staticmethod
    def options():
        return {
            "preset":                     "slow",
            "tune":                       "disabled",
            "profile":                    "auto",
            "encoder_ratecontrol_method": "CRF",
            "constant_quality_scale":     "23",
            "average_bitrate":            "5",
        }

    @staticmethod
    def generate_default_args(settings):
        """
        Generate a list of args for using a libx decoder

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
        No filters are required for libx encoders

        :return:
        """
        return []

    def args(self, stream_id):
        stream_encoding = []

        # Use defaults for basic mode
        if self.settings.get_setting('mode') in ['basic']:
            defaults = self.options()
            stream_encoding += [
                '-preset', str(defaults.get('preset')),
            ]
            # TODO: Calculate best crf based on source bitrate
            default_crf = defaults.get('constant_quality_scale')
            if self.settings.get_setting('video_encoder') in ['libx265']:
                default_crf = 28
            elif self.settings.get_setting('video_encoder') in ['libx264']:
                default_crf = 23
            stream_encoding += ['-crf', str(default_crf)]
            return stream_encoding

        # Add the preset and tune
        if self.settings.get_setting('preset'):
            stream_encoding += ['-preset', str(self.settings.get_setting('preset'))]
        if self.settings.get_setting('tune') and self.settings.get_setting('tune') not in ['auto']:
            stream_encoding += ['-tune', str(self.settings.get_setting('tune'))]
        if self.settings.get_setting('profile') and self.settings.get_setting('profile') not in ['auto']:
            stream_encoding += ['-profile:v', str(self.settings.get_setting('profile'))]

        if self.settings.get_setting('encoder_ratecontrol_method') in ['CRF']:
            # Set values for constant quantizer scale
            stream_encoding += [
                '-crf', str(self.settings.get_setting('constant_quality_scale')),
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

    def get_preset_form_settings(self):
        values = {
            "label":          "Encoder quality preset",
            "sub_setting":    True,
            "input_type":     "select",
            "select_options": [
                {
                    "value": "veryfast",
                    "label": "Very fast - Fastest setting, biggest quality drop",
                },
                {
                    "value": "faster",
                    "label": "Faster - Close to medium/fast quality, faster performance",
                },
                {
                    "value": "fast",
                    "label": "Fast",
                },
                {
                    "value": "medium",
                    "label": "Medium - Balanced performance and quality",
                },
                {
                    "value": "slow",
                    "label": "Slow",
                },
                {
                    "value": "slower",
                    "label": "Slower - Close to 'very slow' quality, faster performance",
                },
                {
                    "value": "veryslow",
                    "label": "Very Slow - Best quality",
                },
            ],
        }
        if self.settings.get_setting('mode') not in ['standard']:
            values["display"] = "hidden"
        return values

    def get_tune_form_settings(self):
        values = {
            "label":          "Tune for a particular type of source or situation",
            "sub_setting":    True,
            "input_type":     "select",
            "select_options": [],
        }
        common_select_options = [
            {
                "value": "auto",
                "label": "Disabled – Do not apply any tune",
            },
            {
                "value": "animation",
                "label": "Animation – good for cartoons; uses higher deblocking and more reference frames",
            },
            {
                "value": "grain",
                "label": "Grain – preserves the grain structure in old, grainy film material",
            },
            {
                "value": "fastdecode",
                "label": "Fast decode – allows faster decoding by disabling certain filters",
            },
            {
                "value": "zerolatency",
                "label": "Zero latency – good for fast encoding and low-latency streaming",
            },
        ]
        if self.settings.get_setting('video_encoder') in ['libx264']:
            values["select_options"] = common_select_options + [
                {
                    "value": "film",
                    "label": "Film – use for high quality movie content; lowers deblocking",
                },
                {
                    "value": "stillimage",
                    "label": "Still image – good for slideshow-like content",
                },
            ]
        elif self.settings.get_setting('video_encoder') in ['libx265']:
            values["select_options"] = common_select_options
        self.__set_default_option(values['select_options'], 'tune')
        if self.settings.get_setting('mode') not in ['standard']:
            values["display"] = "hidden"
        return values

    def get_profile_form_settings(self):
        values = {
            "label":          "Profile for a particular type of source or situation",
            "sub_setting":    True,
            "input_type":     "select",
            "select_options": [],
        }
        if self.settings.get_setting('video_encoder') in ['libx264']:
            values["select_options"] = [
                {
                    "value": "auto",
                    "label": "Auto – Let FFmpeg automatically select the required profile (recommended)",
                },
                {
                    "value": "baseline",
                    "label": "Baseline",
                },
                {
                    "value": "main",
                    "label": "Main",
                },
                {
                    "value": "high",
                    "label": "High",
                },
                {
                    "value": "high10",
                    "label": "High10",
                },
                {
                    "value": "high422",
                    "label": "High422",
                },
                {
                    "value": "high444",
                    "label": "High444",
                },
            ]
        elif self.settings.get_setting('video_encoder') in ['libx265']:
            values["select_options"] = [
                {
                    "value": "auto",
                    "label": "Auto – Let FFmpeg automatically select the required profile (recommended)",
                },
                {
                    "value": "main",
                    "label": "Main",
                },
                {
                    "value": "main-intra",
                    "label": "Main-intra",
                },
                {
                    "value": "mainstillpicture",
                    "label": "Mainstillpicture",
                },
                {
                    "value": "main444-8",
                    "label": "Main444-8",
                },
                {
                    "value": "main444-intra",
                    "label": "Main444-intra",
                },
                {
                    "value": "main444-stillpicture",
                    "label": "Main444-stillpicture",
                },
                {
                    "value": "main10",
                    "label": "Main10",
                },
                {
                    "value": "main10-intra",
                    "label": "Main10-intra",
                },
                {
                    "value": "main422-10",
                    "label": "Main422-10",
                },
                {
                    "value": "main422-10-intra",
                    "label": "Main422-10-intra",
                },
                {
                    "value": "main444-10",
                    "label": "Main444-10",
                },
                {
                    "value": "main444-10-intra",
                    "label": "Main444-10-intra",
                },
                {
                    "value": "main12",
                    "label": "Main12",
                },
                {
                    "value": "main12-intra",
                    "label": "Main12-intra",
                },
                {
                    "value": "main422-12",
                    "label": "Main422-12",
                },
                {
                    "value": "main422-12-intra",
                    "label": "Main422-12-intra",
                },
                {
                    "value": "main444-12",
                    "label": "Main444-12",
                },
                {
                    "value": "main444-12-intra",
                    "label": "Main444-12-intra",
                },
            ]
        # TODO: Enable profile options (currently causing issues)
        values["select_options"] = [
            {
                "value": "auto",
                "label": "Auto – Let FFmpeg automatically select the required profile (recommended)",
            },
        ]
        self.__set_default_option(values['select_options'], 'profile')
        if self.settings.get_setting('mode') not in ['standard']:
            values["display"] = "hidden"
        return values

    def get_encoder_ratecontrol_method_form_settings(self):
        # TODO: Add Two-Pass
        values = {
            "label":          "Encoder ratecontrol method",
            "sub_setting":    True,
            "input_type":     "select",
            "select_options": [
                {
                    "value": "CRF",
                    "label": "CRF - Constant Rate Factor",
                },
            ]
        }
        self.__set_default_option(values['select_options'], 'encoder_ratecontrol_method', default_option='CRF')
        if self.settings.get_setting('mode') not in ['standard']:
            values["display"] = "hidden"
        return values

    def get_constant_quality_scale_form_settings(self):
        # Lower is better
        values = {
            "label":          "Constant rate factor",
            "description":    "",
            "sub_setting":    True,
            "input_type":     "slider",
            "slider_options": {
                "min": 1,
                "max": 51,
            },
        }
        if self.settings.get_setting('mode') not in ['standard']:
            values["display"] = "hidden"
        if self.settings.get_setting('encoder_ratecontrol_method') not in ['CRF']:
            values["display"] = "hidden"
        if self.settings.get_setting('video_encoder') in ['libx264']:
            values["description"] = "Default value for libx264 = 23"
        elif self.settings.get_setting('video_encoder') in ['libx265']:
            values["description"] = "Default value for libx265 = 28 (equivalent to 23 in libx264)"
        return values

    def get_average_bitrate_form_settings(self):
        values = {
            "label":          "Bitrate",
            "sub_setting":    True,
            "input_type":     "slider",
            "slider_options": {
                "min":    1,
                "max":    20,
                "suffix": "M"
            },
        }
        if self.settings.get_setting('mode') not in ['standard']:
            values["display"] = "hidden"
        if self.settings.get_setting('encoder_ratecontrol_method') not in ['VBR', 'LA', 'CBR']:
            values["display"] = "hidden"
        return values
