#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
    plugins.qsv.py

    Written by:               Josh.5 <jsunnex@gmail.com>
    Date:                     08 Jun 2022, (8:14 AM)

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
"""
Notes:
    - Listing available encoder options:
        ffmpeg -h encoder=h264_qsv
        ffmpeg -h encoder=hevc_qsv
        ffmpeg -h encoder=av1_qsv
    - Good breakdown on FFmpeg general args for QSV HW accel: 
        https://gist.github.com/jackleaks/776d2de2688d238c95ed7eafb3d5bae8
"""

from video_transcoder.lib.encoders.base import Encoder


class QsvEncoder(Encoder):
    def __init__(self, settings=None, probe=None):
        super().__init__(settings=settings, probe=probe)

    def _map_pix_fmt(self, is_h264: bool, is_10bit: bool) -> str:
        if is_10bit and not is_h264:
            return "p010le"
        else:
            return "nv12"

    def provides(self):
        return {
            "h264_qsv": {
                "codec": "h264",
                "label": "QSV - h264_qsv",
            },
            "hevc_qsv": {
                "codec": "hevc",
                "label": "QSV - hevc_qsv",
            },
            "av1_qsv":  {
                "codec": "av1",
                "label": "QSV - av1_qsv",
            },
        }

    def options(self):
        return {
            "qsv_decoding_method":            "cpu",
            "qsv_preset":                     "slow",
            "qsv_encoder_ratecontrol_method": "LA_ICQ",
            "qsv_constant_quantizer_scale":   "25",
            "qsv_constant_quality_scale":     "23",
            "qsv_average_bitrate":            "5",
        }

    def generate_default_args(self):
        """
        Generate a list of args for using a QSV decoder

        :return:
        """
        # Encode only (no decoding)
        #   REF: https://trac.ffmpeg.org/wiki/Hardware/QuickSync#Transcode
        generic_kwargs = {
            "-init_hw_device":   "qsv=qsv0",
            "-filter_hw_device": "qsv0",
        }
        advanced_kwargs = {}
        # Check if we are using a HW accelerated decoder> Modify args as required
        if self.settings.get_setting('qsv_decoding_method') in ['qsv']:
            generic_kwargs.update({
                "-hwaccel":               "qsv",
                "-hwaccel_output_format": "qsv",
            })
        return generic_kwargs, advanced_kwargs

    def generate_filtergraphs(self, current_filter_args, smart_filters, encoder_name):
        """
        Generate the required filter for enabling QSV HW acceleration

        :return:
        """
        generic_kwargs = {}
        advanced_kwargs = {}
        start_filter_args = []
        end_filter_args = []

        # Loop over any HW smart filters to be applied and add them as required.
        hw_smart_filters = []
        remaining_smart_filters = []
        for sf in smart_filters:
            if sf.get("scale"):
                w = sf["scale"]["values"]["width"]
                hw_smart_filters.append(f"scale_qsv=w={w}:h=-1")
            else:
                remaining_smart_filters.append(sf)

        # Check if we are decoding with QSV
        hw_decode = self.settings.get_setting('qsv_decoding_method') in ['qsv']
        # Check software format to use
        target_fmt = self._target_pix_fmt_for_encoder(encoder_name)

        # Handle HDR
        enc_supports_hdr = (encoder_name in ["hevc_qsv"])
        target_color_config = self._target_color_config_for_encoder(encoder_name)

        # If we have SW filters:
        if remaining_smart_filters or current_filter_args:
            # If we have SW filters and HW decode is enabled, make decoder produce SW frames
            if hw_decode:
                # Force decoder to deliver SW frames
                generic_kwargs['-hwaccel_output_format'] = target_fmt

            # Add filter to upload software frames to QSV for QSV filters
            # Note, format conversion (if any - eg yuv422p10le -> p010le) happens after the software filters.
            # If a user applies a custom software filter that does not support the pix_fmt, then will need to prefix it with 'format=p010le'
            # Set format and setparams at start of filter
            start_chain = [f"format={target_fmt}"]
            if enc_supports_hdr and target_color_config.get('apply_color_params'):
                start_chain.append(target_color_config['setparams_filter'])
            start_filter_args.append(",".join(start_chain))
            # Upload to hw frames at the end of the filter
            end_chain = start_chain + ["hwupload=extra_hw_frames=64", "format=qsv", f"vpp_qsv=format={target_fmt}"]
            end_filter_args.append(",".join(end_chain))
        # If we have no software filters:
        else:
            # Check if we are software decoding
            if not hw_decode:
                # Set format and setparams at start of filter
                start_chain = [f"format={target_fmt}"]
                if enc_supports_hdr and target_color_config.get('apply_color_params'):
                    start_chain.append(target_color_config['setparams_filter'])
                start_filter_args.append(",".join(start_chain))
                # Upload to hw frames at the end of the filter
                end_chain = start_chain + ["hwupload=extra_hw_frames=64", "format=qsv", f"vpp_qsv=format={target_fmt}"]
                end_filter_args.append(",".join(end_chain))
            else:
                # Add hwupload filter that can handle when the frame was decoded in software or hardware
                chain = [f"format={target_fmt}|qsv",
                         "hwupload=extra_hw_frames=64",
                         "format=qsv", f"vpp_qsv=format={target_fmt}"]
                end_filter_args.append(",".join(chain))

        # Add the smart filters to the end
        end_filter_args += hw_smart_filters

        # Return built args
        return {
            "generic_kwargs":    generic_kwargs,
            "advanced_kwargs":   advanced_kwargs,
            "smart_filters":     remaining_smart_filters,
            "start_filter_args": start_filter_args,
            "end_filter_args":   end_filter_args,
        }

    def encoder_details(self, encoder):
        provides = self.provides()
        return provides.get(encoder, {})

    def stream_args(self, stream_info, stream_id, encoder_name):
        generic_kwargs = {}
        advanced_kwargs = {}
        encoder_args = []
        stream_args = []

        # Handle HDR
        enc_supports_hdr = (encoder_name in ["hevc_qsv"])
        target_color_config = self._target_color_config_for_encoder(encoder_name)
        if enc_supports_hdr and target_color_config.get('apply_color_params'):
            # Force Main10 profile
            stream_args += [f'-profile:v:{stream_id}', 'main10']

        # Use defaults for basic mode
        if self.settings.get_setting('mode') in ['basic']:
            # Read defaults
            defaults = self.options()

            if enc_supports_hdr and target_color_config.get('apply_color_params'):
                # Add HDR color tags to the encoder output stream
                for k, v in target_color_config.get('stream_color_params', {}).items():
                    stream_args += [k, v]

            # Use default LA_ICQ mode
            encoder_args += [
                '-global_quality', str(defaults.get('qsv_constant_quality_scale')),
                '-look_ahead_depth', '100', '-extbrc', '1',
            ]
            if encoder_name in ["h264_qsv"]:
                encoder_args += ['-look_ahead', '1']
            stream_args += ['-preset', str(defaults.get('qsv_preset')), ]
            return {
                "generic_kwargs":  generic_kwargs,
                "advanced_kwargs": advanced_kwargs,
                "encoder_args":    encoder_args,
                "stream_args":     stream_args,
            }

        # Add the preset and tune
        if self.settings.get_setting('qsv_preset'):
            stream_args += ['-preset', str(self.settings.get_setting('qsv_preset'))]

        if self.settings.get_setting('qsv_encoder_ratecontrol_method'):
            if self.settings.get_setting('qsv_encoder_ratecontrol_method') in ['CQP', 'LA_ICQ', 'ICQ']:
                # Configure QSV encoder with a quality-based mode
                if self.settings.get_setting('qsv_encoder_ratecontrol_method') == 'CQP':
                    # Set values for constant quantizer scale
                    encoder_args += ['-q', str(self.settings.get_setting('qsv_constant_quantizer_scale'))]
                elif self.settings.get_setting('qsv_encoder_ratecontrol_method') in ['LA_ICQ', 'ICQ']:
                    # Set the global quality
                    encoder_args += ['-global_quality', str(self.settings.get_setting('qsv_constant_quality_scale'))]
                    # Set values for constant quality scale
                    if self.settings.get_setting('qsv_encoder_ratecontrol_method') == 'LA_ICQ':
                        # Add lookahead
                        if encoder_name in ["h264_qsv"]:
                            encoder_args += ['-look_ahead', '1']
                        encoder_args += ['-look_ahead_depth', '100', '-extbrc', '1']
            else:
                # Configure the QSV encoder with a bitrate-based mode
                # Set the max and average bitrate (used by all bitrate-based modes)
                encoder_args += [f"-b:v:{stream_id}", f"{self.settings.get_setting('qsv_average_bitrate')}M"]
                if self.settings.get_setting('qsv_encoder_ratecontrol_method') == 'LA':
                    # Add lookahead
                    if encoder_name in ["h264_qsv"]:
                        encoder_args += ['-look_ahead', '1']
                    encoder_args += ['-look_ahead_depth', '100', '-extbrc', '1']
                elif self.settings.get_setting('qsv_encoder_ratecontrol_method') == 'CBR':
                    # Add 'maxrate' with the same value to make CBR mode
                    encoder_args += ['-maxrate', f"{self.settings.get_setting('qsv_average_bitrate')}M"]

        # Add stream color args
        if enc_supports_hdr and target_color_config.get('apply_color_params'):
            # Add HDR color tags to the encoder output stream
            for k, v in target_color_config.get('stream_color_params', {}).items():
                stream_args += [k, v]

        # Return built args
        return {
            "generic_kwargs":  generic_kwargs,
            "advanced_kwargs": advanced_kwargs,
            "encoder_args":    encoder_args,
            "stream_args":     stream_args,
        }

    def __set_default_option(self, select_options, key, default_option=None):
        """
        Sets the default option if the currently set option is not available

        :param select_options:
        :param key:
        :return:
        """
        available_options = []
        for option in select_options:
            available_options.append(option.get('value'))
            if not default_option:
                default_option = option.get('value')
        if self.settings.get_setting(key) not in available_options:
            self.settings.set_setting(key, default_option)

    def get_qsv_decoding_method_form_settings(self):
        values = {
            "label":          "Enable HW Accelerated Decoding",
            "description":    "Warning: Ensure your device supports decoding the source video codec or it will fail.\n"
                              "This enables full hardware transcode with QSV, using only GPU memory for the entire video transcode.\n"
                              "If filters are configured in the plugin, decoder will output NV12 or P010LE software surfaces to\n"
                              "those filters which will be slightly slower.",
            "sub_setting":    True,
            "input_type":     "select",
            "select_options": [
                {
                    "value": "cpu",
                    "label": "Disabled - Use CPU to decode of video source (provides best compatibility)",
                },
                {
                    "value": "qsv",
                    "label": "QSV - Enable QSV decoding",
                }
            ]
        }
        self.__set_default_option(values['select_options'], 'qsv_decoding_method', 'cpu')
        if self.settings.get_setting('mode') not in ['standard']:
            values["display"] = "hidden"
        return values

    def get_qsv_preset_form_settings(self):
        values = {
            "label":          "Encoder quality preset",
            "sub_setting":    True,
            "input_type":     "select",
            "select_options": [
                {
                    "value": "veryfast",
                    "label": "Very fast - Fastest setting, biggest quality drop",
                },
                {
                    "value": "faster",
                    "label": "Faster - Close to medium/fast quality, faster performance",
                },
                {
                    "value": "fast",
                    "label": "Fast",
                },
                {
                    "value": "medium",
                    "label": "Medium - Balanced performance and quality",
                },
                {
                    "value": "slow",
                    "label": "Slow",
                },
                {
                    "value": "slower",
                    "label": "Slower - Close to 'very slow' quality, faster performance",
                },
                {
                    "value": "veryslow",
                    "label": "Very Slow - Best quality",
                },
            ],
        }
        self.__set_default_option(values['select_options'], 'qsv_preset')
        if self.settings.get_setting('mode') not in ['standard']:
            values["display"] = "hidden"
        return values

    def get_qsv_encoder_ratecontrol_method_form_settings(self):
        values = {
            "label":          "Encoder ratecontrol method",
            "sub_setting":    True,
            "input_type":     "select",
            "select_options": []
        }
        values['select_options'] = [
            {
                "value": "CQP",
                "label": "CQP - Quality based mode using constant quantizer scale",
            },
            {
                "value": "ICQ",
                "label": "ICQ - Quality based mode using intelligent constant quality",
            }
        ]
        if self.settings.get_setting('video_encoder') in ['h264_qsv']:
            values['select_options'] += [
                {
                    "value": "LA_ICQ",
                    "label": "LA_ICQ - Quality based mode using intelligent constant quality with lookahead",
                }
            ]
        values['select_options'] += [
            {
                "value": "VBR",
                "label": "VBR - Bitrate based mode using variable bitrate",
            },
        ]
        if self.settings.get_setting('video_encoder') in ['h264_qsv', 'hevc_qsv']:
            values['select_options'] += [
                {
                    "value": "LA",
                    "label": "LA - Bitrate based mode using VBR with lookahead",
                }
            ]
        values['select_options'] += [
            {
                "value": "CBR",
                "label": "CBR - Bitrate based mode using constant bitrate",
            }
        ]
        self.__set_default_option(values['select_options'], 'qsv_encoder_ratecontrol_method', default_option='LA')
        if self.settings.get_setting('mode') not in ['standard']:
            values["display"] = "hidden"
        return values

    def get_qsv_constant_quantizer_scale_form_settings(self):
        # Lower is better
        values = {
            "label":          "Constant quantizer scale",
            "sub_setting":    True,
            "input_type":     "slider",
            "slider_options": {
                "min": 0,
                "max": 51,
            },
        }
        if self.settings.get_setting('mode') not in ['standard']:
            values["display"] = "hidden"
        if self.settings.get_setting('qsv_encoder_ratecontrol_method') != 'CQP':
            values["display"] = "hidden"
        return values

    def get_qsv_constant_quality_scale_form_settings(self):
        # Lower is better
        values = {
            "label":          "Constant quality scale",
            "sub_setting":    True,
            "input_type":     "slider",
            "slider_options": {
                "min": 1,
                "max": 51,
            },
        }
        if self.settings.get_setting('mode') not in ['standard']:
            values["display"] = "hidden"
        if self.settings.get_setting('qsv_encoder_ratecontrol_method') not in ['LA_ICQ', 'ICQ']:
            values["display"] = "hidden"
        return values

    def get_qsv_average_bitrate_form_settings(self):
        values = {
            "label":          "Bitrate",
            "sub_setting":    True,
            "input_type":     "slider",
            "slider_options": {
                "min":    1,
                "max":    20,
                "suffix": "M"
            },
        }
        if self.settings.get_setting('mode') not in ['standard']:
            values["display"] = "hidden"
        if self.settings.get_setting('qsv_encoder_ratecontrol_method') not in ['VBR', 'LA', 'CBR']:
            values["display"] = "hidden"
        return values
