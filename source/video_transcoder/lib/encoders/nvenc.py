#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
    plugins.nvenc.py

    Written by:               Josh.5 <jsunnex@gmail.com>
    Date:                     27 Dec 2023, (11:21 AM)

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
        ffmpeg -h encoder=h264_nvenc
        ffmpeg -h encoder=hevc_nvenc
"""
import logging
import re
import subprocess

logger = logging.getLogger("Unmanic.Plugin.video_transcoder")


def list_available_cuda_devices():
    """
    Return a list of available cuda decoder devices
    :return:
    """
    gpu_dicts = []
    try:
        # Run the nvidia-smi command
        result = subprocess.check_output(['nvidia-smi', '-L'], encoding='utf-8')
        # Use regular expression to find device IDs, names, and UUIDs
        gpu_info = re.findall(r'GPU (\d+): (.+) \(UUID: (.+)\)', result)
        # Populate the list of dictionaries for each GPU
        for gpu_id, gpu_name, gpu_uuid in gpu_info:
            gpu_dict = {
                'hwaccel_device':      gpu_id,
                'hwaccel_device_name': f"{gpu_name} (UUID: {gpu_uuid})"
            }
            gpu_dicts.append(gpu_dict)
    except FileNotFoundError:
        # nvidia-smi executable not found
        return []
    except subprocess.CalledProcessError:
        # nvidia-smi command failed, likely no NVIDIA GPU present
        return []
    # Return the list of GPUs
    return gpu_dicts


def get_configured_device(settings):
    """
    Returns the currently configured device
    Checks to ensure that the configured device exists and otherwise will return the first device available
    :param settings:
    :return:
    """
    hardware_device = None
    # Set the hardware device
    hardware_devices = list_available_cuda_devices()
    if not hardware_devices:
        # Return no options. No hardware device was found
        raise Exception("No NVIDIA device found")
    # If we have configured a hardware device
    if settings.get_setting('nvenc_device') not in ['none']:
        # Attempt to match to that configured hardware device
        for hw_device in hardware_devices:
            if settings.get_setting('nvenc_device') == hw_device.get('hwaccel_device'):
                hardware_device = hw_device
                break
    # If no matching hardware device is set, then select the first one
    if not hardware_device:
        hardware_device = hardware_devices[0]
    return hardware_device


class NvencEncoder:

    def __init__(self, settings):
        self.settings = settings

    def provides(self):
        return {
            "h264_nvenc": {
                "codec": "h264",
                "label": "NVENC - h264_nvenc",
            },
            "hevc_nvenc": {
                "codec": "hevc",
                "label": "NVENC - hevc_nvenc",
            },
        }

    def options(self):
        return {
            "nvenc_device":                        "none",
            "nvenc_decoding_method":               "cpu",
            "nvenc_preset":                        "p4",
            "nvenc_tune":                          "auto",
            "nvenc_profile":                       "main",
            "nvenc_encoder_ratecontrol_method":    "auto",
            "nvenc_encoder_ratecontrol_lookahead": 0,
            "nvenc_enable_spatial_aq":             False,
            "nvenc_enable_temporal_aq":            False,
            "nvenc_aq_strength":                   8,
        }

    def generate_default_args(self):
        """
        Generate a list of args for using a NVENC decoder

        REF: https://trac.ffmpeg.org/wiki/HWAccelIntro#NVDECCUVID

        :return:
        """
        hardware_device = get_configured_device(self.settings)

        generic_kwargs = {}
        advanced_kwargs = {}
        # Check if we are using a HW accelerated decoder also
        if self.settings.get_setting('nvenc_decoding_method') in ['cuda', 'nvdec', 'cuvid']:
            generic_kwargs = {
                "-hwaccel_device":   hardware_device.get('hwaccel_device'),
                "-hwaccel":          self.settings.get_setting('nvenc_decoding_method'),
                "-init_hw_device":   "cuda=hw",
                "-filter_hw_device": "hw",
            }
            if self.settings.get_setting('nvenc_decoding_method') in ['cuda', 'nvdec']:
                generic_kwargs["-hwaccel_output_format"] = "cuda"
        return generic_kwargs, advanced_kwargs

    def generate_filtergraphs(self, software_filters, hw_smart_filters):
        """
        Generate the required filter for enabling NVENC HW acceleration

        :return:
        """
        filters = []
        if software_filters:
            # Software filters mean the decoder was outputting nv12 surfaces. We need to upload back to cuda first
            filters.append('hwupload_cuda')
        for smart_filter in hw_smart_filters:
            if smart_filter.get('scale'):
                scale_values = smart_filter.get('scale')
                filters.append('scale_cuda={}:-1'.format(scale_values[0]))
        return filters

    def encoder_details(self, encoder):
        hardware_devices = list_available_cuda_devices()
        if not hardware_devices:
            # Return no options. No hardware device was found
            return {}
        provides = self.provides()
        return provides.get(encoder, {})

    def args(self, stream_info, stream_id):
        generic_kwargs = {}
        stream_encoding = []

        # Specify the GPU to use for encoding
        hardware_device = get_configured_device(self.settings)
        stream_encoding += ['-gpu', str(hardware_device.get('hwaccel_device', '0'))]

        # Use defaults for basic mode
        if self.settings.get_setting('mode') in ['basic']:
            defaults = self.options()
            stream_encoding += [
                '-preset', str(defaults.get('nvenc_preset')),
                '-profile:v:{}'.format(stream_id), str(defaults.get('nvenc_profile')),
            ]
            # TODO: Parse stream info to optimise these settings based on resolution, HDR, etc.
            return generic_kwargs, stream_encoding

        # Add the preset and tune
        if self.settings.get_setting('nvenc_preset'):
            stream_encoding += ['-preset', str(self.settings.get_setting('nvenc_preset'))]
        if self.settings.get_setting('nvenc_tune') and self.settings.get_setting('nvenc_tune') != 'auto':
            stream_encoding += ['-tune', str(self.settings.get_setting('nvenc_tune'))]
        if self.settings.get_setting('nvenc_profile') and self.settings.get_setting('nvenc_profile') != 'auto':
            stream_encoding += ['-profile:v:{}'.format(stream_id), str(self.settings.get_setting('nvenc_profile'))]

        # Apply rate control config
        if self.settings.get_setting('nvenc_encoder_ratecontrol_method') in ['constqp', 'vbr', 'cbr']:
            # Set the rate control method
            stream_encoding += [
                '-rc:v:{}'.format(stream_id), str(self.settings.get_setting('nvenc_encoder_ratecontrol_method'))
            ]
        if self.settings.get_setting('nvenc_encoder_ratecontrol_lookahead'):
            # Set the rate control lookahead frames
            stream_encoding += [
                '-rc-lookahead:v:{}'.format(stream_id), str(self.settings.get_setting('nvenc_encoder_ratecontrol_lookahead'))
            ]

        # Apply adaptive quantization
        if self.settings.get_setting('nvenc_enable_spatial_aq'):
            stream_encoding += ['-spatial-aq', '1']
        if self.settings.get_setting('nvenc_enable_spatial_aq') or self.settings.get_setting('nvenc_enable_temporal_aq'):
            stream_encoding += ['-aq-strength:v:{}'.format(stream_id), str(self.settings.get_setting('nvenc_aq_strength'))]
        if self.settings.get_setting('nvenc_enable_temporal_aq'):
            stream_encoding += ['-temporal-aq', '1']

        # If CUVID is enabled, return generic_kwargs
        if self.settings.get_setting('nvenc_decoding_method') in ['cuvid']:
            generic_kwargs = {
                '-c:v:{}'.format(stream_id): '{}_cuvid'.format(stream_info.get('codec_name', 'unknown_codec_name')),
            }

        return generic_kwargs, stream_encoding

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

    def get_nvenc_device_form_settings(self):
        values = {
            "label":          "NVIDIA Device",
            "sub_setting":    True,
            "input_type":     "select",
            "select_options": [
                {
                    "value": "none",
                    "label": "No NVIDIA devices available",
                }
            ]
        }
        default_option = None
        hardware_devices = list_available_cuda_devices()
        if hardware_devices:
            values['select_options'] = []
            for hw_device in hardware_devices:
                if not default_option:
                    default_option = hw_device.get('hwaccel_device', 'none')
                values['select_options'].append({
                    "value": hw_device.get('hwaccel_device', 'none'),
                    "label": "NVIDIA device '{}'".format(hw_device.get('hwaccel_device_name', 'not found')),
                })
        if not default_option:
            default_option = 'none'

        self.__set_default_option(values['select_options'], 'nvenc_device', default_option=default_option)
        if self.settings.get_setting('mode') not in ['standard']:
            values["display"] = "hidden"
        return values

    def get_nvenc_decoding_method_form_settings(self):
        values = {
            "label":          "Enable HW Decoding",
            "description":    "Warning: Ensure your device supports decoding the source video codec or it will fail.\n"
                              "This enables full hardware transcode with NVDEC and NVENC, using only GPU memory for the entire video transcode.\n"
                              "If filters are configured in the plugin, decoder will output NV12 software surfaces which are slightly slower.\n"
                              "Note: It is recommended that you disable this option for 10-bit encodes.",
            "sub_setting":    True,
            "input_type":     "select",
            "select_options": [
                {
                    "value": "cpu",
                    "label": "Disabled - Use CPU to decode of video source (provides best compatibility)",
                },
                {
                    "value": "cuda",
                    "label": "NVDEC/CUDA - Use the GPUs HW decoding the video source and upload surfaces to CUDA (recommended)",
                },
                {
                    "value": "cuvid",
                    "label": "CUVID - Older interface for HW video decoding. Kepler or older hardware may perform better with this option",
                }
            ]
        }
        if self.settings.get_setting('mode') not in ['standard']:
            values["display"] = "hidden"
        return values

    def get_nvenc_preset_form_settings(self):
        values = {
            "label":          "Encoder quality preset",
            "sub_setting":    True,
            "input_type":     "select",
            "select_options": [
                {
                    "value": "p1",
                    "label": "Fastest (P1)",
                },
                {
                    "value": "p2",
                    "label": "Faster (P2)",
                },
                {
                    "value": "p3",
                    "label": "Fast (P3)",
                },
                {
                    "value": "p4",
                    "label": "Medium (P4) - Balanced performance and quality",
                },
                {
                    "value": "p5",
                    "label": "Slow (P5)",
                },
                {
                    "value": "p6",
                    "label": "Slower (P6)",
                },
                {
                    "value": "p7",
                    "label": "Slowest (P7)",
                },
            ],
        }
        self.__set_default_option(values['select_options'], 'nvenc_preset', default_option='p4')
        if self.settings.get_setting('mode') not in ['standard']:
            values["display"] = "hidden"
        return values

    def get_nvenc_tune_form_settings(self):
        values = {
            "label":          "Tune for a particular type of source or situation",
            "sub_setting":    True,
            "input_type":     "select",
            "select_options": [
                {
                    "value": "auto",
                    "label": "Disabled – Do not apply any tune",
                },
                {
                    "value": "hq",
                    "label": "HQ – High quality (ffmpeg default)",
                },
                {
                    "value": "ll",
                    "label": "LL – Low latency",
                },
                {
                    "value": "ull",
                    "label": "ULL – Ultra low latency",
                },
                {
                    "value": "lossless",
                    "label": "Lossless",
                },
            ],
        }
        self.__set_default_option(values['select_options'], 'nvenc_tune', default_option='auto')
        if self.settings.get_setting('mode') not in ['standard']:
            values["display"] = "hidden"
        return values

    def get_nvenc_profile_form_settings(self):
        values = {
            "label":          "Profile",
            "description":    "The profile determines which features of the codec are available and enabled,\n"
                              "while also affecting other restrictions.\n"
                              "Any of these profiles are capable of 4:2:0, 4:2:2 and 4:4:4, however the support\n"
                              "depends on the installed hardware.",
            "sub_setting":    True,
            "input_type":     "select",
            "select_options": [
                {
                    "value": "auto",
                    "label": "Auto – Let ffmpeg automatically select the required profile (recommended)",
                },
                {
                    "value": "baseline",
                    "label": "Baseline",
                },
                {
                    "value": "main",
                    "label": "Main",
                },
                {
                    "value": "main10",
                    "label": "Main10",
                },
                {
                    "value": "high444p",
                    "label": "High444p",
                },
            ],
        }
        self.__set_default_option(values['select_options'], 'nvenc_profile', default_option='main')
        if self.settings.get_setting('mode') not in ['standard']:
            values["display"] = "hidden"
        return values

    def get_nvenc_encoder_ratecontrol_method_form_settings(self):
        values = {
            "label":          "Encoder ratecontrol method",
            "description":    "Note that the rate control is already defined in the Encoder Quality Preset option.\n"
                              "Selecting anything other than 'Disabled' will override the preset rate-control.",
            "sub_setting":    True,
            "input_type":     "select",
            "select_options": [
                {
                    "value": "auto",
                    "label": "Auto – Use the rate control setting pre-defined in the preset option (recommended)",
                },
                {
                    "value": "constqp",
                    "label": "CQP - Quality based mode using constant quantizer scale",
                },
                {
                    "value": "vbr",
                    "label": "VBR - Bitrate based mode using variable bitrate",
                },
                {
                    "value": "cbr",
                    "label": "CBR - Bitrate based mode using constant bitrate",
                },
            ]
        }
        self.__set_default_option(values['select_options'], 'nvenc_encoder_ratecontrol_method', default_option='auto')
        if self.settings.get_setting('mode') not in ['standard']:
            values["display"] = "hidden"
        return values

    def get_nvenc_encoder_ratecontrol_lookahead_form_settings(self):
        # Lower is better
        values = {
            "label":          "Configure the number of frames to look ahead for rate-control",
            "sub_setting":    True,
            "input_type":     "slider",
            "slider_options": {
                "min": 0,
                "max": 30,
            },
        }
        if self.settings.get_setting('mode') not in ['standard']:
            values["display"] = "hidden"
        return values

    def get_nvenc_enable_spatial_aq_form_settings(self):
        values = {
            "label":       "Enable Spatial Adaptive Quantization",
            "description": "This adjusts the quantization parameter within each frame based on spatial complexity.\n"
                           "This helps in improving the quality of areas within a frame that are more detailed or complex.",
            "sub_setting": True,
        }
        if self.settings.get_setting('mode') not in ['standard']:
            values["display"] = 'hidden'
        return values

    def get_nvenc_enable_temporal_aq_form_settings(self):
        values = {
            "label":       "Enable Temporal Adaptive Quantization",
            "description": "This adjusts the quantization parameter across frames, based on the motion and temporal complexity.\n"
                           "This is particularly effective in scenes with varying levels of motion, enhancing quality where it's most needed.",
            "sub_setting": True,
        }
        if self.settings.get_setting('mode') not in ['standard']:
            values["display"] = 'hidden'
        return values

    def get_nvenc_aq_strength_form_settings(self):
        # Lower is better
        values = {
            "label":          "Strength of the adaptive quantization",
            "description":    "Controls the strength of the adaptive quantization (both spatial and temporal).\n"
                              "A higher value indicates stronger adaptation, which can lead to better preservation\n"
                              "of detail but might also increase the bitrate.",
            "sub_setting":    True,
            "input_type":     "slider",
            "slider_options": {
                "min": 0,
                "max": 15,
            },
        }
        if self.settings.get_setting('mode') not in ['standard']:
            values["display"] = "hidden"
        if not self.settings.get_setting('nvenc_enable_spatial_aq'):
            values["display"] = "hidden"
        return values
