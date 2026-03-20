#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
plugins.plex_dvr_repair.lib.logic.py

Written by:               Josh.5 <jsunnex@gmail.com>
Date:                     18 Mar 2026

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
import re
import shlex
import subprocess
import time
from collections import Counter
from dataclasses import dataclass
from pathlib import Path

COPY_FILE_REGEX = re.compile(r"^(?P<stem>.+?) \((?i:copy) (?P<copy_number>\d+)\)$")
SUPPORTED_EXTENSIONS = {".ts"}
PLEX_SIDECAR_SUFFIXES = (".log", ".txt", ".logo.txt")
COPY_FILE_STALE_MINUTES = 5
RECORDING_GROUP_JOIN_BUFFER_SECONDS = 300
REPAIRED_FILE_MARKER = "UNMANIC_REPAIRED"
logger = logging.getLogger("Unmanic.Plugin.plex_dvr_repair")


@dataclass
class Fragment:
    path: Path
    base_stem: str
    extension: str
    is_copy: bool
    copy_number: int
    size_bytes: int
    mtime: float
    duration: float = None


def is_candidate_extension(extension):
    return str(extension).lower() in SUPPORTED_EXTENSIONS


def is_copy_fragment_name(filename):
    path = Path(filename)
    return COPY_FILE_REGEX.match(path.stem) is not None


def is_repaired_output_name(filename):
    return REPAIRED_FILE_MARKER.lower() in Path(filename).stem.lower()


def parse_fragment_path(path):
    path = Path(path)
    if not path.exists():
        return None
    extension = path.suffix.lower()
    stem = path.stem
    copy_match = COPY_FILE_REGEX.match(stem)
    if copy_match:
        base_stem = copy_match.group("stem")
        copy_number = int(copy_match.group("copy_number"))
        is_copy = True
    else:
        base_stem = stem
        copy_number = 0
        is_copy = False
    stat_result = path.stat()
    return Fragment(
        path=path,
        base_stem=base_stem,
        extension=extension,
        is_copy=is_copy,
        copy_number=copy_number,
        size_bytes=stat_result.st_size,
        mtime=stat_result.st_mtime,
    )


def fragment_sort_key(fragment):
    base_priority = -1 if not fragment.is_copy else fragment.copy_number
    return fragment.mtime, base_priority, fragment.path.name.lower()


def discover_candidate_fragments(base_path):
    base_path = Path(base_path)
    base_fragment = parse_fragment_path(base_path)
    if base_fragment is None:
        return []
    if base_fragment.is_copy or not is_candidate_extension(base_fragment.extension):
        return []
    candidates = []
    for sibling in base_path.parent.iterdir():
        parsed = parse_fragment_path(sibling)
        if parsed is None:
            continue
        if parsed.extension != base_fragment.extension:
            continue
        if parsed.base_stem != base_fragment.base_stem:
            continue
        candidates.append(parsed)
    candidates = sorted(candidates, key=fragment_sort_key)
    logger.debug(
        "Discovered candidate fragments for '%s': %s"
        % (
            base_path.name,
            [
                {
                    "name": fragment.path.name,
                    "mtime": fragment.mtime,
                    "size_bytes": fragment.size_bytes,
                    "copy_number": fragment.copy_number,
                }
                for fragment in candidates
            ],
        )
    )
    return candidates


def is_recently_modified(fragment, within_minutes):
    threshold = time.time() - (within_minutes * 60)
    return fragment.mtime >= threshold


def find_active_sidecars(base_path, grace_minutes, ignore_when_sidecars_exist):
    if not ignore_when_sidecars_exist:
        return []
    base_path = Path(base_path)
    threshold = time.time() - (grace_minutes * 60)
    active = []
    for suffix in PLEX_SIDECAR_SUFFIXES:
        sidecar = base_path.with_suffix(suffix)
        if not sidecar.exists():
            continue
        if sidecar.stat().st_mtime >= threshold:
            active.append(sidecar)
    if active:
        logger.debug(
            "Active sidecars for '%s' within %s minutes: %s"
            % (
                base_path.name,
                grace_minutes,
                [sidecar.name for sidecar in active],
            )
        )
    return active


