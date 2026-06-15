#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
    plugins.tools.py

    Written by:               Josh.5 <jsunnex@gmail.com>
    Date:                     14 June 2026

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

import mimetypes

from audio_transcoder.lib.encoders.ac3 import Ac3Encoder
from audio_transcoder.lib.encoders.aac import AacEncoder
from audio_transcoder.lib.encoders.eac3 import Eac3Encoder
from audio_transcoder.lib.encoders.flac import FlacEncoder
from audio_transcoder.lib.encoders.lame import LameEncoder
from audio_transcoder.lib.encoders.opus import OpusEncoder

CHANNEL_LAYOUT_LABELS = {
    1: "1.0",
    2: "2.0",
    6: "5.1",
    8: "7.1",
}
UNMANIC_STREAM_IGNORE_PLUGIN_ID = "audio_transcoder"


def append_worker_log(worker_log, line: str):
    if worker_log is None or not isinstance(worker_log, list):
        return
    try:
        worker_log.append(str(line))
    except Exception:
        return


def available_encoders(settings=None, probe=None):
    return_encoders = {}
    encoder_libs = [
        LameEncoder,
        AacEncoder,
        FlacEncoder,
        OpusEncoder,
        Ac3Encoder,
        Eac3Encoder,
    ]
    for encoder_class in encoder_libs:
        encoder_lib = encoder_class(settings=settings, probe=probe)
        for encoder in encoder_lib.provides():
            return_encoders[encoder] = encoder_lib
    return return_encoders


def join_filtergraph(filter_id, filter_args, stream_id):
    filtergraph = ''
    count = 1
    for filter_string in filter_args:
        if filtergraph:
            filtergraph += ';'
        filtergraph += '[{}]'.format(filter_id)
        filtergraph += '{}'.format(filter_string)
        filter_id = '0:af:{}-{}'.format(stream_id, count)
        filtergraph += '[{}]'.format(filter_id)
        count += 1
    return filter_id, filtergraph


def get_media_file_mode(path: str):
    file_type = mimetypes.guess_type(path)[0]
    if not file_type:
        return None

    file_type_category = file_type.split('/')[0]
    if file_type_category == 'video':
        return 'video_file'
    if file_type_category == 'audio':
        return 'audio_file'
    return None


def parse_max_channel_count(value):
    if value in [None, '', 'same_as_source']:
        return None
    try:
        parsed = int(value)
        if parsed > 0:
            return parsed
    except (TypeError, ValueError):
        return None
    return None


def get_channel_option_limit(max_channels):
    if not max_channels:
        return None
    valid_options = [
        channel_count for channel_count in sorted(CHANNEL_LAYOUT_LABELS.keys())
        if channel_count <= max_channels
    ]
    if not valid_options:
        return None
    return valid_options[-1]


def build_channel_select_options(max_channels=None):
    options = [
        {
            "value": "same_as_source",
            "label": "Same as source",
        }
    ]
    for channel_count in sorted(CHANNEL_LAYOUT_LABELS.keys(), reverse=True):
        if max_channels and channel_count > max_channels:
            continue
        options.append(
            {
                "value": str(channel_count),
                "label": CHANNEL_LAYOUT_LABELS[channel_count],
            }
        )
    return options


def build_minimum_channel_select_options():
    options = [
        {
            "value": "any",
            "label": "Any channel count",
        }
    ]
    for channel_count in sorted(CHANNEL_LAYOUT_LABELS.keys()):
        options.append(
            {
                "value": str(channel_count),
                "label": "{} and above".format(CHANNEL_LAYOUT_LABELS[channel_count]),
            }
        )
    return options


def parse_minimum_channel_count(value):
    if value in [None, '', 'any']:
        return None
    return parse_max_channel_count(value)


def _parse_boolish(value):
    if value is None:
        return False
    return str(value).strip().lower() in ['1', 'true', 'yes', 'on']


def _parse_unmanic_kv_string(value):
    parsed = {}
    if not value or not isinstance(value, str):
        return parsed
    for part in value.split(';'):
        if '=' not in part:
            continue
        key, raw_value = part.split('=', 1)
        key = key.strip().lower()
        raw_value = raw_value.strip()
        if key:
            parsed[key] = raw_value
    return parsed


def get_unmanic_stream_marker_data(stream_info):
    tags = stream_info.get('tags') or {}
    parsed = {}

    for tag_key, tag_value in tags.items():
        normalized_key = str(tag_key).strip().lower()
        if normalized_key in [
            'unmanic.ignore',
            'unmanic.ignore_for',
            'unmanic.source_plugin',
            'unmanic.role',
            'unmanic_ignore',
            'unmanic_ignore_for',
        ]:
            parsed[normalized_key] = str(tag_value).strip()

    for field in ['comment', 'description']:
        for candidate in [field, field.upper(), field.capitalize()]:
            if candidate in tags:
                parsed.update(_parse_unmanic_kv_string(tags.get(candidate)))

    return parsed


def stream_marked_to_be_ignored(stream_info, plugin_id=UNMANIC_STREAM_IGNORE_PLUGIN_ID):
    marker_data = get_unmanic_stream_marker_data(stream_info)

    if _parse_boolish(marker_data.get('unmanic.ignore')):
        return True
    if _parse_boolish(marker_data.get('unmanic_ignore')):
        return True

    ignore_for = marker_data.get('unmanic.ignore_for') or marker_data.get('unmanic_ignore_for')
    if ignore_for:
        ignored_targets = [value.strip().lower() for value in str(ignore_for).split(',') if value.strip()]
        if 'all' in ignored_targets or str(plugin_id).lower() in ignored_targets:
            return True

    return False
