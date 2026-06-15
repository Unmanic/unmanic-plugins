#!/usr/bin/env python3
# -*- coding:utf-8 -*-

"""
    plugins.global_settings.py

    Written by:               Josh.5 <jsunnex@gmail.com>
    Date:                     10 Jun 2022, (6:52 PM)

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

from audio_transcoder.lib import tools

supported_codecs = {
    "aac": {
        "label": "AAC",
        "max_channels": 8,
        "warning": "Although FFmpeg's native AAC encoder can produce multichannel AAC up to 7.1, 7.1 AAC is a poor choice for home-theater movie audio and should generally be avoided.<br>"
        "In practice, 8-channel AAC can be unstable across channel layouts, FFmpeg mapping can be error-prone, and consumer playback chains often handle multichannel AAC poorly over HDMI.<br>"
        "Even 5.1 AAC for movies can be a compromise.<br>"
        "These are FFmpeg/codec/playback ecosystem limitations, not an arbitrary plugin restriction.",
    },
    "flac": {
        "label": "FLAC",
        "max_channels": 8,
        "warning": "FLAC supports multichannel lossless output up to 7.1 with FFmpeg's FLAC encoder.<br>"
        "However, container and playback support is much narrower than AAC or AC3.<br>"
        "FLAC is a good fit for MKV and dedicated audio workflows, but it is a poor fit for many MP4/MOV/TS-style media workflows.",
    },
    "opus": {
        "label": "Opus",
        "max_channels": 8,
        "warning": "Opus supports multichannel output up to 7.1 with FFmpeg's libopus encoder.<br>"
        "However, container and device compatibility is much narrower than AAC or AC3.<br>"
        "Opus is best suited to MKV/WebM and modern playback environments, and is a poor fit for many traditional home-theater container workflows.",
    },
    "ac3": {
        "label": "AC3 (Dolby Digital)",
        "max_channels": 6,
        "warning": "FFmpeg's AC3 encoder is limited to 5.1.<br>"
        "Selecting AC3 will cap the maximum output channel count at 5.1.<br>"
        "This is an FFmpeg/encoder limitation, not an arbitrary plugin restriction.",
    },
    "eac3": {
        "label": "EAC3 (Dolby Digital Plus)",
        "max_channels": 6,
        "warning": "FFmpeg's EAC3 encoder is limited to 5.1 in this build.<br>"
        "Selecting EAC3 will cap the maximum output channel count at 5.1.<br>"
        "This is an FFmpeg/encoder limitation, not an arbitrary plugin restriction.",
    },
    "mp3": {
        "label": "MP3",
        "max_channels": 2,
        "warning": "FFmpeg's MP3 encoding path should be treated as stereo-only here.<br>"
        "Using MP3 on multichannel movie audio will downmix channels and is likely to be a poor fit for video libraries.<br>"
        "This comes from codec/encoder limitations, not a plugin-only rule.",
    },
}


class GlobalSettings:
    def __init__(self, settings):
        self.settings = settings

    @staticmethod
    def options():
        return {
            "main_options": {
                "mode": "basic",
                "minimum_input_channel_count": "any",
            },
            "encoder_selection": {
                "audio_codec": "aac",
                "audio_codec_admonition": "",
                "force_transcode": False,
                "audio_encoder": "aac",
            },
            "advanced_input_options": {
                "main_options": "",
                "advanced_options": "",
                "custom_options": "aac\n-b:a 192k\n",
            },
            "output_settings": {},
            "filter_settings": {
                "enable_smart_audio_filters": False,
                "max_channel_count": "same_as_source",
                "normalize_audio_volume": False,
                "apply_custom_filters": False,
                "custom_audio_filters": "",
            },
            "smart_output_target": {
                "enable_smart_output_target": True,
                "smart_output_target": "balanced",
                "reencode_matching_codecs_above_target": False,
            },
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
            available_options.append(option.get("value"))
            if not default_option:
                default_option = option.get("value")
        current_value = self.settings.get_setting(key)
        if not getattr(self.settings, "apply_default_fallbacks", True):
            return current_value
        if current_value not in available_options:
            self.settings.settings_configured[key] = default_option
            return default_option
        return current_value

    def __selected_codec_details(self):
        selected_codec = self.settings.get_setting("audio_codec")
        return supported_codecs.get(selected_codec, {})

    def get_mode_form_settings(self):
        return {
            "label": "Config mode",
            "input_type": "select",
            "select_options": [
                {
                    "value": "basic",
                    "label": "Basic (Not sure what I am doing. Configure most of it for me.)",
                },
                {
                    "value": "standard",
                    "label": "Standard (I know how to transcode some audio. Let me tweak some settings.)",
                },
                {
                    "value": "advanced",
                    "label": "Advanced (Dont tell me what to do, I write FFmpeg commands in my sleep.)",
                },
            ],
        }

    def get_minimum_input_channel_count_form_settings(self):
        values = {
            "label": "Only process streams with at least this many channels",
            "description": "Use this to skip lower-channel-count streams such as derived stereo tracks while still processing surround streams in the same file.",
            "input_type": "select",
            "select_options": tools.build_minimum_channel_select_options(),
        }
        self.__set_default_option(
            values["select_options"],
            "minimum_input_channel_count",
            default_option="any",
        )
        if self.settings.get_setting("mode") not in ["basic", "standard", "advanced"]:
            values["display"] = "hidden"
        return values

    def get_audio_codec_form_settings(self):
        values = {
            "label": "Audio Codec",
            "input_type": "select",
            "select_options": [],
        }
        for key in supported_codecs:
            values["select_options"].append(
                {
                    "value": key,
                    "label": supported_codecs.get(key, {}).get("label"),
                }
            )
        selected_codec = self.__set_default_option(
            values["select_options"], "audio_codec", default_option="aac"
        )
        if getattr(self.settings, "apply_default_fallbacks", True):
            current_value = self.settings.get_setting("audio_codec")
            if selected_codec and selected_codec != current_value:
                self.settings.set_setting("audio_codec", selected_codec)
        if self.settings.get_setting("mode") not in ["basic", "standard", "advanced"]:
            values["display"] = "hidden"
        return values

    def get_audio_codec_admonition_form_settings(self):
        codec_details = self.__selected_codec_details()
        codec_max_channels = codec_details.get("max_channels")
        warning = codec_details.get("warning")

        values = {
            "label": "Warning",
            "input_type": "section_admonition",
        }

        description_parts = []
        if codec_max_channels and codec_max_channels < 8:
            channel_label = tools.CHANNEL_LAYOUT_LABELS.get(
                codec_max_channels, codec_max_channels
            )
            description_parts.append(
                "Selected codec supports up to <code>{}</code> channels (<code>{}</code>).".format(
                    codec_max_channels,
                    channel_label,
                )
            )
        if warning:
            description_parts.append(warning)

        if description_parts:
            values["description"] = "<br>".join(description_parts)
        else:
            values["display"] = "hidden"

        if self.settings.get_setting("mode") not in ["basic", "standard", "advanced"]:
            values["display"] = "hidden"
        return values

    def get_force_transcode_form_settings(self):
        values = {
            "label": "Force transcoding even if the file is already using the desired audio codec",
            "description": "Will force a transcode of the audio stream even if it matches the selected audio codec.\n"
            "A file will only be forced to be transcoded once.\n"
            "After that it is flagged to prevent it being added to the pending tasks list in a loop.",
            "sub_setting": True,
        }
        if self.settings.get_setting("mode") not in ["basic", "standard", "advanced"]:
            values["display"] = "hidden"
        return values

    def get_audio_encoder_form_settings(self):
        values = {
            "label": "Audio Encoder",
            "input_type": "select",
            "select_options": [],
        }
        encoder_libs = tools.available_encoders(settings=self.settings)
        for encoder_name, encoder_lib in encoder_libs.items():
            encoder_details = encoder_lib.encoder_details(encoder_name)
            if encoder_details.get("codec") != self.settings.get_setting("audio_codec"):
                continue
            values["select_options"].append(
                {
                    "value": encoder_name,
                    "label": encoder_details.get("label"),
                }
            )
        selected_encoder = self.__set_default_option(
            values["select_options"], "audio_encoder"
        )
        if getattr(self.settings, "apply_default_fallbacks", True):
            current_encoder = self.settings.get_setting("audio_encoder")
            if selected_encoder and selected_encoder != current_encoder:
                self.settings.set_setting("audio_encoder", selected_encoder)
        if self.settings.get_setting("mode") not in ["basic", "standard"]:
            values["display"] = "hidden"
        return values

    def get_enable_smart_output_target_form_settings(self):
        values = {
            "label": "Enable smart output target",
            "description": "Automatically detect an audio bitrate target from the source file for Basic mode transcodes.",
        }
        if self.settings.get_setting("mode") not in ["basic"]:
            values["display"] = "hidden"
        return values

    def get_smart_output_target_form_settings(self):
        values = {
            "label": "Smart output target",
            "description": "Choose how Basic mode balances quality retention against compression when selecting the target bitrate.",
            "sub_setting": True,
            "input_type": "select",
            "select_options": [
                {
                    "value": "prefer_quality",
                    "label": "Prefer Quality",
                },
                {
                    "value": "balanced",
                    "label": "Balanced",
                },
                {
                    "value": "prefer_compression",
                    "label": "Prefer Compression",
                },
            ],
        }
        self.__set_default_option(
            values["select_options"], "smart_output_target", default_option="balanced"
        )
        if not self.settings.get_setting("enable_smart_output_target"):
            values["display"] = "hidden"
        if self.settings.get_setting("mode") not in ["basic"]:
            values["display"] = "hidden"
        return values

    def get_reencode_matching_codecs_above_target_form_settings(self):
        values = {
            "label": "Re-encode matching codecs above target",
            "description": "Also queue files that already use the selected codec when their bitrate is significantly above the smart output target window.",
            "sub_setting": True,
        }
        if not self.settings.get_setting("enable_smart_output_target"):
            values["display"] = "hidden"
        if self.settings.get_setting("mode") not in ["basic"]:
            values["display"] = "hidden"
        return values

    def get_enable_smart_audio_filters_form_settings(self):
        values = {
            "label": "Enable plugin's smart audio filters",
            "description": "Apply audio-aware output shaping such as channel-count limiting and loudness normalization.",
        }
        if self.settings.get_setting("mode") not in ["basic", "standard"]:
            values["display"] = "hidden"
        return values

    def get_max_channel_count_form_settings(self):
        codec_details = self.__selected_codec_details()
        codec_max_channels = codec_details.get("max_channels")
        values = {
            "label": "Set maximum channel count",
            "sub_setting": True,
            "input_type": "select",
            "select_options": tools.build_channel_select_options(codec_max_channels),
        }
        forced_channel_limit = tools.get_channel_option_limit(codec_max_channels)
        if forced_channel_limit:
            values["description"] = (
                "Selected codec supports up to {} channels ({}).".format(
                    forced_channel_limit,
                    tools.CHANNEL_LAYOUT_LABELS.get(
                        forced_channel_limit, forced_channel_limit
                    ),
                )
            )
        default_option = "same_as_source"
        current_value = self.settings.get_setting("max_channel_count")
        if forced_channel_limit and current_value not in [None, "", "same_as_source"]:
            parsed_current = tools.parse_max_channel_count(current_value)
            if parsed_current and parsed_current > forced_channel_limit:
                default_option = str(forced_channel_limit)
        self.__set_default_option(
            values["select_options"], "max_channel_count", default_option=default_option
        )
        if not self.settings.get_setting("enable_smart_audio_filters"):
            values["display"] = "hidden"
        if self.settings.get_setting("mode") not in ["basic", "standard"]:
            values["display"] = "hidden"
        return values

    def get_normalize_audio_volume_form_settings(self):
        values = {
            "label": "Normalise audio volume levels",
            "description": "Apply FFmpeg loudness normalization to the output audio stream.",
            "sub_setting": True,
        }
        if not self.settings.get_setting("enable_smart_audio_filters"):
            values["display"] = "hidden"
        if self.settings.get_setting("mode") not in ["basic", "standard"]:
            values["display"] = "hidden"
        return values

    def get_apply_custom_filters_form_settings(self):
        values = {
            "label": "Apply custom audio filters",
            "description": "Append one FFmpeg audio filter per line to the generated filtergraph.",
        }
        if self.settings.get_setting("mode") not in ["standard"]:
            values["display"] = "hidden"
        return values

    def get_custom_audio_filters_form_settings(self):
        values = {
            "label": "Custom audio filters",
            "input_type": "textarea",
            "sub_setting": True,
        }
        if not self.settings.get_setting("apply_custom_filters"):
            values["display"] = "hidden"
        if self.settings.get_setting("mode") not in ["standard"]:
            values["display"] = "hidden"
        return values

    def get_main_options_form_settings(self):
        values = {
            "label": "Write your own custom main options",
            "input_type": "textarea",
        }
        if self.settings.get_setting("mode") not in ["advanced"]:
            values["display"] = "hidden"
        return values

    def get_advanced_options_form_settings(self):
        values = {
            "label": "Write your own custom advanced options",
            "input_type": "textarea",
        }
        if self.settings.get_setting("mode") not in ["advanced"]:
            values["display"] = "hidden"
        return values

    def get_custom_options_form_settings(self):
        values = {
            "label": "Write your own custom audio options (starting with the encoder to use)",
            "input_type": "textarea",
        }
        if self.settings.get_setting("mode") not in ["advanced"]:
            values["display"] = "hidden"
        return values