def group_fragments_by_recording_window(
    fragments, join_buffer_seconds=RECORDING_GROUP_JOIN_BUFFER_SECONDS
):
    if not fragments:
        return []
    sorted_fragments = sorted(fragments, key=fragment_sort_key)
    groups = [[sorted_fragments[0]]]

    first_fragment_duration = max(sorted_fragments[0].duration or 0.0, 0.0)
    group_end_mtime = sorted_fragments[0].mtime
    group_start_estimate = group_end_mtime - first_fragment_duration
    for fragment in sorted_fragments[1:]:
        fragment_duration = max(fragment.duration or 0.0, 0.0)
        fragment_start_estimate = fragment.mtime - fragment_duration
        allowed_group_end = group_end_mtime + join_buffer_seconds
        if fragment_start_estimate > allowed_group_end:
            groups.append([fragment])
            group_end_mtime = fragment.mtime
            group_start_estimate = fragment_start_estimate
        else:
            groups[-1].append(fragment)
            group_end_mtime = max(group_end_mtime, fragment.mtime)
            group_start_estimate = min(group_start_estimate, fragment_start_estimate)
    logger.debug(
        "Grouped fragments by recording window with %s-second join buffer: %s"
        % (
            join_buffer_seconds,
            [[fragment.path.name for fragment in group] for group in groups],
        )
    )
    return groups


def _group_score(group):
    total_duration = 0.0
    duration_known = False
    for fragment in group:
        duration = getattr(fragment, "duration", None)
        if duration:
            total_duration += duration
            duration_known = True
    total_size = sum(fragment.size_bytes for fragment in group)
    newest = max(fragment.mtime for fragment in group)
    return duration_known, total_duration, total_size, newest


def choose_groups_to_keep(groups, keep_multiple):
    if keep_multiple or len(groups) <= 1:
        logger.debug(
            "Keeping all recording groups: %s"
            % [[fragment.path.name for fragment in group] for group in groups]
        )
        return list(groups)
    scored = []
    for group in groups:
        duration_known, total_duration, total_size, newest = _group_score(group)
        scored.append((duration_known, total_duration, total_size, newest, group))
    scored.sort(key=lambda item: (item[3], item[0], item[1], item[2]), reverse=True)
    logger.debug(
        "Selected latest recording group from scored candidates: %s"
        % [
            {
                "duration_known": item[0],
                "total_duration": item[1],
                "total_size": item[2],
                "newest_mtime": item[3],
                "group": [fragment.path.name for fragment in item[4]],
            }
            for item in scored
        ]
    )
    return [scored[0][4]]


def render_output_name(
    base_path,
    index,
    output_suffix_template,
    output_extension=None,
    replace_original_base_file=True,
):
    base_path = Path(base_path)
    output_extension = output_extension or base_path.suffix
    if index == 1:
        marker_suffix = REPAIRED_FILE_MARKER
    else:
        extra_suffix = (output_suffix_template or "{index}").format(index=index)
        marker_suffix = f"{REPAIRED_FILE_MARKER} - {extra_suffix}"
    return base_path.with_name(f"{base_path.stem} - {marker_suffix}{output_extension}")


def guess_output_paths(
    base_path,
    groups,
    keep_multiple,
    replace_original_base_file,
    output_suffix_template,
    output_profile="same_as_source",
    source_video_codec="h264",
):
    output_target = resolve_output_profile(
        output_profile=output_profile,
        source_extension=Path(base_path).suffix,
        source_video_codec=source_video_codec,
    )
    outputs = []
    if not keep_multiple and groups:
        outputs.append(
            render_output_name(
                base_path,
                1,
                output_suffix_template,
                output_extension=output_target["extension"],
                replace_original_base_file=replace_original_base_file,
            )
        )
        return outputs
    for index, _group in enumerate(groups, start=1):
        outputs.append(
            render_output_name(
                base_path,
                index,
                output_suffix_template,
                output_extension=output_target["extension"],
                replace_original_base_file=replace_original_base_file,
            )
        )
    return outputs


