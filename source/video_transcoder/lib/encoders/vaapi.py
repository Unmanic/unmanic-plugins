#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
    plugins.vaapi.py

    Written by:               Josh.5 <jsunnex@gmail.com>
    Date:                     08 Jun 2022, (8:15 AM)

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
import os


def list_available_vaapi_devices():
    """
    Return a list of available VAAPI decoder devices
    :return:
    """
    decoders = []
    dir_path = os.path.join("/", "dev", "dri")

    if os.path.exists(dir_path):
        for device in sorted(os.listdir(dir_path)):
            if device.startswith('render'):
                device_data = {
                    'hwaccel':             'vaapi',
                    'hwaccel_device':      device,
                    'hwaccel_device_path': os.path.join("/", "dev", "dri", device),
                }
                decoders.append(device_data)

    # Return the list of decoders
    return decoders


class VaapiEncoder:
    encoders = [
        "h264_vaapi",
        "hevc_vaapi",
    ]

    def __init__(self, settings):
        self.settings = settings

    @staticmethod
    def options():
        return {
            "encoder_ratecontrol_method": "ICQ",
            "constant_quantizer_scale":   "25",
            "constant_quality_scale":     "23",
            "average_bitrate":            "5",
            "vaapi_device":               "none",
            "enabled_hw_decoding":        True,
        }

    @staticmethod
    def generate_default_args(settings):
        """
        Generate a list of args for using a VAAPI decoder

        :param settings:
        :return:
        """
        # Set the hardware device
        hardware_devices = list_available_vaapi_devices()
        if not hardware_devices:
            # Return no options. No hardware device was found
            raise Exception("No VAAPI device found")

        hardware_device = None
        # If we have configured a hardware device
        if settings.get_setting('vaapi_device') not in ['none']:
            # Attempt to match to that configured hardware device
            for hw_device in hardware_devices:
                if settings.get_setting('vaapi_device') == hw_device.get('hwaccel_device'):
                    hardware_device = hw_device
                    break
        # If no matching hardware device is set, then select the first one
        if not hardware_device:
            hardware_device = hardware_devices[0]

        # Check if we are using a VAAPI encoder also...
        if settings.get_setting('enabled_hw_decoding'):
            # Set a named global device that can be used with various params
            dev_id = 'vaapi0'
            # Configure args such that when the input may or may not be able to be decoded with hardware we can do:
            #   REF: https://trac.ffmpeg.org/wiki/Hardware/VAAPI#Encoding
            generic_kwargs = {
                "-init_hw_device":        "vaapi={}:{}".format(dev_id, hardware_device.get('hwaccel_device_path')),
                "-hwaccel":               "vaapi",
                "-hwaccel_output_format": "vaapi",
                "-hwaccel_device":        dev_id,
            }
            advanced_kwargs = {
                "-filter_hw_device": dev_id,
            }
        else:
            # Encode only (no decoding)
            #   REF: https://trac.ffmpeg.org/wiki/Hardware/VAAPI#Encode-only (sorta)
            generic_kwargs = {
                "-vaapi_device": hardware_device.get('hwaccel_device_path'),
            }
            advanced_kwargs = {}

        return generic_kwargs, advanced_kwargs

    @staticmethod
    def generate_filtergraphs():
        """
        Generate the required filter for enabling VAAPI HW acceleration

        :return:
        """
        return ["format=nv12|vaapi,hwupload"]

    def args(self, stream_id):
        stream_encoding = []

        # Use defaults for basic mode
        if self.settings.get_setting('mode') == 'basic':
            # Use the default VAAPI settings - Choose the mode automatically based on driver support
            return stream_encoding

        stream_encoding += [
            '-rc_mode', str(self.settings.get_setting('encoder_ratecontrol_method')),
        ]
        if self.settings.get_setting('encoder_ratecontrol_method') in ['CQP', 'ICQ']:
            if self.settings.get_setting('encoder_ratecontrol_method') in ['CQP']:
                stream_encoding += [
                    '-q', str(self.settings.get_setting('constant_quantizer_scale')),
                ]
            elif self.settings.get_setting('encoder_ratecontrol_method') in ['ICQ']:
                stream_encoding += [
                    '-global_quality', str(self.settings.get_setting('constant_quality_scale')),
                ]
        else:
            # Configure the encoder with a bitrate-based mode
            # Set the max and average bitrate (used by all bitrate-based modes)
            stream_encoding += [
                '-b:v:{}'.format(stream_id), '{}M'.format(self.settings.get_setting('average_bitrate')),
            ]
            if self.settings.get_setting('encoder_ratecontrol_method') == 'CBR':
                # Add 'maxrate' with the same value to make CBR mode
                stream_encoding += [
                    '-maxrate', '{}M'.format(self.settings.get_setting('average_bitrate')),
                ]
        return stream_encoding

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

    def get_vaapi_device_form_settings(self):
        values = {
            "label":          "VAAPI Device",
            "sub_setting":    True,
            "input_type":     "select",
            "select_options": [
                {
                    "value": "none",
                    "label": "No VAAPI devices available",
                }
            ]
        }
        default_option = None
        hardware_devices = list_available_vaapi_devices()
        if hardware_devices:
            values['select_options'] = []
            for hw_device in hardware_devices:
                if not default_option:
                    default_option = hw_device.get('hwaccel_device', 'none')
                values['select_options'].append({
                    "value": hw_device.get('hwaccel_device', 'none'),
                    "label": "VAAPI device '{}'".format(hw_device.get('hwaccel_device_path', 'not found')),
                })
        if not default_option:
            default_option = 'none'

        self.__set_default_option(values['select_options'], 'vaapi_device', default_option=default_option)
        if self.settings.get_setting('mode') not in ['standard']:
            values["display"] = "hidden"
        return values

    def get_enabled_hw_decoding_form_settings(self):
        values = {
            "label":       "Enable HW Decoding",
            "sub_setting": True,
            "description": "Will fallback to software decoding and hardware encoding when the input is not be hardware decodable.",
        }
        if self.settings.get_setting('mode') not in ['standard']:
            values["display"] = "hidden"
        return values

    def get_encoder_ratecontrol_method_form_settings(self):
        values = {
            "label":          "Encoder ratecontrol method",
            "sub_setting":    True,
            "input_type":     "select",
            "select_options": [
                {
                    "value": "CQP",
                    "label": "CQP - Quality based mode using constant quantizer scale",
                },
                {
                    "value": "ICQ",
                    "label": "ICQ - Quality based mode using intelligent constant quality",
                },
                {
                    "value": "CBR",
                    "label": "CBR - Bitrate based mode using constant bitrate",
                },
                {
                    "value": "VBR",
                    "label": "VBR - Bitrate based mode using variable bitrate",
                },
            ]
        }
        # TODO: Add support for these:
        # {
        #     "value": "QVBR",
        #     "label": "QVBR - Quality defined variable bitrate mode",
        # },
        # {
        #     "value": "AVBR",
        #     "label": "AVBR - Average variable bitrate mode",
        # },
        self.__set_default_option(values['select_options'], 'encoder_ratecontrol_method', default_option='CQP')
        if self.settings.get_setting('mode') not in ['standard']:
            values["display"] = "hidden"
        return values

    def get_constant_quantizer_scale_form_settings(self):
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
        if self.settings.get_setting('encoder_ratecontrol_method') != 'CQP':
            values["display"] = "hidden"
        return values

    def get_constant_quality_scale_form_settings(self):
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
        if self.settings.get_setting('encoder_ratecontrol_method') not in ['LA_ICQ', 'ICQ']:
            values["display"] = "hidden"
        return values

    def get_average_bitrate_form_settings(self):
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
        if self.settings.get_setting('encoder_ratecontrol_method') not in ['VBR', 'LA', 'CBR']:
            values["display"] = "hidden"
        return values
