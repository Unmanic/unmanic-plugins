#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
    plugins.smart_audio_bitrate.py

    Written by:               Josh.5 <jsunnex@gmail.com>
    Date:                     14 Jun 2026

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


logger = logging.getLogger("Unmanic.Plugin.audio_transcoder")


class SmartAudioBitrateHelper:
    GOAL_PREFER_QUALITY = "prefer_quality"
    GOAL_BALANCED = "balanced"
    GOAL_PREFER_COMPRESSION = "prefer_compression"

    _GOALS = {
        GOAL_PREFER_QUALITY,
        GOAL_BALANCED,
        GOAL_PREFER_COMPRESSION,
    }

    _BITRATE_LADDERS = {
        "aac": [24, 32, 40, 48, 64, 80, 96, 112, 128, 160, 192, 224, 256, 320, 384, 448, 512, 576],
        "ac3": [96, 128, 160, 192, 224, 256, 320, 384, 448, 512, 576, 640],
        "eac3": [96, 128, 160, 192, 224, 256, 320, 384, 448, 512, 576, 640, 768, 896, 1024],
        "mp3": [32, 40, 48, 64, 80, 96, 112, 128, 160, 192, 224, 256, 320],
        "opus": [32, 48, 64, 80, 96, 112, 128, 160, 192, 224, 256, 320, 384, 448, 512],
    }

    _TARGETS = {
        "aac": {
            GOAL_PREFER_QUALITY: {
                "mono": 96,
                "stereo": 192,
                "surround": 384,
            },
            GOAL_BALANCED: {
                "mono": 80,
                "stereo": 160,
                "surround": 320,
            },
            GOAL_PREFER_COMPRESSION: {
                "mono": 64,
                "stereo": 128,
                "surround": 256,
            },
        },
        "mp3": {
            GOAL_PREFER_QUALITY: {
                "mono": 128,
                "stereo": 224,
                "surround": 320,
            },
            GOAL_BALANCED: {
                "mono": 96,
                "stereo": 192,
                "surround": 256,
            },
            GOAL_PREFER_COMPRESSION: {
                "mono": 64,
                "stereo": 160,
                "surround": 224,
            },
        },
        "ac3": {
            GOAL_PREFER_QUALITY: {
                "mono": 160,
                "stereo": 256,
                "surround": 640,
            },
            GOAL_BALANCED: {
                "mono": 128,
                "stereo": 224,
                "surround": 448,
            },
            GOAL_PREFER_COMPRESSION: {
                "mono": 96,
                "stereo": 192,
                "surround": 384,
            },
        },
        "eac3": {
            GOAL_PREFER_QUALITY: {
                "mono": 128,
                "stereo": 224,
                "surround": 512,
            },
            GOAL_BALANCED: {
                "mono": 96,
                "stereo": 192,
                "surround": 384,
            },
            GOAL_PREFER_COMPRESSION: {
                "mono": 64,
                "stereo": 160,
                "surround": 320,
            },
        },
        "opus": {
            GOAL_PREFER_QUALITY: {
                "mono": 80,
                "stereo": 160,
                "surround": 320,
            },
            GOAL_BALANCED: {
                "mono": 64,
                "stereo": 128,
                "surround": 256,
            },
            GOAL_PREFER_COMPRESSION: {
                "mono": 48,
                "stereo": 96,
                "surround": 192,
            },
        },
    }

    _MINIMUMS = {
        "aac": {
            "mono": 48,
            "stereo": 96,
            "surround": 192,
        },
        "mp3": {
            "mono": 64,
            "stereo": 96,
            "surround": 160,
        },
        "ac3": {
            "mono": 96,
            "stereo": 192,
            "surround": 384,
        },
        "eac3": {
            "mono": 64,
            "stereo": 128,
            "surround": 256,
        },
        "opus": {
            "mono": 48,
            "stereo": 96,
            "surround": 192,
        },
    }

    _LOSSY_SOURCE_RETAIN = {
        GOAL_PREFER_QUALITY: 1.00,
        GOAL_BALANCED: 0.92,
        GOAL_PREFER_COMPRESSION: 0.82,
    }

    _FIT_UPPER_FACTORS = {
        GOAL_PREFER_QUALITY: 1.35,
        GOAL_BALANCED: 1.20,
        GOAL_PREFER_COMPRESSION: 1.10,
    }

    _LOSSY_CODECS = {
        "aac",
        "ac3",
        "amr_nb",
        "amr_wb",
        "dts",
        "eac3",
        "mp2",
        "mp3",
        "opus",
        "vorbis",
        "wma",
    }

    _LOSSLESS_CODECS = {
        "alac",
        "ape",
        "flac",
        "pcm_alaw",
        "pcm_f32be",
        "pcm_f32le",
        "pcm_f64be",
        "pcm_f64le",
        "pcm_mulaw",
        "pcm_s16be",
        "pcm_s16le",
        "pcm_s24be",
        "pcm_s24le",
        "pcm_s32be",
        "pcm_s32le",
        "pcm_u16be",
        "pcm_u16le",
        "pcm_u24be",
        "pcm_u24le",
        "pcm_u32be",
        "pcm_u32le",
        "truehd",
        "tta",
        "wavpack",
    }

    _LOSSLESS_TARGET_CODECS = {
        "flac",
    }

    def __init__(self, probe):
        self.probe = probe

    @staticmethod
    def _safe_int(value):
        try:
            return int(value)
        except (TypeError, ValueError):
            return None

    @staticmethod
    def _safe_float(value):
        try:
            return float(value)
        except (TypeError, ValueError):
            return None

    @staticmethod
    def _parse_duration_hhmmss(duration_tag):
        if not duration_tag or not isinstance(duration_tag, str) or ":" not in duration_tag:
            return None
        try:
            h, m, s = duration_tag.split(":")
            return float(h) * 3600 + float(m) * 60 + float(s)
        except (TypeError, ValueError):
            return None

    @staticmethod
    def _get_tag_value(tags, key):
        if not isinstance(tags, dict):
            return None
        candidates = (
            key,
            key.upper(),
            key.lower(),
            "{}-eng".format(key),
            "{}-eng".format(key.upper()),
            "{}-eng".format(key.lower()),
        )
        for candidate in candidates:
            if candidate in tags:
                return tags.get(candidate)
        key_lower = str(key).lower()
        for tag_key, tag_value in tags.items():
            if str(tag_key).lower() in (key_lower, "{}-eng".format(key_lower)):
                return tag_value
        return None

    def _duration_seconds(self, probe_dict, stream_info):
        format_info = probe_dict.get("format") or {}
        duration = self._safe_float(format_info.get("duration"))
        if duration and duration > 0:
            return duration

        duration = self._safe_float(stream_info.get("duration"))
        if duration and duration > 0:
            return duration

        for tags in (stream_info.get("tags") or {}, format_info.get("tags") or {}):
            duration_tag = self._get_tag_value(tags, "DURATION")
            duration = self._parse_duration_hhmmss(duration_tag)
            if duration and duration > 0:
                return duration

        return None

    def _channel_bucket(self, channels):
        if not channels or channels <= 1:
            return "mono"
        if channels <= 2:
            return "stereo"
        return "surround"

    def _source_bitrate_from_tags(self, stream_info):
        tags = stream_info.get("tags") or {}

        bps = self._safe_int(self._get_tag_value(tags, "BPS"))
        if bps and bps > 0:
            return bps

        number_of_bytes = self._safe_int(self._get_tag_value(tags, "NUMBER_OF_BYTES"))
        duration_seconds = self._parse_duration_hhmmss(self._get_tag_value(tags, "DURATION"))
        if number_of_bytes and number_of_bytes > 0 and duration_seconds and duration_seconds > 0:
            return int((number_of_bytes * 8) / duration_seconds)

        return None

    def _derive_source_bitrate(self, stream_info):
        probe_dict = self.probe.get_probe() or {}
        stream_bitrate = self._safe_int(stream_info.get("bit_rate"))
        tag_bitrate = None if stream_bitrate else self._source_bitrate_from_tags(stream_info)
        container_bitrate = self._safe_int((probe_dict.get("format") or {}).get("bit_rate"))

        file_path = (probe_dict.get("format") or {}).get("filename")
        duration = self._duration_seconds(probe_dict, stream_info)
        filesize_bits = None
        if file_path and os.path.exists(file_path):
            try:
                filesize_bits = os.path.getsize(file_path) * 8
            except OSError:
                filesize_bits = None

        derived_bitrate = None
        if stream_bitrate:
            derived_bitrate = stream_bitrate
        elif tag_bitrate:
            derived_bitrate = tag_bitrate
        elif container_bitrate:
            derived_bitrate = container_bitrate
        elif filesize_bits and duration and duration > 0:
            derived_bitrate = int(filesize_bits / duration)

        confidence = "high"
        notes = []
        if derived_bitrate is None:
            confidence = "low"
            notes.append("missing_bitrate")
        elif stream_bitrate is None:
            confidence = "medium"
            notes.append("bitrate_estimated")

        if container_bitrate is None:
            notes.append("missing_container_bitrate")

        return {
            "stream_bitrate": stream_bitrate,
            "container_bitrate": container_bitrate,
            "derived_bitrate": derived_bitrate,
            "duration": duration,
            "confidence": confidence,
            "notes": notes,
        }

    def _sample_rate_factor(self, sample_rate, goal):
        sample_rate = self._safe_int(sample_rate) or 0
        if sample_rate and sample_rate <= 24000:
            return 0.75
        if sample_rate and sample_rate <= 32000:
            return 0.85
        if sample_rate and sample_rate >= 88200:
            if goal == self.GOAL_PREFER_QUALITY:
                return 1.10
            if goal == self.GOAL_BALANCED:
                return 1.05
        return 1.0

    def _target_bitrate_kbps(self, target_codec, goal, channels, sample_rate, source_codec, source_bitrate_kbps):
        codec_table = self._TARGETS.get(target_codec) or self._TARGETS.get("aac")
        goal = goal if goal in self._GOALS else self.GOAL_BALANCED
        channel_bucket = self._channel_bucket(channels)

        base_target = codec_table.get(goal, {}).get(channel_bucket)
        if not base_target:
            base_target = codec_table.get(self.GOAL_BALANCED, {}).get(channel_bucket, 128)

        target = float(base_target) * self._sample_rate_factor(sample_rate, goal)
        minimum = self._MINIMUMS.get(target_codec, {}).get(channel_bucket, 64)

        source_codec = (source_codec or "").lower()
        if source_bitrate_kbps and source_codec in self._LOSSY_CODECS:
            retain_factor = self._LOSSY_SOURCE_RETAIN.get(goal, 0.92)
            target = min(target, float(source_bitrate_kbps) * retain_factor)

        target = max(target, float(minimum))
        return self._round_bitrate(target_codec, int(round(target)))

    def _round_bitrate(self, target_codec, bitrate_kbps):
        ladder = self._BITRATE_LADDERS.get(target_codec) or self._BITRATE_LADDERS.get("aac")
        if not ladder:
            return bitrate_kbps
        for value in ladder:
            if value >= bitrate_kbps:
                return int(value)
        return int(ladder[-1])

    def _fits_target(self, goal, estimated_source_kbps, recommended_target_kbps):
        if not estimated_source_kbps or not recommended_target_kbps:
            return False, None
        upper_factor = self._FIT_UPPER_FACTORS.get(goal, 1.20)
        max_fit = int(round(recommended_target_kbps * upper_factor))
        return estimated_source_kbps <= max_fit, max_fit

    def recommend_params(self, stream_info, target_codec, target_encoder, goal, target_channels=None):
        target_codec = (target_codec or "aac").lower()
        requested_goal = goal or self.GOAL_BALANCED
        goal = requested_goal if requested_goal in self._GOALS else self.GOAL_BALANCED

        source_codec = (stream_info.get("codec_name") or "").lower()
        source_channels = self._safe_int(stream_info.get("channels")) or 2
        channels = self._safe_int(target_channels) or source_channels
        sample_rate = self._safe_int(stream_info.get("sample_rate")) or 44100
        bitrate_data = self._derive_source_bitrate(stream_info)
        derived_bitrate = bitrate_data.get("derived_bitrate")
        source_bitrate_kbps = int(round(derived_bitrate / 1000.0)) if derived_bitrate else None

        if target_codec in self._LOSSLESS_TARGET_CODECS:
            notes = list(bitrate_data.get("notes") or [])
            notes.append("lossless_target")
            recommendation = {
                "goal": goal,
                "target_codec": target_codec,
                "target_encoder": target_encoder,
                "source_codec": source_codec,
                "source_channels": source_channels,
                "target_channels": channels,
                "source_sample_rate": sample_rate,
                "source_bitrate_kbps": source_bitrate_kbps,
                "recommended_target_kbps": None,
                "max_fit_kbps": None,
                "quality_mode": "lossless",
                "confidence": bitrate_data.get("confidence"),
                "should_transcode_for_bitrate": False,
                "notes": notes,
            }
            logger.debug(
                "[SmartAudioBitrateHelper] recommendation goal=%s target_codec=%s source_codec=%s source_kbps=%s target_kbps=%s max_fit_kbps=%s confidence=%s notes=%s",
                recommendation.get("goal"),
                recommendation.get("target_codec"),
                recommendation.get("source_codec"),
                recommendation.get("source_bitrate_kbps"),
                recommendation.get("recommended_target_kbps"),
                recommendation.get("max_fit_kbps"),
                recommendation.get("confidence"),
                ",".join(recommendation.get("notes") or []),
            )
            return recommendation

        recommended_target_kbps = self._target_bitrate_kbps(
            target_codec,
            goal,
            channels,
            sample_rate,
            source_codec,
            source_bitrate_kbps,
        )
        fits_target, max_fit_kbps = self._fits_target(goal, source_bitrate_kbps, recommended_target_kbps)

        should_transcode_for_bitrate = bool(
            source_codec == target_codec and
            source_bitrate_kbps and
            max_fit_kbps and
            source_bitrate_kbps > max_fit_kbps
        )

        notes = list(bitrate_data.get("notes") or [])
        if source_codec in self._LOSSLESS_CODECS:
            notes.append("lossless_source")
        elif source_codec in self._LOSSY_CODECS:
            notes.append("lossy_source")

        if should_transcode_for_bitrate:
            notes.append("above_target_window")
        elif fits_target:
            notes.append("within_target_window")
        elif source_bitrate_kbps and source_bitrate_kbps < recommended_target_kbps:
            notes.append("below_target_no_upbitrate")

        recommendation = {
            "goal": goal,
            "target_codec": target_codec,
            "target_encoder": target_encoder,
            "source_codec": source_codec,
            "source_channels": source_channels,
            "target_channels": channels,
            "source_sample_rate": sample_rate,
            "source_bitrate_kbps": source_bitrate_kbps,
            "recommended_target_kbps": recommended_target_kbps,
            "max_fit_kbps": max_fit_kbps,
            "quality_mode": "target_bitrate",
            "confidence": bitrate_data.get("confidence"),
            "should_transcode_for_bitrate": should_transcode_for_bitrate,
            "notes": notes,
        }

        logger.debug(
            "[SmartAudioBitrateHelper] recommendation goal=%s target_codec=%s source_codec=%s source_kbps=%s target_kbps=%s max_fit_kbps=%s confidence=%s notes=%s",
            recommendation.get("goal"),
            recommendation.get("target_codec"),
            recommendation.get("source_codec"),
            recommendation.get("source_bitrate_kbps"),
            recommendation.get("recommended_target_kbps"),
            recommendation.get("max_fit_kbps"),
            recommendation.get("confidence"),
            ",".join(recommendation.get("notes") or []),
        )

        return recommendation