def _stream_signature(stream):
    return (
        stream.get("codec_name"),
        stream.get("width"),
        stream.get("height"),
        stream.get("avg_frame_rate"),
        stream.get("field_order"),
        stream.get("sample_rate"),
        stream.get("channel_layout"),
        stream.get("channels"),
    )


def _first_stream(probe, codec_type):
    for stream in probe.get("streams", []):
        if stream.get("codec_type") == codec_type:
            return stream
    return None


def _safe_int(value):
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def _safe_float(value):
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def ensure_fragment_profiles(fragment_probe_pairs):
    enriched = []
    for fragment, probe in fragment_probe_pairs:
        format_section = probe.get("format", {})
        duration = format_section.get("duration")
        try:
            duration = float(duration) if duration is not None else None
        except (TypeError, ValueError):
            duration = None
        setattr(fragment, "duration", duration)
        video_stream = _first_stream(probe, "video")
        if video_stream is None:
            continue
        enriched.append((fragment, probe))
    return enriched


def estimate_fragment_bitrates(fragment_probes):
    video_samples = []
    audio_samples = []
    for fragment, probe in fragment_probes:
        duration = (
            fragment.duration
            or _safe_float(probe.get("format", {}).get("duration"))
            or 0.0
        )
        if duration <= 0:
            continue
        video_stream = _first_stream(probe, "video") or {}
        audio_stream = _first_stream(probe, "audio") or {}

        video_bitrate = _safe_int(video_stream.get("bit_rate"))
        audio_bitrate = _safe_int(audio_stream.get("bit_rate"))
        format_bitrate = _safe_int(probe.get("format", {}).get("bit_rate"))

        if video_bitrate is None:
            estimated_total = format_bitrate or int(
                (fragment.size_bytes * 8) / duration
            )
            estimated_audio = audio_bitrate or 192000
            video_bitrate = max(estimated_total - estimated_audio, 500000)
        if audio_bitrate is None and audio_stream:
            estimated_total = format_bitrate or int(
                (fragment.size_bytes * 8) / duration
            )
            audio_bitrate = min(max(int(estimated_total * 0.08), 96000), 448000)

        video_samples.append((video_bitrate, duration))
        if audio_bitrate:
            audio_samples.append((audio_bitrate, duration))

    def weighted_average(samples, fallback):
        if not samples:
            return fallback
        total_weight = sum(weight for _value, weight in samples)
        if total_weight <= 0:
            return fallback
        return int(sum(value * weight for value, weight in samples) / total_weight)

    video_target = weighted_average(video_samples, 6_000_000)
    audio_target = weighted_average(audio_samples, 192_000)
    video_target = min(max(video_target, 500_000), 40_000_000)
    audio_target = min(max(audio_target, 96_000), 640_000)
    result = {
        "video_bitrate": video_target,
        "audio_bitrate": audio_target if audio_samples else None,
    }
    logger.debug(
        "Estimated bitrate targets from fragment probes: %s"
        % {
            "video_samples": video_samples,
            "audio_samples": audio_samples,
            "result": result,
        }
    )
    return result


def _target_container_for_profile(output_profile, source_extension):
    if output_profile == "h264_mkv":
        return "matroska", ".mkv"
    if output_profile == "h265_mkv":
        return "matroska", ".mkv"
    if str(source_extension).lower() == ".mkv":
        return "matroska", ".mkv"
    return "mpegts", ".ts"


