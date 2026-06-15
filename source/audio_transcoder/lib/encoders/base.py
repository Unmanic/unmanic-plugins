#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
    plugins.base.py

    Written by:               Josh.5 <jsunnex@gmail.com>
    Date:                     14 June 2026

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


class Encoder:
    def __init__(self, settings=None, probe=None):
        self.settings = settings
        self.probe = probe

    def provides(self):
        raise NotImplementedError("This method must be implemented by a child class.")

    def options(self):
        raise NotImplementedError("This method must be implemented by a child class.")

    def generate_default_args(self):
        raise NotImplementedError("This method must be implemented by a child class.")

    def generate_filtergraphs(self, current_filter_args, smart_filters, encoder_name):
        raise NotImplementedError("This method must be implemented by a child class.")

    def stream_args(self, stream_info, stream_id, encoder_name, filter_state=None):
        raise NotImplementedError("This method must be implemented by a child class.")

    def encoder_details(self, encoder):
        return self.provides().get(encoder, {})

    def get_output_file_extension(self, encoder):
        raise NotImplementedError("This method must be implemented by a child class.")
