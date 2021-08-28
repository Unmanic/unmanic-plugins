#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
    unmanic.stream_mapper.py

    Written by:               Josh.5 <jsunnex@gmail.com>
    Date:                     30 Jul 2021, (9:41 AM)

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
from logging import Logger

from .probe import Probe


class StreamMapper(object):
    probe: Probe = None

    processing_stream_type = ''
    found_streams_to_encode = False
    stream_mapping = []
    stream_encoding = []
    video_stream_count = 0
    audio_stream_count = 0
    subtitle_stream_count = 0

    def __init__(self, logger: Logger, processing_stream_type: str):
        self.logger = logger
        if processing_stream_type is not None:
            if not processing_stream_type in ['video', 'audio', 'subtitle']:
                raise Exception("processing_stream_type must be either 'video', 'audio' or 'subtitle'")
            self.processing_stream_type = processing_stream_type

    def __copy_stream_mapping(self, codec_type, stream_id):
        # Map this stream for copy to the destination file
        self.stream_mapping += ['-map', '0:{}:{}'.format(codec_type, stream_id)]
        # Add a encoding flag copying this stream
        self.stream_encoding += ['-c:{}:{}'.format(codec_type, stream_id), 'copy']

    def __apply_custom_stream_mapping(self, mapping_dict):
        # Ensure the mapping dictionary provided is correct
        if not isinstance(mapping_dict, dict):
            raise Exception("processing_stream_type must return a dictionary")
        if not mapping_dict.get('stream_mapping'):
            raise Exception("processing_stream_type return dictionary must contain 'stream_mapping' key")
        if not isinstance(mapping_dict.get('stream_mapping'), list):
            raise Exception("processing_stream_type 'stream_mapping' value must be of type 'list'")
        if not mapping_dict.get('stream_encoding'):
            raise Exception("processing_stream_type return dictionary must contain 'stream_encoding' key")
        if not isinstance(mapping_dict.get('stream_encoding'), list):
            raise Exception("processing_stream_type 'stream_mapping' value must be of type 'list'")
        # Append this custom stream mapping
        self.stream_mapping += mapping_dict.get('stream_mapping')
        # Append these custom encoding flags
        self.stream_encoding += mapping_dict.get('stream_encoding')

    def set_probe(self, probe: Probe):
        self.probe = probe

    def test_stream_needs_processing(self, stream_info: dict):
        """
        Overwrite this function to test a stream.
        Return 'True' if it needs to be process.
        Return 'False' if it should just be copied over to the new file

        :param stream_info:
        :return: bool
        """
        raise NotImplementedError

    def custom_stream_mapping(self, stream_info: dict, stream_id: int):
        """
        Configure custom mapping for a single stream
        This function must return a dictionary containing 2 key values:
            {
                'stream_mapping': [],
                'stream_encoding': [],
            }

        :param stream_info:
        :param stream_id:
        :return: dict
        """
        raise NotImplementedError

    def __set_stream_mapping(self):
        """
        Sets a list of stream maps and encoding variables

        :return:
        """

        # Require a list of probe streams to continue
        file_probe_streams = self.probe.get('streams')
        if not file_probe_streams:
            return False

        # What type of streams are we looking for ('video', 'audio' or 'subtitle')
        processing_stream_type = self.processing_stream_type

        # Map the streams into two arrays that will be placed together in the correct order.
        self.stream_mapping = []
        self.stream_encoding = []

        # Count streams by type
        self.video_stream_count = 0
        self.audio_stream_count = 0
        self.subtitle_stream_count = 0

        # Set flag for finding a stream that needs to be processed as False by default.
        found_streams_to_process = False

        # Loop over all streams found in the file probe
        for stream_info in file_probe_streams:
            # Fore each of these streams:

            # If this is a video/image stream?
            if stream_info.get('codec_type').lower() == "video":
                # Map the video stream
                if processing_stream_type == "video":
                    if not self.test_stream_needs_processing(stream_info):
                        self.__copy_stream_mapping('v', self.video_stream_count)
                        self.video_stream_count += 1
                        continue
                    else:
                        found_streams_to_process = True
                        self.__apply_custom_stream_mapping(
                            self.custom_stream_mapping(stream_info, self.video_stream_count)
                        )
                        self.video_stream_count += 1
                        continue
                else:
                    self.__copy_stream_mapping('v', self.video_stream_count)
                    self.video_stream_count += 1
                    continue

            # If this is a audio stream?
            if stream_info.get('codec_type').lower() == "audio":
                # Map the audio stream
                if processing_stream_type == "audio":
                    if not self.test_stream_needs_processing(stream_info):
                        self.__copy_stream_mapping('a', self.audio_stream_count)
                        self.audio_stream_count += 1
                        continue
                    else:
                        found_streams_to_process = True
                        self.__apply_custom_stream_mapping(
                            self.custom_stream_mapping(stream_info, self.audio_stream_count)
                        )
                        self.audio_stream_count += 1
                        continue
                else:
                    self.__copy_stream_mapping('a', self.audio_stream_count)
                    self.audio_stream_count += 1
                    continue

            # If this is a subtitle stream?
            if stream_info.get('codec_type').lower() == "subtitle":
                # Map the subtitle stream
                if processing_stream_type == "subtitle":
                    if not self.test_stream_needs_processing(stream_info):
                        self.__copy_stream_mapping('s', self.subtitle_stream_count)
                        self.subtitle_stream_count += 1
                        continue
                    else:
                        found_streams_to_process = True
                        self.__apply_custom_stream_mapping(
                            self.custom_stream_mapping(stream_info, self.subtitle_stream_count)
                        )
                        self.subtitle_stream_count += 1
                        continue
                else:
                    self.__copy_stream_mapping('s', self.subtitle_stream_count)
                    self.subtitle_stream_count += 1
                    continue

        return found_streams_to_process

    def streams_need_processing(self):
        return self.__set_stream_mapping()

    def get_stream_mapping(self):
        if not self.stream_mapping:
            self.__set_stream_mapping()
        return self.stream_mapping

    def get_stream_encoding(self):
        if not self.stream_encoding:
            self.__set_stream_mapping()
        return self.stream_encoding
