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

from audio_transcoder.lib import tools
from audio_transcoder.lib.ffmpeg import StreamMapper
from audio_transcoder.lib.smart_audio_bitrate import SmartAudioBitrateHelper

logger = logging.getLogger("Unmanic.Plugin.audio_transcoder")


class PluginStreamMapper(StreamMapper):
    def __init__(self, worker_log=None):
        super(PluginStreamMapper, self).__init__(logger, ['audio'])
        self.worker_log = worker_log if isinstance(worker_log, list) else None
        self.abspath = None
        self.settings = None
        self.media_file_mode = 'audio_file'
        self.complex_audio_filters = {}
        self.filter_complex_parts = []
        self.forced_encode = False
        self.execution_stage = False
        self.stream_recommendations = {}

    def _minimum_input_channel_count(self):
        return tools.parse_minimum_channel_count(
            self.settings.get_setting('minimum_input_channel_count')
        )

    @staticmethod
    def _stream_channels(stream_info):
        try:
            return int(stream_info.get('channels'))
        except (TypeError, ValueError):
            return None

    def _get_target_channel_count(self, stream_info):
        source_channels = stream_info.get('channels')
        encoder_name = self.settings.get_setting('audio_encoder')
        encoder_lib = tools.available_encoders(settings=self.settings, probe=self.probe).get(encoder_name)
        encoder_details = encoder_lib.encoder_details(encoder_name) if encoder_lib else {}
        codec_max_channels = encoder_details.get('max_channels')

        max_channel_count = None
        if self.settings.get_setting('enable_smart_audio_filters'):
            max_channel_count = tools.parse_max_channel_count(self.settings.get_setting('max_channel_count'))

        try:
            source_channels = int(source_channels)
        except (TypeError, ValueError):
            source_channels = None

        target_channels = source_channels
        if max_channel_count:
            if target_channels is None:
                target_channels = max_channel_count
            else:
                target_channels = min(target_channels, max_channel_count)

        if codec_max_channels:
            if target_channels is None:
                target_channels = codec_max_channels
            else:
                target_channels = min(target_channels, codec_max_channels)

        return target_channels

    def set_default_values(self, settings, abspath, probe):
        self.execution_stage = False
        self.abspath = abspath
        self.set_probe(probe)
        self.set_input_file(abspath)
        self.settings = settings
        self.media_file_mode = tools.get_media_file_mode(abspath) or 'audio_file'
        self.filter_complex_parts = []
        tools.append_worker_log(
            self.worker_log,
            "Stream mapper configured (mode='{}', media_mode='{}', encoder='{}')".format(
                self.settings.get_setting('mode'),
                self.media_file_mode,
                self.settings.get_setting('audio_encoder'),
            )
        )

        if self.settings.get_setting('mode') == 'advanced':
            main_options = settings.get_setting('main_options').split()
            if main_options:
                self.main_options = main_options
            advanced_options = settings.get_setting('advanced_options').split()
            if advanced_options:
                self.advanced_options = advanced_options
            return

        encoder_name = self.settings.get_setting('audio_encoder')
        encoder_lib = tools.available_encoders(settings=self.settings, probe=self.probe).get(encoder_name)
        if encoder_lib:
            generic_kwargs, advanced_kwargs = encoder_lib.generate_default_args()
            self.set_ffmpeg_generic_options(**generic_kwargs)
            self.set_ffmpeg_advanced_options(**advanced_kwargs)

    def enable_execution_stage(self):
        self.execution_stage = True
        tools.append_worker_log(self.worker_log, "Stream mapper entering execution stage")
        self.stream_mapping = []
        self.stream_encoding = []
        self.complex_audio_filters = {}
        self.filter_complex_parts = []
        self.stream_recommendations = {}

    def _append_filter_complex(self, filter_complex):
        if not filter_complex:
            return
        self.filter_complex_parts.append(filter_complex)
        self.set_ffmpeg_advanced_options(
            **{"-filter_complex": ';'.join(self.filter_complex_parts)}
        )

    def streams_need_processing(self):
        tools.append_worker_log(
            self.worker_log,
            "Stream mapper building stream mapping (stage='{}')".format(
                "execution" if self.execution_stage else "analysis"
            )
        )
        needs_processing = super(PluginStreamMapper, self).streams_need_processing()
        tools.append_worker_log(
            self.worker_log,
            "Stream mapper stream summary (video={}, audio={}, subtitle={}, data={}, attachment={})".format(
                self.video_stream_count,
                self.audio_stream_count,
                self.subtitle_stream_count,
                self.data_stream_count,
                self.attachment_stream_count,
            )
        )
        return needs_processing

    def build_filter_chain(self, stream_info, stream_id):
        tools.append_worker_log(self.worker_log, "Stream mapper building filter chain for audio stream {}".format(stream_id))
        filter_args = []
        source_channels = stream_info.get('channels')
        source_layout = stream_info.get('channel_layout')
        source_sample_rate = stream_info.get('sample_rate')
        target_channels = self._get_target_channel_count(stream_info)
        filter_state = {
            "source_channels":       source_channels,
            "target_channels":       target_channels,
            "source_layout":         source_layout,
            "target_layout":         source_layout,
            "source_sample_rate":    source_sample_rate,
            "target_sample_rate":    source_sample_rate,
            "normalization_applied": False,
            "downmix_applied":       False,
            "resample_applied":      False,
            "execution_stage":       self.execution_stage,
        }

        encoder_name = self.settings.get_setting('audio_encoder')
        encoder_lib = tools.available_encoders(settings=self.settings, probe=self.probe).get(encoder_name)

        smart_filters = []
        if self.settings.get_setting('enable_smart_audio_filters'):
            if target_channels and source_channels and int(target_channels) < int(source_channels):
                filter_state["downmix_applied"] = True
                if int(target_channels) == 1:
                    filter_state["target_layout"] = "mono"
                elif int(target_channels) == 2:
                    filter_state["target_layout"] = "stereo"
                elif int(target_channels) == 6:
                    filter_state["target_layout"] = "5.1"
                elif int(target_channels) == 8:
                    filter_state["target_layout"] = "7.1"

            if self.settings.get_setting('normalize_audio_volume'):
                smart_filters.append({
                    "loudnorm": {
                        "filter": "loudnorm=I=-16:TP=-1.5:LRA=11"
                    }
                })
                filter_state["normalization_applied"] = True

        filtergraph_config = {}
        if encoder_lib:
            filtergraph_config = encoder_lib.generate_filtergraphs(
                filter_args,
                smart_filters,
                encoder_name,
            )

        smart_filters = filtergraph_config.get('smart_filters', smart_filters)
        for smart_filter in smart_filters:
            for _, filter_data in smart_filter.items():
                filter_args.append(filter_data.get('filter'))

        if self.settings.get_setting('mode') == 'standard' and self.settings.get_setting('apply_custom_filters'):
            for audio_filter in self.settings.get_setting('custom_audio_filters').splitlines():
                if audio_filter.strip():
                    filter_args.append(audio_filter.strip())

        self.set_ffmpeg_generic_options(**filtergraph_config.get('generic_kwargs', {}))
        self.set_ffmpeg_advanced_options(**filtergraph_config.get('advanced_kwargs', {}))

        start_filter_args = filtergraph_config.get('start_filter_args', [])
        end_filter_args = filtergraph_config.get('end_filter_args', [])
        filter_args = start_filter_args + filter_args + end_filter_args

        if not filter_args:
            self.complex_audio_filters[stream_id] = filter_state
            return None, None, filter_state

        filter_id = '0:a:{}'.format(stream_id)
        filter_id, filtergraph = tools.join_filtergraph(filter_id, filter_args, stream_id)

        self.complex_audio_filters[stream_id] = filter_state
        return filter_id, filtergraph, filter_state

    def test_stream_needs_processing(self, stream_info: dict):
        codec_type = stream_info.get('codec_type', '').lower()
        codec_name = stream_info.get('codec_name', '').lower()

        if codec_type in ['audio']:
            if tools.stream_marked_to_be_ignored(
                stream_info,
                plugin_id=tools.UNMANIC_STREAM_IGNORE_PLUGIN_ID,
            ):
                tools.append_worker_log(
                    self.worker_log,
                    "Audio stream marked to be ignored by Unmanic metadata - skipping"
                )
                return False

            minimum_channels = self._minimum_input_channel_count()
            source_channels = self._stream_channels(stream_info)
            if minimum_channels and source_channels and source_channels < minimum_channels:
                tools.append_worker_log(
                    self.worker_log,
                    "Audio stream channel count below configured processing threshold (stream={}, minimum={}) - skipping".format(
                        source_channels,
                        minimum_channels,
                    )
                )
                return False

            if (
                self.settings.get_setting('enable_smart_audio_filters') and (
                    (
                        self.settings.get_setting('normalize_audio_volume')
                    ) or (
                        self._get_target_channel_count(stream_info) and
                        int(self._get_target_channel_count(stream_info)) < int(stream_info.get('channels') or 0)
                    )
                )
            ):
                return True
            if (
                self.settings.get_setting('mode') == 'standard' and
                self.settings.get_setting('apply_custom_filters') and
                self.settings.get_setting('custom_audio_filters').strip()
            ):
                return True
            if codec_name == self.settings.get_setting('audio_codec'):
                if (
                    self.settings.get_setting('mode') in ['basic'] and
                    self.settings.get_setting('enable_smart_output_target') and
                    self.settings.get_setting('reencode_matching_codecs_above_target')
                ):
                    helper = SmartAudioBitrateHelper(self.probe)
                    recommendation = helper.recommend_params(
                        stream_info,
                        self.settings.get_setting('audio_codec'),
                        self.settings.get_setting('audio_encoder'),
                        self.settings.get_setting('smart_output_target'),
                        target_channels=self._get_target_channel_count(stream_info),
                    )
                    self.stream_recommendations[stream_info.get('index', len(self.stream_recommendations))] = recommendation
                    if recommendation.get('should_transcode_for_bitrate'):
                        tools.append_worker_log(
                            self.worker_log,
                            "Audio stream bitrate exceeds smart target window (source={}k, target={}k, max_fit={}k)".format(
                                recommendation.get('source_bitrate_kbps'),
                                recommendation.get('recommended_target_kbps'),
                                recommendation.get('max_fit_kbps'),
                            )
                        )
                        return True
                if not self.settings.get_setting('force_transcode'):
                    return False
                self.forced_encode = True

        return True

    def custom_stream_mapping(self, stream_info: dict, stream_id: int):
        codec_type = stream_info.get('codec_type', '').lower()
        stream_specifier = '{}:{}'.format(self.stream_type_idents.get(codec_type), stream_id)
        map_identifier = '0:{}'.format(stream_specifier)
        encoder_name = self.settings.get_setting('audio_encoder')

        if codec_type in ['audio']:
            tools.append_worker_log(
                self.worker_log,
                "Stream mapper mapping audio stream {} for encoding (encoder='{}')".format(stream_id, encoder_name)
            )
            if self.settings.get_setting('mode') == 'advanced':
                stream_encoding = ['-c:{}'.format(stream_specifier)]
                stream_encoding += self.settings.get_setting('custom_options').split()
            else:
                filter_id, filter_complex, filter_state = self.build_filter_chain(stream_info, stream_id)
                if filter_complex:
                    map_identifier = '[{}]'.format(filter_id)
                    self._append_filter_complex(filter_complex)
                else:
                    filter_state = self.complex_audio_filters.get(stream_id, {
                        "source_channels":       stream_info.get('channels'),
                        "target_channels":       stream_info.get('channels'),
                        "source_layout":         stream_info.get('channel_layout'),
                        "target_layout":         stream_info.get('channel_layout'),
                        "source_sample_rate":    stream_info.get('sample_rate'),
                        "target_sample_rate":    stream_info.get('sample_rate'),
                        "normalization_applied": False,
                        "downmix_applied":       False,
                        "resample_applied":      False,
                        "execution_stage":       self.execution_stage,
                    })

                stream_encoding = [
                    '-c:{}'.format(stream_specifier), encoder_name,
                ]
                encoder_lib = tools.available_encoders(settings=self.settings, probe=self.probe).get(encoder_name)
                if encoder_lib:
                    recommendation = None
                    if self.settings.get_setting('mode') in ['basic'] and self.settings.get_setting('enable_smart_output_target'):
                        recommendation = self.stream_recommendations.get(stream_id)
                        if recommendation is None:
                            helper = SmartAudioBitrateHelper(self.probe)
                            recommendation = helper.recommend_params(
                                stream_info,
                                self.settings.get_setting('audio_codec'),
                                encoder_name,
                                self.settings.get_setting('smart_output_target'),
                                target_channels=filter_state.get('target_channels'),
                            )
                            self.stream_recommendations[stream_id] = recommendation
                        tools.append_worker_log(
                            self.worker_log,
                            "Smart bitrate target selected for audio stream {} (goal='{}', source={}k, target={}k, confidence='{}')".format(
                                stream_id,
                                recommendation.get('goal'),
                                recommendation.get('source_bitrate_kbps'),
                                recommendation.get('recommended_target_kbps'),
                                recommendation.get('confidence'),
                            )
                        )
                    stream_args = encoder_lib.stream_args(
                        stream_info,
                        stream_id,
                        encoder_name,
                        filter_state=filter_state,
                    )
                    stream_encoding += stream_args.get("encoder_args", [])
                    stream_encoding += stream_args.get("stream_args", [])
                    self.set_ffmpeg_generic_options(**stream_args.get("generic_kwargs", {}))
                    self.set_ffmpeg_advanced_options(**stream_args.get("advanced_kwargs", {}))
        else:
            raise Exception("Unsupported codec type {}".format(codec_type))

        return {
            'stream_mapping':  ['-map', map_identifier],
            'stream_encoding': stream_encoding,
        }

    def set_output_file(self, path):
        if self.media_file_mode == 'video_file':
            self.output_file = os.path.abspath(path)
            return self.output_file

        encoder_name = self.settings.get_setting('audio_encoder')
        encoder = tools.available_encoders(settings=self.settings, probe=self.probe).get(encoder_name)
        container_extension = encoder.get_output_file_extension(encoder_name)
        split_file_out = os.path.splitext(path)
        new_file_out = "{}.{}".format(split_file_out[0], container_extension)
        self.output_file = os.path.abspath(new_file_out)
        return self.output_file
