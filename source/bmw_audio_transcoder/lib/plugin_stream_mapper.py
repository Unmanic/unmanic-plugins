#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
    plugins.plugin_stream_mapper.py

    Written by:               Josh.5 <jsunnex@gmail.com>
    Date:                     04 Jun 2022, (5:43 PM)

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
import logging
import os

from audio_transcoder.lib.encoders.aac import AacEncoder
from audio_transcoder.lib.encoders.lame import LameEncoder
from audio_transcoder.lib.ffmpeg import StreamMapper

logger = logging.getLogger("Unmanic.Plugin.audio_transcoder")


class PluginStreamMapper(StreamMapper):
    def __init__(self):
        super(PluginStreamMapper, self).__init__(logger, ['audio'])
        self.abspath = None
        self.settings = None
        self.complex_audio_filters = {}
        self.crop_value = None
        self.forced_encode = False

    @staticmethod
    def get_encoders(settings):
        """
        Return a dictionary of encoders and their controller classes
        :return:
        """
        return {
            "libmp3lame": LameEncoder(settings),
            "aac":        AacEncoder(settings),
        }

    def set_default_values(self, settings, abspath, probe):
        """
        Configure the stream mapper with defaults

        :param settings:
        :param abspath:
        :param probe:
        :return:
        """
        self.abspath = abspath
        # Set the file probe data
        self.set_probe(probe)
        # Set the input file
        self.set_input_file(abspath)
        # Configure settings
        self.settings = settings

        # Set default Advanced options
        self.advanced_options = [
            '-strict', '-2',
        ]

        # Build default options of advanced mode
        if self.settings.get_setting('mode') == 'advanced':
            # If any main options are provided, overwrite them
            main_options = settings.get_setting('main_options').split()
            if main_options:
                # Overwrite all main options
                self.main_options = main_options
            advanced_options = settings.get_setting('advanced_options').split()
            if advanced_options:
                # Overwrite all advanced options
                self.advanced_options = advanced_options
            # Don't apply any other settings
            return

        # Build default options of standard mode
        if self.settings.get_setting('mode') == 'standard':
            # No standard mode defaults yet exist
            pass

        # Build encoder specific args based on configured encoder
        # Note: these are not applied to advanced mode - advanced mode was returned above
        encoder = self.get_encoders(self.settings).get(self.settings.get_setting('audio_encoder'))
        generic_kwargs, advanced_kwargs = encoder.generate_default_args(self.settings)
        self.set_ffmpeg_generic_options(**generic_kwargs)
        self.set_ffmpeg_advanced_options(**advanced_kwargs)

    def test_stream_needs_processing(self, stream_info: dict):
        """
        Tests if the command will need to transcode the audio stream
            - Return false if the stream should just be copied
            - Return true to transcode this stream (configured by the 'custom_stream_mapping' method)

        :param stream_info:
        :return:
        """
        # If the stream is an audio, add a final check if the codec is already the correct format
        #   (Ignore checks if force transcode is set)
        if stream_info.get('codec_type', '').lower() in ['audio'] and stream_info.get(
                'codec_name').lower() == self.settings.get_setting('audio_codec'):
            if not self.settings.get_setting('force_transcode'):
                return False
            else:
                self.forced_encode = True

        # All other streams should be custom mapped
        return True

    def custom_stream_mapping(self, stream_info: dict, stream_id: int):
        """
        Generate the custom stream mapping and encoding args for the given stream based on the configured settings

        :param stream_info:
        :param stream_id:
        :return:
        """
        codec_type = stream_info.get('codec_type', '').lower()
        stream_specifier = '{}:{}'.format(self.stream_type_idents.get(codec_type), stream_id)
        map_identifier = '0:{}'.format(stream_specifier)
        if self.settings.get_setting('mode') == 'advanced':
            stream_encoding = ['-c:{}'.format(stream_specifier)]
            stream_encoding += self.settings.get_setting('custom_options').split()
        else:
            stream_encoding = [
                '-c:{}'.format(stream_specifier), self.settings.get_setting('audio_encoder'),
            ]

            # Add encoder args
            encoder = self.get_encoders(self.settings).get(self.settings.get_setting('audio_encoder'))
            stream_encoding += encoder.args(stream_id)

        return {
            'stream_mapping':  ['-map', map_identifier],
            'stream_encoding': stream_encoding,
        }

    def set_output_file(self, path):
        """
        Set the output file for the FFmpeg args based on the configured codec

        :param path:
        :return:
        """
        # Get the container extension
        encoder = self.get_encoders(self.settings).get(self.settings.get_setting('audio_encoder'))
        container_extension = encoder.get_output_file_extension(self.settings.get_setting('audio_encoder'))
        # Remove the extension from the current file out path and replace with the encoder extension
        split_file_out = os.path.splitext(path)
        new_file_out = "{}.{}".format(split_file_out[0], container_extension)
        # Set the output file path
        self.output_file = os.path.abspath(new_file_out)
        # Return the output file path
        return self.output_file
