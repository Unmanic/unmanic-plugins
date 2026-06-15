#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
    plugins.opus.py

    Written by:               Josh.5 <jsunnex@gmail.com>
    Date:                     15 June 2026

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


class OpusEncoder(Encoder):
    def __init__(self, settings=None, probe=None):
        super().__init__(settings=settings, probe=probe)

    def provides(self):
        return {
            "libopus": {
                "codec":        "opus",
                "label":        "Opus - libopus",
                "max_channels": 8,
            },
        }

    def options(self):
        return {
            "opus_encoder_ratecontrol_method": "VBR",
            "opus_average_bitrate":            "128",
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
        if encoder == "libopus":
            return "opus"
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

        if self.settings.get_setting('opus_encoder_ratecontrol_method') in ['CBR']:
            stream_args += ['-vbr', 'off']
        elif self.settings.get_setting('opus_encoder_ratecontrol_method') in ['CVBR']:
            stream_args += ['-vbr', 'constrained']
        else:
            stream_args += ['-vbr', 'on']

        stream_args += [
            '-b:a', "{}k".format(self.settings.get_setting('opus_average_bitrate')),
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

    def get_opus_encoder_ratecontrol_method_form_settings(self):
        values = {
            "label":          "Encoder ratecontrol method",
            "sub_setting":    True,
            "input_type":     "select",
            "select_options": [
                {"value": "VBR", "label": "VBR - Variable Bitrate"},
                {"value": "CVBR", "label": "CVBR - Constrained Variable Bitrate"},
                {"value": "CBR", "label": "CBR - Constant Bitrate"},
            ],
        }
        selected_method = self.__set_default_option(
            values['select_options'],
            'opus_encoder_ratecontrol_method',
            default_option='VBR',
        )
        if getattr(self.settings, 'apply_default_fallbacks', True):
            current_value = self.settings.get_setting('opus_encoder_ratecontrol_method')
            if selected_method and selected_method != current_value:
                self.settings.set_setting('opus_encoder_ratecontrol_method', selected_method)
        if self.settings.get_setting('mode') not in ['standard']:
            values["display"] = "hidden"
        return values

    def get_opus_average_bitrate_form_settings(self):
        values = {
            "label":          "Bitrate",
            "sub_setting":    True,
            "input_type":     "select",
            "select_options": [
                {"value": "48", "label": "48kbps"},
                {"value": "64", "label": "64kbps"},
                {"value": "80", "label": "80kbps"},
                {"value": "96", "label": "96kbps"},
                {"value": "112", "label": "112kbps"},
                {"value": "128", "label": "128kbps"},
                {"value": "160", "label": "160kbps"},
                {"value": "192", "label": "192kbps"},
                {"value": "224", "label": "224kbps"},
                {"value": "256", "label": "256kbps"},
                {"value": "320", "label": "320kbps"},
                {"value": "384", "label": "384kbps"},
                {"value": "448", "label": "448kbps"},
                {"value": "512", "label": "512kbps"},
            ],
        }
        if self.settings.get_setting('mode') not in ['standard']:
            values["display"] = "hidden"
        return values