def _target_video_codec_for_profile(output_profile, source_video_codec):
    normalized_source = (source_video_codec or "h264").lower()
    if output_profile == "h264_mkv":
        return "h264"
    if output_profile == "h265_mkv":
        return "hevc"
    if normalized_source in {"h264", "hevc"}:
        return normalized_source
    return "h264"


def resolve_output_profile(output_profile, source_extension, source_video_codec):
    container, extension = _target_container_for_profile(
        output_profile, source_extension
    )
    video_codec = _target_video_codec_for_profile(output_profile, source_video_codec)
    profile = {
        "output_profile": output_profile,
        "container": container,
        "extension": extension,
        "video_codec": video_codec,
    }
    logger.debug("Resolved output profile: %s" % profile)
    return profile


def estimate_target_video_bitrate(
    fragment_probes, source_video_codec, target_video_codec
):
    bitrate_targets = estimate_fragment_bitrates(fragment_probes)
    source_bitrate = bitrate_targets["video_bitrate"]
    source_codec = (source_video_codec or "h264").lower()
    target_codec = (target_video_codec or source_codec).lower()
    max_height = max(
        [
            _safe_int((_first_stream(probe, "video") or {}).get("height")) or 0
            for _fragment, probe in fragment_probes
        ]
        or [0]
    )

    reduction_factor = 1.0
    reason = "keeping source-like bitrate target"
    if source_codec == "h264" and target_codec == "hevc":
        if max_height >= 2160:
            reduction_factor = 0.50
        elif max_height >= 1080:
            reduction_factor = 0.55
        elif max_height >= 720:
            reduction_factor = 0.62
        else:
            reduction_factor = 0.72
        reason = "reducing target bitrate for H.264 to H.265 transcode"

    target_bitrate = int(source_bitrate * reduction_factor)
    if max_height >= 2160:
        min_bitrate = 4_000_000
    elif max_height >= 1080:
        min_bitrate = 1_800_000
    elif max_height >= 720:
        min_bitrate = 900_000
    else:
        min_bitrate = 500_000
    target_bitrate = max(target_bitrate, min_bitrate)
    result = {
        "source_video_bitrate": source_bitrate,
        "target_video_bitrate": target_bitrate,
        "audio_bitrate": bitrate_targets["audio_bitrate"],
        "source_video_codec": source_codec,
        "target_video_codec": target_codec,
        "max_height": max_height,
        "reduction_factor": reduction_factor,
        "reason": reason,
    }
    logger.debug("Estimated target bitrate decision: %s" % result)
    return result


def select_dominant_profile(fragment_probes):
    video_counter = Counter()
    audio_counter = Counter()
    video_profiles = {}
    audio_profiles = {}
    video_candidates = []
    audio_candidates = []
    all_equal = True
    first_video_signature = None
    first_audio_signature = None

    for fragment, probe in fragment_probes:
        weight = max(fragment.size_bytes, 1)
        video_stream = _first_stream(probe, "video")
        if not video_stream:
            continue
        video_signature = _stream_signature(video_stream)
        video_counter[video_signature] += weight
        video_profiles[video_signature] = video_stream
        video_duration = (
            _safe_float(video_stream.get("duration")) or fragment.duration or 0.0
        )
        video_candidates.append((video_duration, fragment.size_bytes, video_stream))
        if first_video_signature is None:
            first_video_signature = video_signature
        elif first_video_signature != video_signature:
            all_equal = False

        audio_stream = _first_stream(probe, "audio")
        if audio_stream:
            audio_signature = _stream_signature(audio_stream)
            audio_counter[audio_signature] += weight
            audio_profiles[audio_signature] = audio_stream
            audio_duration = (
                _safe_float(audio_stream.get("duration")) or fragment.duration or 0.0
            )
            audio_candidates.append((audio_duration, fragment.size_bytes, audio_stream))
            if first_audio_signature is None:
                first_audio_signature = audio_signature
            elif first_audio_signature != audio_signature:
                all_equal = False

    video_candidates.sort(key=lambda item: (item[0], item[1]), reverse=True)
    dominant_video = video_candidates[0][2]

    if audio_candidates:
        audio_candidates.sort(key=lambda item: (item[0], item[1]), reverse=True)
        dominant_audio = audio_candidates[0][2]
    else:
        dominant_audio = None

    logger.debug(
        "Selected dominant stream profile: %s"
        % {
            "video": dominant_video,
            "audio": dominant_audio,
            "all_equal": all_equal,
        }
    )
    return dominant_video, dominant_audio, all_equal


