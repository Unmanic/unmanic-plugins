#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
    plugins.flac.py

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


class FlacEncoder(Encoder):
    def __init__(self, settings=None, probe=None):
        super().__init__(settings=settings, probe=probe)

    def provides(self):
        return {
            "flac": {
                "codec":        "flac",
                "label":        "FLAC",
                "max_channels": 8,
            },
        }

    def options(self):
        return {}

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
        if encoder == "flac":
            return "flac"
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
