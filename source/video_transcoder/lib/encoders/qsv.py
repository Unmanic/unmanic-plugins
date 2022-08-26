#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
    plugins.qsv.py

    Written by:               Josh.5 <jsunnex@gmail.com>
    Date:                     08 Jun 2022, (8:14 AM)

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
"""
Notes:
    - Good breakdown on FFmpeg general args for QSV HW accel: 
        https://gist.github.com/jackleaks/776d2de2688d238c95ed7eafb3d5bae8
"""


class QsvEncoder:
    encoders = [
        "h264_qsv",
        "hevc_qsv",
    ]

    def __init__(self, settings):
        self.settings = settings

    @staticmethod
    def options():
        return {
            "preset":                     "slow",
            "tune":                       "film",
            "encoder_ratecontrol_method": "LA_ICQ",
            "constant_quantizer_scale":   "25",
            "constant_quality_scale":     "23",
            "average_bitrate":            "5",
        }

    @staticmethod
    def generate_default_args(settings):
        """
        Generate a list of args for using a QSV decoder

        :param settings:
        :return:
        """
        # Encode only (no decoding)
        #   REF: https://trac.ffmpeg.org/wiki/Hardware/QuickSync#Transcode
        generic_kwargs = {
            "-init_hw_device":   "qsv=hw",
            "-filter_hw_device": "hw",
        }
        advanced_kwargs = {}
        return generic_kwargs, advanced_kwargs

    @staticmethod
    def generate_filtergraphs():
        """
        Generate the required filter for enabling QSV HW acceleration

        :return:
        """
        return ["hwupload=extra_hw_frames=64,format=qsv"]

    def args(self, stream_id):
        stream_encoding = []

        # Use defaults for basic mode
        if self.settings.get_setting('mode') in ['basic']:
            defaults = self.options()
            # Use default LA_ICQ mode
            stream_encoding += [
                '-preset', str(defaults.get('preset')),
                '-global_quality', str(defaults.get('constant_quality_scale')), '-look_ahead', '1',
            ]
            return stream_encoding

        # Add the preset and tune
        if self.settings.get_setting('preset'):
            stream_encoding += ['-preset', str(self.settings.get_setting('preset'))]
        if self.settings.get_setting('tune'):
            stream_encoding += ['-tune', str(self.settings.get_setting('tune'))]

        # TODO: Split this into encoder specific functions
        if self.settings.get_setting('encoder_ratecontrol_method'):
            if self.settings.get_setting('encoder_ratecontrol_method') in ['CQP', 'LA_ICQ', 'ICQ']:
                # Configure QSV encoder with a quality-based mode
                if self.settings.get_setting('encoder_ratecontrol_method') == 'CQP':
                    # Set values for constant quantizer scale
                    stream_encoding += [
                        '-q', str(self.settings.get_setting('constant_quantizer_scale')),
                    ]
                elif self.settings.get_setting('encoder_ratecontrol_method') in ['LA_ICQ', 'ICQ']:
                    # Set the global quality
                    stream_encoding += [
                        '-global_quality', str(self.settings.get_setting('constant_quality_scale')),
                    ]
                    # Set values for constant quality scale
                    if self.settings.get_setting('encoder_ratecontrol_method') == 'LA_ICQ':
                        # Add lookahead
                        stream_encoding += [
                            '-look_ahead', '1',
                        ]
            else:
                # Configure the QSV encoder with a bitrate-based mode
                # Set the max and average bitrate (used by all bitrate-based modes)
                stream_encoding += [
                    '-b:v:{}'.format(stream_id), '{}M'.format(self.settings.get_setting('average_bitrate')),
                ]
                if self.settings.get_setting('encoder_ratecontrol_method') == 'LA':
                    # Add lookahead
                    stream_encoding += [
                        '-look_ahead', '1',
                    ]
                elif self.settings.get_setting('encoder_ratecontrol_method') == 'CBR':
                    # Add 'maxrate' with the same value to make CBR mode
                    stream_encoding += [
                        '-maxrate', '{}M'.format(self.settings.get_setting('average_bitrate')),
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
            "select_options": [
                {
                    "value": "auto",
                    "label": "Disabled – Do not apply any tune",
                },
                {
                    "value": "film",
                    "label": "Film – use for high quality movie content; lowers deblocking",
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
                    "value": "stillimage",
                    "label": "Still image – good for slideshow-like content",
                },
                {
                    "value": "fastdecode",
                    "label": "Fast decode – allows faster decoding by disabling certain filters",
                },
                {
                    "value": "zerolatency",
                    "label": "Zero latency – good for fast encoding and low-latency streaming",
                },
            ],
        }
        self.__set_default_option(values['select_options'], 'tune')
        if self.settings.get_setting('mode') not in ['standard']:
            values["display"] = "hidden"
        return values

    def get_encoder_ratecontrol_method_form_settings(self):
        values = {
            "label":          "Encoder ratecontrol method",
            "sub_setting":    True,
            "input_type":     "select",
            "select_options": [
                {
                    "value": "CQP",
                    "label": "CQP - Quality based mode using constant quantizer scale",
                },
                {
                    "value": "ICQ",
                    "label": "ICQ - Quality based mode using intelligent constant quality",
                },
                {
                    "value": "LA_ICQ",
                    "label": "LA_ICQ - Quality based mode using intelligent constant quality with lookahead",
                },
                {
                    "value": "VBR",
                    "label": "VBR - Bitrate based mode using variable bitrate",
                },
                {
                    "value": "LA",
                    "label": "LA - Bitrate based mode using VBR with lookahead",
                },
                {
                    "value": "CBR",
                    "label": "CBR - Bitrate based mode using constant bitrate",
                },
            ]
        }
        self.__set_default_option(values['select_options'], 'encoder_ratecontrol_method', default_option='LA_ICQ')
        if self.settings.get_setting('mode') not in ['standard']:
            values["display"] = "hidden"
        return values

    def get_constant_quantizer_scale_form_settings(self):
        # Lower is better
        values = {
            "label":          "Constant quantizer scale",
            "sub_setting":    True,
            "input_type":     "slider",
            "slider_options": {
                "min": 0,
                "max": 51,
            },
        }
        if self.settings.get_setting('mode') not in ['standard']:
            values["display"] = "hidden"
        if self.settings.get_setting('encoder_ratecontrol_method') != 'CQP':
            values["display"] = "hidden"
        return values

    def get_constant_quality_scale_form_settings(self):
        # Lower is better
        values = {
            "label":          "Constant quality scale",
            "sub_setting":    True,
            "input_type":     "slider",
            "slider_options": {
                "min": 1,
                "max": 51,
            },
        }
        if self.settings.get_setting('mode') not in ['standard']:
            values["display"] = "hidden"
        if self.settings.get_setting('encoder_ratecontrol_method') not in ['LA_ICQ', 'ICQ']:
            values["display"] = "hidden"
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
