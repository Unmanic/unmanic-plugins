#!/usr/bin/env python3
# -*- coding: utf-8 -*-

class FlacEncoder:
    encoders = [
        "flac",
    ]

    def __init__(self, settings):
        self.settings = settings

    @staticmethod
    def options():
        return {
            "flac_compression_level": "5",
        }

    @staticmethod
    def generate_default_args(settings):
        return {}, {}

    @staticmethod
    def generate_filtergraphs():
        return []

    @staticmethod
    def get_output_file_extension(encoder):
        if encoder == "flac":
            return "flac"
        return ""

    def args(self, stream_id):
        stream_encoding = []

        if self.settings.get_setting('mode') in ['basic']:
            return stream_encoding

        stream_encoding += [
            '-compression_level', str(self.settings.get_setting('flac_compression_level')),
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

    def get_flac_compression_level_form_settings(self):
        values = {
            "label":          "FLAC Compression Level",
            "description":    "0 is fastest, least compression. 12 is slowest, most compression. Default is 5.",
            "sub_setting":    True,
            "input_type":     "slider",
            "slider_options": {
                "min": 0,
                "max": 12,
            },
        }
        if self.settings.get_setting('mode') not in ['standard']:
            values["display"] = "hidden"
        return values