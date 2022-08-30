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

from video_transcoder.lib import tools
from video_transcoder.lib.encoders import vaapi
from video_transcoder.lib.encoders.libx import LibxEncoder
from video_transcoder.lib.encoders.qsv import QsvEncoder
from video_transcoder.lib.encoders.vaapi import VaapiEncoder
from video_transcoder.lib.ffmpeg import StreamMapper

# Configure plugin logger
logger = logging.getLogger("Unmanic.Plugin.video_transcoder")


class PluginStreamMapper(StreamMapper):
    def __init__(self):
        super(PluginStreamMapper, self).__init__(logger, ['video', 'data', 'attachment'])
        self.abspath = None
        self.settings = None
        self.complex_video_filters = {}
        self.crop_value = None
        self.vaapi_encoders = ['hevc_vaapi', 'h264_vaapi']
        self.forced_encode = False

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

            # Set max muxing queue size
            if self.settings.get_setting('max_muxing_queue_size'):
                advanced_kwargs = {
                    '-max_muxing_queue_size': str(self.settings.get_setting('max_muxing_queue_size'))
                }
                self.set_ffmpeg_advanced_options(**advanced_kwargs)

            # Check for config specific settings
            if self.settings.get_setting('apply_smart_filters'):
                if self.settings.get_setting('autocrop_black_bars'):
                    # Test if the file has black bars
                    self.crop_value = tools.detect_plack_bars(abspath, probe.get_probe())

        # Build hardware acceleration args based on encoder
        # Note: these are not applied to advanced mode - advanced mode was returned above
        if self.settings.get_setting('video_encoder') in LibxEncoder.encoders:
            generic_kwargs, advanced_kwargs = LibxEncoder.generate_default_args(self.settings)
            self.set_ffmpeg_generic_options(**generic_kwargs)
            self.set_ffmpeg_advanced_options(**advanced_kwargs)
        elif self.settings.get_setting('video_encoder') in QsvEncoder.encoders:
            generic_kwargs, advanced_kwargs = QsvEncoder.generate_default_args(self.settings)
            self.set_ffmpeg_generic_options(**generic_kwargs)
            self.set_ffmpeg_advanced_options(**advanced_kwargs)
        elif self.settings.get_setting('video_encoder') in self.vaapi_encoders:
            generic_kwargs, advanced_kwargs = VaapiEncoder.generate_default_args(self.settings)
            self.set_ffmpeg_generic_options(**generic_kwargs)
            self.set_ffmpeg_advanced_options(**advanced_kwargs)
            # TODO: Disable any options not compatible with this encoder
        # TODO: Add NVENC args

    def scale_resolution(self, stream_info: dict):
        def get_test_resolution(settings):
            target_resolution = settings.get_setting('target_resolution')
            # Set the target resolution
            custom_resolutions = settings.get_setting('custom_resolutions')
            test_resolution = {
                'width':  tools.resolution_map.get(target_resolution, {}).get('width'),
                'height': tools.resolution_map.get(target_resolution, {}).get('height'),
            }
            if custom_resolutions:
                test_resolution = {
                    'width':  settings.get_setting('{}_width'.format(target_resolution)),
                    'height': settings.get_setting('{}_height'.format(target_resolution)),
                }
            return test_resolution

        # Only run if target resolution is set
        if self.settings.get_setting('target_resolution') in ['source']:
            return None, None

        # Get video width and height
        vid_width = stream_info.get('width', stream_info.get('coded_width', 0))
        vid_height = stream_info.get('height', stream_info.get('coded_height', 0))

        # Get the test resolution
        test_resolution = get_test_resolution(self.settings)

        # Check if the streams resolution is greater than the test resolution
        if int(vid_width) > int(test_resolution['width']) or int(vid_height) > int(test_resolution['height']):
            return test_resolution['width'], test_resolution['height']

        # Return none (nothing will be done)
        return None, None

    def build_filter_chain(self, stream_info, stream_id):
        """
        Builds a complex video filtergraph for the provided stream

        :param stream_info:
        :param stream_id:
        :return:
        """
        # TODO: Check for supported hardware filters
        filter_id = '0:v:{}'.format(stream_id)
        software_filters = []
        hardware_filters = []

        # Apply smart filters first
        if self.settings.get_setting('apply_smart_filters'):
            if self.settings.get_setting('autocrop_black_bars') and self.crop_value:
                software_filters.append('crop={}'.format(self.crop_value))
            if self.settings.get_setting('target_resolution') not in ['source']:
                vid_width, vid_height = self.scale_resolution(stream_info)
                # TODO: ignore this if hardware encoding is enabled and the hardware has the ability to perform
                #  the scaling filter
                if vid_width:
                    # Apply scale with only width to keep aspect ratio
                    software_filters.append('scale={}:-1'.format(vid_width))

        # Apply custom software filters
        if self.settings.get_setting('apply_custom_filters'):
            for software_filter in self.settings.get_setting('custom_software_filters').splitlines():
                if software_filter.strip():
                    software_filters.append(software_filter.strip())

        # Check for hardware encoders that required video filters
        if self.settings.get_setting('video_encoder') in QsvEncoder.encoders:
            # Add filtergraph required for using QSV encoding
            hardware_filters += QsvEncoder.generate_filtergraphs()
        elif self.settings.get_setting('video_encoder') in self.vaapi_encoders:
            # Add filtergraph required for using VAAPI encoding
            hardware_filters += VaapiEncoder.generate_filtergraphs()
            # If we are using software filters, then disable vaapi surfaces.
            # Instead, putput software frames
            if software_filters:
                self.set_ffmpeg_generic_options(**{'-hwaccel_output_format': 'nv12'})

        # TODO: Add HW scaling filter if available (disable software filter above)

        # Return here if there are no filters to apply
        if not software_filters and not hardware_filters:
            return None, None

        # Join filtergraph
        filtergraph = ''
        count = 1
        for filter in software_filters:
            # If we are appending to existing filters, separate by a semicolon to start a new chain
            if filtergraph:
                filtergraph += ';'
            # Add the input for this filter
            filtergraph += '[{}]'.format(filter_id)
            # Add filtergraph
            filtergraph += '{}'.format(filter)
            # Update filter ID and add it to the end
            filter_id = '0:vf:{}-{}'.format(stream_id, count)
            filtergraph += '[{}]'.format(filter_id)
            # Increment filter ID counter
            count += 1
        for filter in hardware_filters:
            # If we are appending to existing filters, separate by a semicolon to start a new chain
            if filtergraph:
                filtergraph += ';'
            # Add the input for this filter
            filtergraph += '[{}]'.format(filter_id)
            # Add filtergraph
            filtergraph += '{}'.format(filter)
            # Update filter ID and add it to the end
            filter_id = '0:vf:{}-{}'.format(stream_id, count)
            filtergraph += '[{}]'.format(filter_id)
            # Increment filter ID counter
            count += 1

        return filter_id, filtergraph

    def test_stream_needs_processing(self, stream_info: dict):
        """
        Tests if the command will need to transcode the video stream
            - Return false if the stream should just be copied
            - Return true to transcode this stream (configured by the 'custom_stream_mapping' method)

        :param stream_info:
        :return:
        """
        # If force transcode is enabled, then process everything regardless of the current codec
        # Ignore image video streams (will just copy them)
        if stream_info.get('codec_name').lower() in tools.image_video_codecs:
            return False

        # Check if video filters need to be applied (build_filter_chain)
        if self.settings.get_setting('apply_smart_filters'):
            # Video filters
            if stream_info.get('codec_type', '').lower() in ['video']:
                # Check if autocrop filter needs to be applied
                if self.settings.get_setting('autocrop_black_bars') and self.crop_value:
                    return True
                # Check if scale filter needs to be applied
                if self.settings.get_setting('target_resolution') not in ['source']:
                    vid_width, vid_height = self.scale_resolution(stream_info)
                    if vid_width:
                        return True
            # Data/Attachment filters
            if stream_info.get('codec_type', '').lower() in ['data', 'attachment']:
                # Enable removal of data and attachment streams
                if self.settings.get_setting('remove_data_and_attachment_streams'):
                    # Remove it
                    return True

        # If the stream is a video, add a final check if the codec is already the correct format
        #   (Ignore checks if force transcode is set)
        if stream_info.get('codec_type', '').lower() in ['video'] and stream_info.get(
                'codec_name').lower() == self.settings.get_setting('video_codec'):
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
        ident = {
            'video':      'v',
            'audio':      'a',
            'subtitle':   's',
            'data':       'd',
            'attachment': 't'
        }
        codec_type = stream_info.get('codec_type', '').lower()
        stream_specifier = '{}:{}'.format(ident.get(codec_type), stream_id)
        map_identifier = '0:{}'.format(stream_specifier)
        if stream_info.get('codec_type', '').lower() in ['video']:
            if self.settings.get_setting('mode') == 'advanced':
                stream_encoding = ['-c:{}'.format(stream_specifier)]
                stream_encoding += self.settings.get_setting('custom_options').split()
            else:
                # Build complex filter
                filter_id, filter_complex = self.build_filter_chain(stream_info, stream_id)
                if filter_complex:
                    map_identifier = '[{}]'.format(filter_id)
                    self.set_ffmpeg_advanced_options(**{"-filter_complex": filter_complex})

                stream_encoding = [
                    '-c:{}'.format(stream_specifier), self.settings.get_setting('video_encoder'),
                ]

                # Add encoder args
                if self.settings.get_setting('video_encoder') in LibxEncoder.encoders:
                    qsv_encoder = LibxEncoder(self.settings)
                    stream_encoding += qsv_encoder.args(stream_id)
                elif self.settings.get_setting('video_encoder') in QsvEncoder.encoders:
                    qsv_encoder = QsvEncoder(self.settings)
                    stream_encoding += qsv_encoder.args(stream_id)
                elif self.settings.get_setting('video_encoder') in VaapiEncoder.encoders:
                    vaapi_encoder = VaapiEncoder(self.settings)
                    stream_encoding += vaapi_encoder.args(stream_id)
        elif stream_info.get('codec_type', '').lower() in ['data']:
            if not self.settings.get_setting('apply_smart_filters'):
                # If smart filters are not enabled, return 'False' to let the default mapping just copy the data stream
                return False
            # Remove if settings configured to do so, strip the data stream
            if self.settings.get_setting('strip_data_streams'):
                return {
                    'stream_mapping':  [],
                    'stream_encoding': [],
                }
            # Resort to returning 'False' to let the default mapping just copy the data stream
            return False
        elif stream_info.get('codec_type', '').lower() in ['attachment']:
            if not self.settings.get_setting('apply_smart_filters'):
                # If smart filters are not enabled, return 'False' to let the default mapping just copy the attachment
                #   stream
                return False
            # Remove if settings configured to do so, strip the attachment stream
            if self.settings.get_setting('strip_attachment_streams'):
                return {
                    'stream_mapping':  [],
                    'stream_encoding': [],
                }
            # Resort to returning 'False' to let the default mapping just copy the attachment stream
            return False
        else:
            raise Exception("Unsupported codec type {}".format())

        return {
            'stream_mapping':  ['-map', map_identifier],
            'stream_encoding': stream_encoding,
        }
