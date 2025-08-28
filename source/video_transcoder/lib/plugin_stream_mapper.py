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
from video_transcoder.lib.encoders.libx import LibxEncoder
from video_transcoder.lib.encoders.qsv import QsvEncoder
from video_transcoder.lib.encoders.vaapi import VaapiEncoder
from video_transcoder.lib.encoders.nvenc import NvencEncoder
from video_transcoder.lib.encoders.libsvtav1 import LibsvtAv1Encoder
from video_transcoder.lib.ffmpeg import Probe, StreamMapper

# Configure plugin logger
logger = logging.getLogger("Unmanic.Plugin.video_transcoder")


class PluginStreamMapper(StreamMapper):
    def __init__(self):
        super(PluginStreamMapper, self).__init__(logger, ['video', 'data', 'attachment'])
        self.abspath = None
        self.settings = None
        self.complex_video_filters = {}
        self.crop_value = None
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
                    self.crop_value = tools.detect_black_bars(abspath, probe.get_probe(), self.settings)

        # Build hardware acceleration args based on encoder
        # Note: these are not applied to advanced mode - advanced mode was returned above
        encoder_name = self.settings.get_setting('video_encoder')
        encoder_lib = tools.available_encoders(settings=self.settings).get(encoder_name)
        if encoder_lib:
            generic_kwargs, advanced_kwargs = encoder_lib.generate_default_args()
            self.set_ffmpeg_generic_options(**generic_kwargs)
            self.set_ffmpeg_advanced_options(**advanced_kwargs)

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
        software_filters = []
        hardware_filters = []
        filter_args = []

        # Get configured encoder name
        encoder_name = self.settings.get_setting('video_encoder')

        # Load encoder classes
        libx_encoder = LibxEncoder(self.settings, self.probe)
        stva1_encoder = LibsvtAv1Encoder(self.settings, self.probe)
        qsv_encoder = QsvEncoder(self.settings, self.probe)
        vaapi_encoder = VaapiEncoder(self.settings, self.probe)
        nvenc_encoder = NvencEncoder(self.settings, self.probe)

        # HW accelerated encoder libs
        hw_encoder_libs = [qsv_encoder, vaapi_encoder, nvenc_encoder]
        hw_encoder = next((lib for lib in hw_encoder_libs if encoder_name in lib.provides()), None)

        # All available encoder libs
        all_encoder_libs = [libx_encoder, qsv_encoder, vaapi_encoder, nvenc_encoder, stva1_encoder]
        active_encoder = next((lib for lib in all_encoder_libs if encoder_name in lib.provides()), None)

        # Apply smart filters first
        smart_filters = []
        if self.settings.get_setting('apply_smart_filters'):
            # NOTE: Crop must come first. Filters like scale will ruin the crop values
            if self.settings.get_setting('autocrop_black_bars') and self.crop_value:
                # Note: There is no good way to crop with HW filters at this time. For now, lets leave this as a SW filter.
                filter_args.append(f"crop={self.crop_value}")
            if self.settings.get_setting('target_resolution') not in ['source']:
                vid_width, vid_height = self.scale_resolution(stream_info)
                if vid_height:
                    # Apply scale with only width to keep aspect ratio.
                    # NOTE: Use width since this may follow the black bar crop which will likely crop
                    # height not width changing the aspect ratio.
                    smart_filters.append({
                        "scale": {
                            "filter": f"scale={vid_width}:-1",
                            "values": {"width": vid_width, "height": vid_height}
                        },
                    })

        # Apply custom filtergraph logic from encoder libraries
        filtergraph_config = {}
        if active_encoder:
            filtergraph_config = active_encoder.generate_filtergraphs(
                filter_args,
                smart_filters,
                encoder_name
            )

        # Set un-changed smart-filters (hw overrides will have removed them)
        smart_filters = filtergraph_config.get('smart_filters', smart_filters)
        for smart_filter in smart_filters:
            for filter_type, filter_data in smart_filter.items():
                filter_args.append(filter_data.get('filter'))

        # Apply custom software filters
        if self.settings.get_setting('apply_custom_filters'):
            for software_filter in self.settings.get_setting('custom_software_filters').splitlines():
                if software_filter.strip():
                    filter_args.append(software_filter.strip())

        generic_kwargs = filtergraph_config.get('generic_kwargs', {})
        self.set_ffmpeg_generic_options(**generic_kwargs)

        advanced_kwargs = filtergraph_config.get('advanced_kwargs', {})
        self.set_ffmpeg_advanced_options(**advanced_kwargs)

        start_filter_args = filtergraph_config.get('start_filter_args', [])
        end_filter_args = filtergraph_config.get('end_filter_args', [])
        filter_args = start_filter_args + filter_args + end_filter_args

        # Return here if there are no filters to apply
        if not filter_args:
            return None, None

        # Join filtergraph
        filter_id = '0:v:{}'.format(stream_id)
        filter_id, filtergraph = tools.join_filtergraph(filter_id, filter_args, stream_id)

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
        if stream_info.get('codec_name', '').lower() in tools.image_video_codecs:
            return False

        # Check if video filters need to be applied (build_filter_chain)
        codec_type = stream_info.get('codec_type', '').lower()
        codec_name = stream_info.get('codec_name', '').lower()
        if self.settings.get_setting('apply_smart_filters'):
            # Video filters
            if codec_type in ['video']:
                if self.settings.get_setting('mode') == 'standard':
                    # Check if autocrop filter needs to be applied (standard mode only)
                    if self.settings.get_setting('autocrop_black_bars') and self.crop_value:
                        return True
                    # Check if scale filter needs to be applied (standard mode only)
                    if self.settings.get_setting('target_resolution') not in ['source']:
                        vid_width, vid_height = self.scale_resolution(stream_info)
                        if vid_width:
                            return True
            # Data/Attachment filters
            if codec_type in ['data', 'attachment']:
                # Enable removal of data and attachment streams
                if self.settings.get_setting('remove_data_and_attachment_streams'):
                    # Remove it
                    return True

        # If the stream is a video, add a final check if the codec is already the correct format
        #   (Ignore checks if force transcode is set)
        if codec_type in ['video'] and codec_name == self.settings.get_setting('video_codec'):
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

        # Get configured encoder name
        encoder_name = self.settings.get_setting('video_encoder')

        if codec_type in ['video']:
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
                    '-c:{}'.format(stream_specifier), encoder_name,
                ]

                # Load encoder classes
                libx_encoder = LibxEncoder(self.settings, self.probe)
                stva1_encoder = LibsvtAv1Encoder(self.settings, self.probe)
                qsv_encoder = QsvEncoder(self.settings, self.probe)
                vaapi_encoder = VaapiEncoder(self.settings, self.probe)
                nvenc_encoder = NvencEncoder(self.settings, self.probe)

                # Add encoder args
                if encoder_name in libx_encoder.provides():
                    stream_args = libx_encoder.stream_args(stream_info, stream_id, encoder_name)
                    stream_encoding += stream_args.get("encoder_args", [])
                    stream_encoding += stream_args.get("stream_args", [])
                elif encoder_name in stva1_encoder.provides():
                    stream_args = vaapi_encoder.stream_args(stream_info, stream_id, encoder_name)
                    stream_encoding += stream_args.get("encoder_args", [])
                    stream_encoding += stream_args.get("stream_args", [])
                elif encoder_name in qsv_encoder.provides():
                    stream_args = qsv_encoder.stream_args(stream_info, stream_id, encoder_name)
                    stream_encoding += stream_args.get("encoder_args", [])
                    stream_encoding += stream_args.get("stream_args", [])
                elif encoder_name in vaapi_encoder.provides():
                    stream_args = vaapi_encoder.stream_args(stream_info, stream_id, encoder_name)
                    stream_encoding += stream_args.get("encoder_args", [])
                    stream_encoding += stream_args.get("stream_args", [])
                elif encoder_name in nvenc_encoder.provides():
                    stream_args = nvenc_encoder.stream_args(stream_info, stream_id, encoder_name)
                    stream_encoding += stream_args.get("encoder_args", [])
                    stream_encoding += stream_args.get("stream_args", [])
                    self.set_ffmpeg_generic_options(**stream_args.get("generic_kwargs", {}))

        elif codec_type in ['data']:
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
        elif codec_type in ['attachment']:
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
