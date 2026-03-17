#!/usr/bin/env python3
# -*- coding: utf-8 -*-

class OpusEncoder:
    encoders = [
        "libopus",
    ]

    def __init__(self, settings):
        self.settings = settings

    @staticmethod
    def options():
        return {
            "opus_encoder_ratecontrol_method": "VBR",
            "opus_average_bitrate":            "128",
        }

    @staticmethod
    def generate_default_args(settings):
        return {}, {}

    @staticmethod
    def generate_filtergraphs():
        return []

    @staticmethod
    def get_output_file_extension(encoder):
        if encoder == "libopus":
            return "opus"
        return ""

    def args(self, stream_id):
        stream_encoding = []

        if self.settings.get_setting('mode') in ['basic']:
            return stream_encoding

        if self.settings.get_setting('opus_encoder_ratecontrol_method') in ['VBR']:
            stream_encoding += [
                '-vbr', 'on',
            ]
        elif self.settings.get_setting('opus_encoder_ratecontrol_method') in ['CBR']:
            stream_encoding += [
                '-vbr', 'off',
            ]

        stream_encoding += [
            '-b:a', "{}k".format(self.settings.get_setting('opus_average_bitrate')),
        ]

        return stream_encoding

    def __set_default_option(self, select_options, key, default_option=None):
        available_options = []
        for option in select_options:
            available_options.append(option.get('value'))
            if not default_option:
                default_option = option.get('value')
        if self.settings.get_setting(key) not in available_options:
            self.settings.set_setting(key, default_option)

    def get_opus_encoder_ratecontrol_method_form_settings(self):
        values = {
            "label":          "Encoder ratecontrol method",
            "sub_setting":    True,
            "input_type":     "select",
            "select_options": [
                {
                    "value": "VBR",
                    "label": "VBR - Variable Bitrate",
                },
                {
                    "value": "CBR",
                    "label": "CBR - Constant Bitrate",
                },
            ]
        }
        self.__set_default_option(values['select_options'], 'opus_encoder_ratecontrol_method', default_option='VBR')
        if self.settings.get_setting('mode') not in ['standard']:
            values["display"] = "hidden"
        return values

    def get_opus_average_bitrate_form_settings(self):
        values = {
            "label":          "Bitrate",
            "sub_setting":    True,
            "input_type":     "select",
            "select_options": [
                {
                    "value": "32",
                    "label": "32Kbit/s",
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
                    "value": "96",
                    "label": "96Kbit/s",
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
                    "value": "256",
                    "label": "256Kbit/s",
                },
                {
                    "value": "320",
                    "label": "320Kbit/s",
                },
            ]
        }
        self.__set_default_option(values['select_options'], 'opus_average_bitrate', default_option='128')
        if self.settings.get_setting('mode') not in ['standard']:
            values["display"] = "hidden"
        return values