def _parse_frame_rate(frame_rate):
    if not frame_rate or frame_rate in {"0/0", "N/A"}:
        return None
    if "/" in frame_rate:
        numerator, denominator = frame_rate.split("/", 1)
        try:
            numerator = float(numerator)
            denominator = float(denominator)
            if denominator:
                return numerator / denominator
        except (TypeError, ValueError, ZeroDivisionError):
            return None
    try:
        return float(frame_rate)
    except (TypeError, ValueError):
        return None


def _list_ffmpeg_encoders():
    result = subprocess.run(
        ["ffmpeg", "-hide_banner", "-encoders"],
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode != 0:
        return ""
    output = result.stdout or ""
    logger.debug("Fetched ffmpeg encoders list successfully")
    return output


def detect_hardware_acceleration_methods(target_video_codec="h264"):
    available = []
    encoders_output = _list_ffmpeg_encoders()
    target_video_codec = (target_video_codec or "h264").lower()
    nvenc_encoder = "hevc_nvenc" if target_video_codec == "hevc" else "h264_nvenc"
    vaapi_encoder = "hevc_vaapi" if target_video_codec == "hevc" else "h264_vaapi"
    if (
        Path("/dev/nvidiactl").exists() or Path("/dev/nvidia0").exists()
    ) and nvenc_encoder in encoders_output:
        available.append("nvenc")
    if Path("/dev/dri").exists() and vaapi_encoder in encoders_output:
        available.append("vaapi")
    available.append("software")
    logger.debug(
        "Detected hardware acceleration methods in priority order for %s: %s"
        % (target_video_codec, available)
    )
    return available


def _build_stream_mapping(fragment_probes, container):
    first_probe = fragment_probes[0][1] if fragment_probes else {}
    streams = first_probe.get("streams", [])
    mapping = []
    subtitle_actions = []
    has_video_mapping = False

    for stream in streams:
        stream_type = stream.get("codec_type")
        stream_index = stream.get("index")
        codec_name = (stream.get("codec_name") or "").lower()
        if stream_index is None:
            continue
        if stream_type == "video":
            mapping.append(["-map", f"0:{stream_index}?"])
            has_video_mapping = True
        elif stream_type == "audio":
            mapping.append(["-map", f"0:{stream_index}?"])
        elif stream_type == "subtitle":
            if container != "matroska":
                continue
            if codec_name in {
                "subrip",
                "srt",
                "ass",
                "ssa",
                "webvtt",
                "hdmv_pgs_subtitle",
                "dvd_subtitle",
            }:
                mapping.append(["-map", f"0:{stream_index}?"])
                subtitle_actions.append("copy")
            elif codec_name in {"mov_text", "text"}:
                mapping.append(["-map", f"0:{stream_index}?"])
                subtitle_actions.append("srt")
            else:
                logger.debug(
                    "Skipping subtitle stream %s with codec '%s' because it is not safe for MKV output"
                    % (stream_index, codec_name)
                )
        elif stream_type == "attachment" and container == "matroska":
            mapping.append(["-map", f"0:{stream_index}?"])
        elif stream_type == "data" and container == "matroska":
            logger.debug(
                "Skipping data stream %s with codec '%s' for MKV output"
                % (stream_index, codec_name)
            )

    if not has_video_mapping:
        mapping.insert(0, ["-map", "0:v:0?"])
    logger.debug(
        "Built stream mapping for %s output: %s"
        % (
            container,
            {
                "mapping": mapping,
                "subtitle_actions": subtitle_actions,
            },
        )
    )
    return mapping, subtitle_actions


def build_ffmpeg_command(
    concat_file,
    output_file,
    fragment_probes,
    metadata_file=None,
    encoder_mode="software",
    output_profile="same_as_source",
):
    dominant_video, dominant_audio, _all_equal = select_dominant_profile(
        fragment_probes
    )
    output_target = resolve_output_profile(
        output_profile=output_profile,
        source_extension=fragment_probes[0][0].extension if fragment_probes else ".ts",
        source_video_codec=(
            dominant_video.get("codec_name") if dominant_video else "h264"
        ),
    )
    bitrate_targets = estimate_target_video_bitrate(
        fragment_probes,
        source_video_codec=(
            dominant_video.get("codec_name") if dominant_video else "h264"
        ),
        target_video_codec=output_target["video_codec"],
    )
    video_bitrate = bitrate_targets["target_video_bitrate"]
    audio_bitrate = bitrate_targets["audio_bitrate"]
    maxrate = int(video_bitrate * 1.10)
    bufsize = int(video_bitrate * 2.0)
    output_file = Path(output_file)
    command = [
        "ffmpeg",
        "-hide_banner",
        "-y",
        "-fflags",
        "+discardcorrupt+genpts",
        "-err_detect",
        "ignore_err",
        "-analyzeduration",
        "256M",
        "-probesize",
        "256M",
        "-fpsprobesize",
        "0",
        "-f",
        "concat",
        "-safe",
        "0",
        "-i",
        str(concat_file),
        "-progress",
        "pipe:1",
        "-nostats",
    ]
    if metadata_file:
        command += [
            "-i",
            str(metadata_file),
        ]

    command += ["-map_metadata", "0"]
    if metadata_file:
        command += ["-map_chapters", "1"]

    mapping, subtitle_actions = _build_stream_mapping(
        fragment_probes, output_target["container"]
    )
    for mapping_item in mapping:
        command += mapping_item

    target_video_codec = output_target["video_codec"]
    if encoder_mode == "nvenc":
        command += [
            "-c:v",
            "hevc_nvenc" if target_video_codec == "hevc" else "h264_nvenc",
            "-preset",
            "p5",
            "-rc",
            "vbr",
            "-b:v",
            str(video_bitrate),
            "-maxrate:v",
            str(maxrate),
            "-bufsize:v",
            str(bufsize),
            "-spatial_aq",
            "1",
            "-aq-strength",
            "8",
            "-bf",
            "2",
        ]
        if target_video_codec == "h264":
            command += ["-profile:v", "high"]
        else:
            command += ["-profile:v", "main"]
    elif encoder_mode == "vaapi":
        vaapi_device = (
            "/dev/dri/renderD128"
            if Path("/dev/dri/renderD128").exists()
            else "/dev/dri/card0"
        )
        command += [
            "-vaapi_device",
            vaapi_device,
            "-vf",
            "format=nv12,hwupload",
            "-c:v",
            "hevc_vaapi" if target_video_codec == "hevc" else "h264_vaapi",
            "-b:v",
            str(video_bitrate),
            "-maxrate:v",
            str(maxrate),
            "-bufsize:v",
            str(bufsize),
        ]
        if target_video_codec == "h264":
            command += ["-profile:v", "high"]
        else:
            command += ["-profile:v", "main"]
    else:
        command += [
            "-c:v",
            "libx265" if target_video_codec == "hevc" else "libx264",
            "-preset",
            "medium",
            "-b:v",
            str(video_bitrate),
            "-maxrate:v",
            str(maxrate),
            "-bufsize:v",
            str(bufsize),
        ]
        if target_video_codec == "hevc":
            command += [
                "-tag:v",
                "hvc1",
                "-x265-params",
                "repeat-headers=1:hrd=1",
            ]
        else:
            command += [
                "-profile:v",
                "high",
                "-x264-params",
                "nal-hrd=vbr:force-cfr=1",
            ]
    if encoder_mode != "vaapi":
        command += ["-pix_fmt", "yuv420p"]

    frame_rate = _parse_frame_rate(dominant_video.get("avg_frame_rate"))
    if frame_rate:
        command += ["-r", f"{frame_rate:.6f}"]

    if dominant_audio:
        audio_codec = dominant_audio.get("codec_name") or "aac"
        if audio_codec in {"ac3", "eac3", "mp2"}:
            command += ["-c:a", audio_codec]
        elif audio_codec == "mp3":
            command += ["-c:a", "libmp3lame"]
        else:
            command += ["-c:a", "aac"]
        sample_rate = dominant_audio.get("sample_rate")
        channels = dominant_audio.get("channels")
        if audio_bitrate:
            command += ["-b:a", str(audio_bitrate)]
        if sample_rate:
            command += ["-ar", str(sample_rate)]
        if channels:
            command += ["-ac", str(channels)]

    if subtitle_actions:
        if all(action == "copy" for action in subtitle_actions):
            command += ["-c:s", "copy"]
        else:
            command += ["-c:s", "srt"]

    command += [
        "-max_muxing_queue_size",
        "4096",
        "-max_interleave_delta",
        "0",
        "-avoid_negative_ts",
        "make_zero",
    ]
    if output_target["container"] == "mpegts":
        command += [
            "-muxdelay",
            "0",
            "-muxpreload",
            "0",
            "-mpegts_flags",
            "+resend_headers",
            "-f",
            "mpegts",
            str(output_file),
        ]
    else:
        command += [
            "-f",
            "matroska",
            str(output_file),
        ]
    logger.debug(
        "Built ffmpeg command configuration: %s"
        % {
            "output_profile": output_profile,
            "container": output_target["container"],
            "encoder_mode": encoder_mode,
            "video_codec": target_video_codec,
            "video_bitrate": video_bitrate,
            "audio_bitrate": audio_bitrate,
            "maxrate": maxrate,
            "bufsize": bufsize,
            "output_file": str(output_file),
            "metadata_file": str(metadata_file) if metadata_file else None,
            "command": format_command_for_logs(command),
        }
    )
    return command


def merge_chapters(fragment_probes):
    merged = []
    offset_seconds = 0.0
    chapter_index = 1
    for fragment, probe in fragment_probes:
        chapters = probe.get("chapters", [])
        for chapter in chapters:
            try:
                start = float(chapter.get("start_time", 0))
                end = float(chapter.get("end_time", 0))
            except (TypeError, ValueError):
                continue
            if end <= start:
                continue
            tags = dict(chapter.get("tags") or {})
            tags.setdefault("title", f"Chapter {chapter_index}")
            merged.append(
                {
                    "start": start + offset_seconds,
                    "end": end + offset_seconds,
                    "tags": tags,
                }
            )
            chapter_index += 1
        offset_seconds += getattr(fragment, "duration", 0.0) or 0.0
    logger.debug("Merged chapter metadata entries: %s" % merged)
    return merged


def write_ffmetadata(path, chapters):
    lines = [";FFMETADATA1"]
    for chapter in chapters:
        start_ms = max(int(chapter["start"] * 1000), 0)
        end_ms = max(int(chapter["end"] * 1000), start_ms + 1)
        lines.extend(
            [
                "[CHAPTER]",
                "TIMEBASE=1/1000",
                f"START={start_ms}",
                f"END={end_ms}",
            ]
        )
        for key, value in (chapter.get("tags") or {}).items():
            sanitized = str(value).replace("\n", " ").strip()
            lines.append(f"{key}={sanitized}")
    Path(path).write_text("\n".join(lines) + "\n", encoding="utf-8")


def format_command_for_logs(command):
    return " ".join(shlex.quote(str(part)) for part in command)
