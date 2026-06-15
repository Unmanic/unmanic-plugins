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
from audio_transcoder.lib.encoders.base import Encoder
from audio_transcoder.lib.smart_audio_bitrate import SmartAudioBitrateHelper


class LameEncoder(Encoder):
    def __init__(self, settings=None, probe=None):
        super().__init__(settings=settings, probe=probe)

    def provides(self):
        return {
            "libmp3lame": {
                "codec":        "mp3",
                "label":        "LAME - libmp3lame",
                "max_channels": 2,
            },
        }

    def options(self):
        return {
            "encoder_ratecontrol_method": "VBR",
            "constant_quality_scale":     "4",
            "average_bitrate":            "192",
        }

    def generate_default_args(self):
        return {}, {}

    def generate_filtergraphs(self, current_filter_args, smart_filters, encoder_name):
        return {
            "generic_kwargs":    {},
            "advanced_kwargs":   {},
            "smart_filters":     smart_filters,
            "start_filter_args": [],
            "end_filter_args":   [],
        }

    def get_output_file_extension(self, encoder):
        if encoder == "libmp3lame":
            return "mp3"
        return ""

    def stream_args(self, stream_info, stream_id, encoder_name, filter_state=None):
        generic_kwargs = {}
        advanced_kwargs = {}
        encoder_args = []
        stream_args = []
        target_channels = None
        if filter_state:
            try:
                target_channels = int(filter_state.get('target_channels'))
            except (TypeError, ValueError):
                target_channels = None

        if self.settings.get_setting('mode') in ['basic']:
            if self.settings.get_setting('enable_smart_output_target') and self.probe:
                helper = SmartAudioBitrateHelper(self.probe)
                recommendation = helper.recommend_params(
                    stream_info,
                    self.settings.get_setting('audio_codec'),
                    encoder_name,
                    self.settings.get_setting('smart_output_target'),
                    target_channels=target_channels,
                )
                target_kbps = recommendation.get('recommended_target_kbps')
                if target_kbps:
                    stream_args += [
                        '-b:a', "{}k".format(target_kbps),
                    ]
                    if target_channels:
                        stream_args += [
                            '-ac:a:{}'.format(stream_id), str(target_channels),
                        ]
                    return {
                        "generic_kwargs":  generic_kwargs,
                        "advanced_kwargs": advanced_kwargs,
                        "encoder_args":    encoder_args,
                        "stream_args":     stream_args,
                    }

            stream_args += [
                '-q:a', str(self.settings.get_setting('constant_quality_scale')),
            ]
            if target_channels:
                stream_args += [
                    '-ac:a:{}'.format(stream_id), str(target_channels),
                ]
            return {
                "generic_kwargs":  generic_kwargs,
                "advanced_kwargs": advanced_kwargs,
                "encoder_args":    encoder_args,
                "stream_args":     stream_args,
            }

        if self.settings.get_setting('encoder_ratecontrol_method') in ['VBR']:
            stream_args += [
                '-q:a', str(self.settings.get_setting('constant_quality_scale')),
            ]
        elif self.settings.get_setting('encoder_ratecontrol_method') in ['CBR']:
            stream_args += [
                '-b:a', "{}k".format(self.settings.get_setting('average_bitrate')),
            ]

        if target_channels:
            stream_args += [
                '-ac:a:{}'.format(stream_id), str(target_channels),
            ]

        return {
            "generic_kwargs":  generic_kwargs,
            "advanced_kwargs": advanced_kwargs,
            "encoder_args":    encoder_args,
            "stream_args":     stream_args,
        }

    def __set_default_option(self, select_options, key, default_option=None):
        available_options = []
        for option in select_options:
            available_options.append(option.get('value'))
            if not default_option:
                default_option = option.get('value')
        current_value = self.settings.get_setting(key)
        if not getattr(self.settings, 'apply_default_fallbacks', True):
            return current_value
        if current_value not in available_options:
            self.settings.settings_configured[key] = default_option
            return default_option
        return current_value

    def get_encoder_ratecontrol_method_form_settings(self):
        values = {
            "label":          "Encoder ratecontrol method",
            "sub_setting":    True,
            "input_type":     "select",
            "select_options": [],
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
        selected_method = self.__set_default_option(
            values['select_options'],
            'encoder_ratecontrol_method',
            default_option='VBR',
        )
        if getattr(self.settings, 'apply_default_fallbacks', True):
            current_value = self.settings.get_setting('encoder_ratecontrol_method')
            if selected_method and selected_method != current_value:
                self.settings.set_setting('encoder_ratecontrol_method', selected_method)
        if self.settings.get_setting('mode') not in ['standard']:
            values["display"] = "hidden"
        return values

    def get_constant_quality_scale_form_settings(self):
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
                {"value": "8", "label": "8Kbit/s"},
                {"value": "16", "label": "16Kbit/s"},
                {"value": "24", "label": "24Kbit/s"},
                {"value": "32", "label": "32Kbit/s"},
                {"value": "40", "label": "40Kbit/s"},
                {"value": "48", "label": "48Kbit/s"},
                {"value": "64", "label": "64Kbit/s"},
                {"value": "80", "label": "80Kbit/s"},
                {"value": "96", "label": "96Kbit/s"},
                {"value": "112", "label": "112Kbit/s"},
                {"value": "128", "label": "128Kbit/s"},
                {"value": "160", "label": "160Kbit/s"},
                {"value": "192", "label": "192Kbit/s"},
                {"value": "224", "label": "224Kbit/s"},
                {"value": "256", "label": "256Kbit/s"},
                {"value": "320", "label": "320Kbit/s"},
            ],
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
