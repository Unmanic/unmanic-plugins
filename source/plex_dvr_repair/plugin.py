#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
plugins.plex_dvr_repair.plugin.py

Written by:               Josh.5 <jsunnex@gmail.com>
Date:                     18 Mar 2026

Copyright:
    Copyright (C) 2026 Josh Sunnex

    This program is free software: you can redistribute it and/or modify it under the terms of the GNU General
    Public License as published by the Free Software Foundation, version 3.

    This program is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the
    implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License
    for more details.

    You should have received a copy of the GNU General Public License along with this program.
    If not, see <https://www.gnu.org/licenses/>.
"""

import json
import logging
import os
import re
import shutil
import subprocess
import tempfile
from pathlib import Path

from plex_dvr_repair.lib.logic import (
    COPY_FILE_STALE_MINUTES,
    REPAIRED_FILE_MARKER,
    build_ffmpeg_command,
    choose_groups_to_keep,
    detect_hardware_acceleration_methods,
    discover_candidate_fragments,
    ensure_fragment_profiles,
    find_active_sidecars,
    format_command_for_logs,
    group_fragments_by_recording_window,
    guess_output_paths,
    is_candidate_extension,
    is_copy_fragment_name,
    is_recently_modified,
    is_repaired_output_name,
    merge_chapters,
    parse_fragment_path,
    write_ffmetadata,
)
from unmanic.libs.unplugins.child_process import PluginChildProcess
from unmanic.libs.unplugins.settings import PluginSettings

logger = logging.getLogger("Unmanic.Plugin.plex_dvr_repair")
PLUGIN_ID = "plex_dvr_repair"
TASK_STATE_KEY = "repair_job_manifest"
FFMPEG_DIAGNOSTIC_PATTERNS = {
    "corrupt_packets": [
        re.compile(r"packet corrupt", re.IGNORECASE),
        re.compile(r"corrupt", re.IGNORECASE),
        re.compile(r"discarding", re.IGNORECASE),
    ],
    "decode_errors": [
        re.compile(r"error while decoding", re.IGNORECASE),
        re.compile(r"invalid data found", re.IGNORECASE),
        re.compile(r"missing picture", re.IGNORECASE),
        re.compile(r"concealing", re.IGNORECASE),
    ],
    "timestamp_warnings": [
        re.compile(r"non monotonically increasing dts", re.IGNORECASE),
        re.compile(r"backward in time", re.IGNORECASE),
        re.compile(r"timestamp", re.IGNORECASE),
        re.compile(r"dts", re.IGNORECASE),
        re.compile(r"pts", re.IGNORECASE),
    ],
    "muxing_warnings": [
        re.compile(r"mux", re.IGNORECASE),
        re.compile(r"interleav", re.IGNORECASE),
        re.compile(r"queue", re.IGNORECASE),
    ],
    "audio_warnings": [
        re.compile(r"\baudio\b", re.IGNORECASE),
        re.compile(r"\baac\b", re.IGNORECASE),
    ],
    "video_warnings": [
        re.compile(r"\bvideo\b", re.IGNORECASE),
        re.compile(r"\bh264\b", re.IGNORECASE),
        re.compile(r"\bhevc\b", re.IGNORECASE),
    ],
}


class Settings(PluginSettings):
    settings = {
        "ignore_recently_modified_minutes": 120,
        "use_hardware_acceleration": False,
        "output_profile": "same_as_source",
    }

    def __init__(self, *args, **kwargs):
        super(Settings, self).__init__(*args, **kwargs)
        self.form_settings = {
            "ignore_recently_modified_minutes": {
                "label": "Ignore Files By Modification Time",
                "description": "Ignore files that have been modified in the configured number of minutes. This includes the recording, any copy fragments, and related Plex post-processing files.",
            },
            "use_hardware_acceleration": {
                "label": "Try hardware-accelerated encoding before falling back to software",
            },
            "output_profile": {
                "label": "Select the output video codec and container profile",
                "input_type": "select",
                "select_options": [
                    {
                        "value": "same_as_source",
                        "label": "Same as Source",
                    },
                    {"value": "h264_mkv", "label": "H.264 MKV"},
                    {"value": "h265_mkv", "label": "H.265 MKV"},
                ],
            },
        }


def load_settings(data):
    if data.get("library_id"):
        settings = Settings(library_id=data.get("library_id"))
    else:
        settings = Settings()
    settings_dict = {key: settings.get_setting(key) for key in Settings.settings}
    if not settings_dict.get("ignore_recently_modified_minutes"):
        legacy_value = settings.get_setting("sidecar_grace_period_minutes")
        if legacy_value:
            settings_dict["ignore_recently_modified_minutes"] = legacy_value
    logger.debug("Loaded plugin settings: %s", settings_dict)
    return settings_dict


def probe_json(path):
    command = [
        "ffprobe",
        "-v",
        "error",
        "-print_format",
        "json",
        "-show_format",
        "-show_streams",
        "-show_chapters",
        str(path),
    ]
    result = subprocess.run(command, capture_output=True, text=True, check=False)
    if result.returncode != 0:
        raise RuntimeError(result.stderr.strip() or f"ffprobe failed for '{path}'")
    return json.loads(result.stdout or "{}")


def validate_output(output_path):
    probe = probe_json(output_path)
    video_streams = [
        stream
        for stream in probe.get("streams", [])
        if stream.get("codec_type") == "video"
    ]
    if not video_streams:
        raise RuntimeError(
            f"Output validation failed for '{output_path}': no video stream detected"
        )
    return probe


def repaired_metadata_for_path(path, file_metadata=None):
    if file_metadata and hasattr(file_metadata, "get"):
        try:
            metadata = file_metadata.get()
            if metadata.get("status") == "repaired" or metadata.get("repaired") is True:
                return metadata
        except Exception as exc:
            logger.debug("Unable to read file metadata for '%s': %s", path, exc)
    return {}


def _to_float(value):
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def summarize_probe(probe_data):
    streams = probe_data.get("streams", [])
    format_data = probe_data.get("format", {})
    video_streams = [
        stream for stream in streams if stream.get("codec_type") == "video"
    ]
    audio_streams = [
        stream for stream in streams if stream.get("codec_type") == "audio"
    ]
    subtitle_streams = [
        stream for stream in streams if stream.get("codec_type") == "subtitle"
    ]
    data_streams = [stream for stream in streams if stream.get("codec_type") == "data"]
    video_stream = video_streams[0] if video_streams else {}
    audio_stream = audio_streams[0] if audio_streams else {}
    format_duration = _to_float(format_data.get("duration"))
    video_start_time = _to_float(video_stream.get("start_time"))
    audio_start_time = _to_float(audio_stream.get("start_time"))
    return {
        "container": format_data.get("format_name"),
        "duration": format_duration,
        "duration_present": format_duration is not None,
        "bit_rate": format_data.get("bit_rate"),
        "video": {
            "codec": video_stream.get("codec_name"),
            "width": video_stream.get("width"),
            "height": video_stream.get("height"),
            "pix_fmt": video_stream.get("pix_fmt"),
            "frame_rate": video_stream.get("avg_frame_rate"),
            "start_time": video_start_time,
        },
        "audio": {
            "codec": audio_stream.get("codec_name"),
            "channels": audio_stream.get("channels"),
            "sample_rate": audio_stream.get("sample_rate"),
            "bit_rate": audio_stream.get("bit_rate"),
            "start_time": audio_start_time,
        },
        "stream_counts": {
            "video": len(video_streams),
            "audio": len(audio_streams),
            "subtitle": len(subtitle_streams),
            "data": len(data_streams),
            "chapters": len(probe_data.get("chapters", [])),
        },
        "health_flags": {
            "missing_duration_metadata": format_duration is None,
            "negative_video_start_time": bool(
                video_start_time is not None and video_start_time < 0
            ),
            "negative_audio_start_time": bool(
                audio_start_time is not None and audio_start_time < 0
            ),
        },
    }


def build_fragment_group_summary(group):
    return [
        {
            "name": fragment.path.name,
            "mtime": fragment.mtime,
            "duration": fragment.duration,
            "size_bytes": fragment.size_bytes,
            "copy_number": fragment.copy_number,
        }
        for fragment in group
    ]


def build_input_diagnostics(job_state, fragments_with_probe):
    selected_group = job_state["selected_group"]
    total_duration = sum(
        fragment.duration or 0.0 for fragment, _probe in fragments_with_probe
    )
    total_size = sum(
        fragment.size_bytes or 0 for fragment, _probe in fragments_with_probe
    )
    primary_probe = fragments_with_probe[0][1] if fragments_with_probe else {}
    return {
        "recording_attempt_count": len(job_state["all_groups"]),
        "selected_fragment_count": len(selected_group),
        "selected_fragments": build_fragment_group_summary(selected_group),
        "all_recording_groups": [
            build_fragment_group_summary(group) for group in job_state["all_groups"]
        ],
        "selected_group_totals": {
            "duration": total_duration,
            "size_bytes": total_size,
        },
        "source_probe_summary": summarize_probe(primary_probe),
        "health_flags": {
            "fragmented_input": len(selected_group) > 1,
            "multiple_recording_attempts_detected": len(job_state["all_groups"]) > 1,
        },
    }


def create_ffmpeg_diagnostics():
    return {
        "counts": {
            "corrupt_packets": 0,
            "decode_errors": 0,
            "timestamp_warnings": 0,
            "muxing_warnings": 0,
            "audio_warnings": 0,
            "video_warnings": 0,
        },
        "examples": {
            "corrupt_packets": [],
            "decode_errors": [],
            "timestamp_warnings": [],
            "muxing_warnings": [],
            "audio_warnings": [],
            "video_warnings": [],
        },
    }


def collect_ffmpeg_diagnostic_line(line, diagnostics):
    for category, patterns in FFMPEG_DIAGNOSTIC_PATTERNS.items():
        if any(pattern.search(line) for pattern in patterns):
            diagnostics["counts"][category] += 1
            examples = diagnostics["examples"][category]
            if len(examples) < 5 and line not in examples:
                examples.append(line)


def build_repair_summary(input_diag, repair_diag, output_diag):
    findings = []
    if input_diag["health_flags"]["multiple_recording_attempts_detected"]:
        findings.append("multiple recording attempts detected")
    if input_diag["health_flags"]["fragmented_input"]:
        findings.append("selected recording attempt required stitching")
    if input_diag["source_probe_summary"]["health_flags"]["missing_duration_metadata"]:
        findings.append("input duration metadata missing")
    if repair_diag["ffmpeg_findings"]["counts"]["corrupt_packets"] > 0:
        findings.append("ffmpeg encountered corrupt packets")
    if repair_diag["ffmpeg_findings"]["counts"]["decode_errors"] > 0:
        findings.append("ffmpeg encountered decode errors")
    if repair_diag["ffmpeg_findings"]["counts"]["timestamp_warnings"] > 0:
        findings.append("ffmpeg encountered timestamp warnings")
    output_findings = []
    if output_diag["probe_summary"]["duration_present"]:
        output_findings.append("output duration metadata present")
    if not output_diag["probe_summary"]["health_flags"]["negative_video_start_time"]:
        output_findings.append("video timestamps do not start negative")
    if not output_diag["probe_summary"]["health_flags"]["negative_audio_start_time"]:
        output_findings.append("audio timestamps do not start negative")
    return {
        "input_findings": findings,
        "output_findings": output_findings,
    }


def execute_ffmpeg_command(
    command,
    total_duration,
    percent_start,
    percent_span,
    log_queue=None,
    prog_queue=None,
):
    message = f"Running command: {format_command_for_logs(command)}"
    logger.info(message)
    if log_queue is not None:
        log_queue.put(message)
    debug_message = (
        f"ffmpeg progress tracking configured with total_duration={total_duration}, "
        f"percent_start={percent_start}, percent_span={percent_span}"
    )
    logger.debug(debug_message)
    if log_queue is not None:
        log_queue.put(debug_message)
    process = subprocess.Popen(
        command,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        universal_newlines=True,
        errors="replace",
    )
    last_percent = None
    diagnostics = create_ffmpeg_diagnostics()
    while True:
        line = process.stdout.readline()
        if line:
            stripped = line.rstrip()
            if "=" in stripped:
                key, value = stripped.split("=", 1)
                if key == "out_time_us":
                    try:
                        out_time_seconds = int(value) / 1_000_000
                        ratio = (
                            0.0
                            if total_duration <= 0
                            else min(out_time_seconds / total_duration, 1.0)
                        )
                        percent = min(
                            percent_start + int(ratio * percent_span),
                            percent_start + percent_span,
                        )
                        if prog_queue is not None and percent != last_percent:
                            prog_queue.put(percent)
                            last_percent = percent
                    except (TypeError, ValueError):
                        pass
                elif key == "progress":
                    if value == "end" and prog_queue is not None:
                        prog_queue.put(percent_start + percent_span)
                elif key in {"frame", "fps", "speed", "total_size", "out_time"}:
                    pass
                    # Uncomment below to log the ffmpeg command progress
                    # message = f"ffmpeg {key}={value}"
                    # logger.debug(message)
                    # if log_queue is not None:
                    #     log_queue.put(message)
            elif stripped:
                logger.debug(stripped)
                if log_queue is not None:
                    log_queue.put(stripped)
                collect_ffmpeg_diagnostic_line(stripped, diagnostics)
        if line == "" and process.poll() is not None:
            break
    if process.returncode != 0:
        raise RuntimeError(
            f"Command failed with exit code {process.returncode}: {format_command_for_logs(command)}"
        )
    return diagnostics


def execute_ffmpeg_with_fallback(
    commands,
    total_duration,
    percent_start,
    percent_span,
    log_queue=None,
    prog_queue=None,
):
    last_error = None
    message = f"Prepared ffmpeg fallback chain: {[encoder_mode for encoder_mode, _command in commands]}"
    logger.debug(message)
    if log_queue is not None:
        log_queue.put(message)
    for encoder_mode, command in commands:
        try:
            message = f"Attempting ffmpeg repair with encoder mode '{encoder_mode}'"
            logger.info(message)
            if log_queue is not None:
                log_queue.put(message)
            diagnostics = execute_ffmpeg_command(
                command,
                total_duration=total_duration,
                percent_start=percent_start,
                percent_span=percent_span,
                log_queue=log_queue,
                prog_queue=prog_queue,
            )
            return encoder_mode, diagnostics
        except Exception as exc:
            last_error = exc
            message = (
                f"Encoder mode '{encoder_mode}' failed, trying next fallback: {exc}"
            )
            logger.warning(message)
            if log_queue is not None:
                log_queue.put(message)
    raise RuntimeError(f"All ffmpeg encoder attempts failed: {last_error}")


def commit_output(staged_path, final_path, log_queue=None):
    final_path = Path(final_path)
    staged_path = Path(staged_path)
    final_path.parent.mkdir(parents=True, exist_ok=True)
    os.replace(staged_path, final_path)
    message = f"Committed repaired output '{final_path.name}'"
    logger.info(message)
    if log_queue is not None:
        log_queue.put(message)


def build_cache_output_path(primary_cache_path, final_output_path):
    primary_cache_path = Path(primary_cache_path)
    final_output_path = Path(final_output_path)
    return primary_cache_path.with_suffix(final_output_path.suffix)


def build_repaired_destination_path(destination_abspath):
    destination_abspath = Path(destination_abspath)
    return destination_abspath.with_name(
        f"{destination_abspath.stem} - {REPAIRED_FILE_MARKER}{destination_abspath.suffix}"
    )


def build_job_state(base_path, settings_dict, log_queue=None):
    base_fragment = parse_fragment_path(base_path)
    if base_fragment is None:
        logger.debug("Skipping unsupported filename '%s'", base_path.name)
        if log_queue is not None:
            log_queue.put(f"Skipping unsupported filename '{base_path.name}'")
        return None
    if base_fragment.is_copy:
        logger.debug(
            "Skipping copy fragment worker invocation for '%s'", base_path.name
        )
        if log_queue is not None:
            log_queue.put(
                f"Skipping copy fragment worker invocation for '{base_path.name}'"
            )
        return None
    if not is_candidate_extension(base_fragment.extension):
        logger.debug(
            "Skipping unsupported source extension '%s'", base_fragment.extension
        )
        if log_queue is not None:
            log_queue.put(
                f"Skipping unsupported source extension '{base_fragment.extension}'"
            )
        return None
    if is_repaired_output_name(base_path.name):
        logger.debug("Skipping already repaired filename '%s'", base_path.name)
        if log_queue is not None:
            log_queue.put(f"Skipping already repaired filename '{base_path.name}'")
        return None

    candidates = discover_candidate_fragments(base_path)
    recent_fragments = [
        fragment
        for fragment in candidates
        if is_recently_modified(fragment, COPY_FILE_STALE_MINUTES)
    ]
    if recent_fragments:
        message = f"Skipping because one or more fragments were modified within the last {COPY_FILE_STALE_MINUTES} minutes"
        logger.info(message)
        if log_queue is not None:
            log_queue.put(message)
        return None

    sidecars = find_active_sidecars(
        base_path,
        grace_minutes=int(settings_dict.get("ignore_recently_modified_minutes", 120)),
        ignore_when_sidecars_exist=True,
    )
    if sidecars:
        sidecar_list = ", ".join(sidecar.name for sidecar in sidecars)
        message = (
            f"Skipping because Plex sidecar indicates post-processing: {sidecar_list}"
        )
        logger.info(message)
        if log_queue is not None:
            log_queue.put(message)
        return None

    fragment_probe_pairs = []
    for fragment in candidates:
        try:
            probe_data = probe_json(fragment.path)
        except Exception as exc:
            message = f"Failed to probe candidate fragment '{fragment.path.name}' before grouping: {exc}"
            logger.warning(message)
            if log_queue is not None:
                log_queue.put(message)
            probe_data = {}
        fragment_probe_pairs.append((fragment, probe_data))
    fragment_probe_pairs = ensure_fragment_profiles(fragment_probe_pairs)
    candidates = [fragment for fragment, _probe in fragment_probe_pairs]
    if not candidates:
        raise RuntimeError(f"No probeable fragments remained for '{base_path.name}'")

    filtered_groups = group_fragments_by_recording_window(candidates)

    message = (
        f"Grouped {len(candidates)} files into {len(filtered_groups)} recording groups"
    )
    logger.info(message)
    if log_queue is not None:
        log_queue.put(message)
    for fragment, _probe in fragment_probe_pairs:
        if fragment.duration is None:
            logger.debug(
                "Fragment '%s' has no known duration during best-group scoring.",
                fragment.path.name,
            )
    selected_groups = choose_groups_to_keep(
        filtered_groups,
        keep_multiple=False,
    )
    output_profile = settings_dict.get("output_profile", "same_as_source")
    source_video_codec = None
    for _fragment, probe_data in fragment_probe_pairs:
        for stream in probe_data.get("streams", []):
            if stream.get("codec_type") == "video":
                source_video_codec = stream.get("codec_name") or "h264"
                break
        if source_video_codec:
            break
    source_video_codec = source_video_codec or "h264"
    output_paths = guess_output_paths(
        base_path,
        selected_groups,
        keep_multiple=False,
        replace_original_base_file=True,
        output_suffix_template="stitched {index}",
        output_profile=output_profile,
        source_video_codec=source_video_codec,
    )
    selected_group = selected_groups[0]
    output_path = output_paths[0]
    message = "Job state prepared with selected_group=%s output_path=%s" % (
        [fragment.path.name for fragment in selected_group],
        str(output_path),
    )
    logger.debug(message)
    if log_queue is not None:
        log_queue.put(message)
    return {
        "base_fragment": base_fragment,
        "all_groups": filtered_groups,
        "selected_group": selected_group,
        "output_path": output_path,
    }


def stage_group_output(
    temp_dir, group, final_output_path, group_index, settings_dict, log_queue=None
):
    fragments_with_probe = []
    for fragment in group:
        try:
            probe_data = probe_json(fragment.path)
            fragments_with_probe.append((fragment, probe_data))
        except Exception as exc:
            message = f"Failed to probe fragment '{fragment.path.name}': {exc}"
            logger.warning(message)
            if log_queue is not None:
                log_queue.put(message)

    fragments_with_probe = ensure_fragment_profiles(fragments_with_probe)
    if not fragments_with_probe:
        raise RuntimeError(f"No probeable fragments remained for group {group_index}")
    message = "Stage group %s probe summary: %s" % (
        group_index,
        [
            {
                "name": fragment.path.name,
                "duration": fragment.duration,
                "size_bytes": fragment.size_bytes,
            }
            for fragment, _probe in fragments_with_probe
        ],
    )
    logger.debug(message)
    if log_queue is not None:
        log_queue.put(message)

    concat_file = Path(temp_dir) / f"group-{group_index}.concat.txt"
    concat_lines = []
    for fragment, _probe in fragments_with_probe:
        escaped = str(fragment.path).replace("'", "'\\''")
        concat_lines.append(f"file '{escaped}'\n")
    concat_file.write_text("".join(concat_lines), encoding="utf-8")
    message = f"Building ffmpeg concat list for group {group_index}"
    logger.info(message)
    if log_queue is not None:
        log_queue.put(message)

    chapter_entries = merge_chapters(fragments_with_probe)
    metadata_file = None
    if chapter_entries:
        metadata_file = Path(temp_dir) / f"group-{group_index}.ffmetadata.txt"
        write_ffmetadata(metadata_file, chapter_entries)
        message = (
            f"Preserving {len(chapter_entries)} chapter markers from source fragments"
        )
        logger.info(message)
        if log_queue is not None:
            log_queue.put(message)

    staged_output = Path(temp_dir) / f"group-{group_index}.stitched.ts"
    staged_output = staged_output.with_suffix(Path(final_output_path).suffix)
    output_profile = settings_dict.get("output_profile", "same_as_source")
    target_codec = "hevc" if output_profile == "h265_mkv" else None
    if target_codec is None and fragments_with_probe:
        video_stream = next(
            (
                stream
                for stream in fragments_with_probe[0][1].get("streams", [])
                if stream.get("codec_type") == "video"
            ),
            {},
        )
        target_codec = video_stream.get("codec_name") or "h264"
    encoder_modes = ["software"]
    if bool(settings_dict.get("use_hardware_acceleration", False)):
        encoder_modes = detect_hardware_acceleration_methods(target_codec)
    message = f"Group {group_index} encoder candidates: {encoder_modes}"
    logger.debug(message)
    if log_queue is not None:
        log_queue.put(message)
    commands = [
        (
            encoder_mode,
            build_ffmpeg_command(
                concat_file=concat_file,
                output_file=staged_output,
                fragment_probes=fragments_with_probe,
                metadata_file=metadata_file,
                encoder_mode=encoder_mode,
                output_profile=output_profile,
            ),
        )
        for encoder_mode in encoder_modes
    ]
    total_duration = sum(
        fragment.duration or 0.0 for fragment, _probe in fragments_with_probe
    )
    message = f"Group {group_index} estimated stitched duration={total_duration} final_output='{final_output_path}'"
    logger.debug(message)
    if log_queue is not None:
        log_queue.put(message)
    return staged_output, commands, total_duration


def run_repair_job(
    file_in,
    primary_cache_output,
    settings_dict,
    task_id=None,
    log_queue=None,
    prog_queue=None,
):
    base_path = Path(file_in)
    primary_cache_output = Path(primary_cache_output)
    primary_cache_output.parent.mkdir(parents=True, exist_ok=True)
    logger.debug("Starting repair job for '%s'", base_path)
    if log_queue is not None:
        log_queue.put(f"Starting repair job for '{base_path}'")
    job_state = build_job_state(base_path, settings_dict, log_queue=log_queue)
    if job_state is None:
        if prog_queue is not None:
            prog_queue.put(100)
        return

    selected_group = job_state["selected_group"]
    cache_output_path = build_cache_output_path(
        primary_cache_output, job_state["output_path"]
    )
    temp_dir = Path(
        tempfile.mkdtemp(
            prefix=f".{PLUGIN_ID}.{task_id or 'task'}.",
            dir=str(primary_cache_output.parent),
        )
    )
    staged_output = None

    try:
        message = "Processing group 1/1 with fragments=%s" % (
            [fragment.path.name for fragment in selected_group],
        )
        logger.debug(message)
        if log_queue is not None:
            log_queue.put(message)
        if prog_queue is not None:
            prog_queue.put(0)
        staged_output, commands, total_duration = stage_group_output(
            temp_dir=temp_dir,
            group=selected_group,
            final_output_path=cache_output_path,
            group_index=1,
            settings_dict=settings_dict,
            log_queue=log_queue,
        )
        fragments_with_probe = ensure_fragment_profiles(
            [(fragment, probe_json(fragment.path)) for fragment in selected_group]
        )
        input_diagnostics = build_input_diagnostics(job_state, fragments_with_probe)
        if log_queue is not None:
            log_queue.put(f"Repair diagnostics (input): {input_diagnostics}")
        encoder_mode, ffmpeg_findings = execute_ffmpeg_with_fallback(
            commands,
            total_duration=total_duration,
            percent_start=0,
            percent_span=90,
            log_queue=log_queue,
            prog_queue=prog_queue,
        )
        output_probe = validate_output(staged_output)
        output_format = output_probe.get("format", {})
        output_diagnostics = {
            "probe_summary": summarize_probe(output_probe),
        }
        repair_diagnostics = {
            "encoder_mode": encoder_mode,
            "fallback_used": encoder_mode != commands[0][0],
            "ffmpeg_findings": ffmpeg_findings,
        }
        summary = build_repair_summary(
            input_diagnostics, repair_diagnostics, output_diagnostics
        )
        message = (
            f"Successfully stitched group 1 with encoder '{encoder_mode}' -> "
            f"{cache_output_path.name}"
        )
        logger.info(message)
        if log_queue is not None:
            log_queue.put(message)
        message = "Group 1 result: %s" % (
            {
                "path": str(cache_output_path),
                "group_index": 1,
                "encoder_mode": encoder_mode,
                "source_fragment_count": len(selected_group),
                "output_bitrate": output_format.get("bit_rate"),
                "output_duration": output_format.get("duration"),
            },
        )
        logger.debug(message)
        if log_queue is not None:
            log_queue.put(message)
        if log_queue is not None:
            log_queue.put(f"Repair diagnostics (process): {repair_diagnostics}")
            log_queue.put(f"Repair diagnostics (output): {output_diagnostics}")
            log_queue.put(f"Repair diagnostics (summary): {summary}")
        commit_output(staged_output, cache_output_path, log_queue=log_queue)
        if prog_queue is not None:
            prog_queue.put(100)
    except Exception:
        raise
    finally:
        if temp_dir.exists() and staged_output is not None:
            shutil.rmtree(temp_dir, ignore_errors=True)


def on_library_management_file_test(data, file_metadata=None):
    """
    Runner function - enables additional actions during the library management file tests.

    The 'data' object argument includes:
        library_id                      - The library that the current task is associated with
        path                            - String containing the full path to the file being tested.
        issues                          - List of currently found issues for not processing the file.
        add_file_to_pending_tasks       - Boolean, is the file currently marked to be added to the queue for processing.
        priority_score                  - Integer, an additional score that can be added to set the position of the new task in the task queue.
        shared_info                     - Dictionary, information provided by previous plugin runners. This can be appended to for subsequent runners.

    :param data:
    :return:
    """
    settings_dict = load_settings(data)

    abspath = Path(data.get("path"))
    logger.debug("Library scan evaluating '%s'", abspath)
    existing_metadata = repaired_metadata_for_path(abspath, file_metadata=file_metadata)
    if existing_metadata:
        data["add_file_to_pending_tasks"] = False
        logger.debug(
            "File '%s' does not need repair because repaired metadata already exists.",
            abspath,
        )
        data["issues"].append(
            {
                "id": "Plex DVR Repair",
                "message": f"Skipping '{abspath.name}' because it has already been repaired.",
            }
        )
        return

    fragment = parse_fragment_path(abspath)
    if fragment is None:
        logger.debug(
            "File '%s' does not need repair because it does not match a supported Plex DVR recording filename pattern.",
            abspath,
        )
        return

    if not is_candidate_extension(abspath.suffix):
        logger.debug(
            "File '%s' does not need repair because it is not a supported Plex DVR source extension.",
            abspath,
        )
        return

    if is_repaired_output_name(abspath.name):
        data["add_file_to_pending_tasks"] = False
        logger.debug(
            "File '%s' does not need repair because it is already a repaired output.",
            abspath,
        )
        data["issues"].append(
            {
                "id": "Plex DVR Repair",
                "message": f"Skipping repaired output '{abspath.name}'.",
            }
        )
        return

    if fragment.is_copy:
        data["add_file_to_pending_tasks"] = False
        logger.debug(
            "File '%s' is a copy fragment, so the base recording will be considered instead.",
            abspath,
        )
        data["issues"].append(
            {
                "id": "Plex DVR Repair",
                "message": f"Skipping Plex DVR copy fragment '{abspath.name}'. The base recording will be processed instead.",
            }
        )
        return

    candidates = discover_candidate_fragments(abspath)

    recent_candidates = [
        candidate
        for candidate in candidates
        if is_recently_modified(candidate, COPY_FILE_STALE_MINUTES)
    ]
    if recent_candidates:
        data["add_file_to_pending_tasks"] = False
        logger.debug(
            "File '%s' is being skipped for now because one or more fragments are still recent.",
            abspath,
        )
        data["issues"].append(
            {
                "id": "Plex DVR Repair",
                "message": f"Skipping '{abspath.name}' because one or more recording fragments are still recent.",
            }
        )
        return

    active_sidecars = find_active_sidecars(
        abspath,
        grace_minutes=int(settings_dict.get("ignore_recently_modified_minutes", 120)),
        ignore_when_sidecars_exist=True,
    )
    if active_sidecars:
        data["add_file_to_pending_tasks"] = False
        logger.debug(
            "File '%s' is being skipped for now because active Plex sidecars were detected.",
            abspath,
        )
        data["issues"].append(
            {
                "id": "Plex DVR Repair",
                "message": f"Skipping '{abspath.name}' because Plex sidecar files indicate post-processing is still active.",
            }
        )
        return

    copies = [candidate for candidate in candidates if candidate.is_copy]
    if not copies:
        data["add_file_to_pending_tasks"] = True
        logger.debug(
            "File '%s' should be repaired because it is an unrepaired Plex DVR transport stream with no copy fragments.",
            abspath,
        )
        return

    data["add_file_to_pending_tasks"] = True
    logger.debug(
        "File '%s' should be repaired because the latest recording attempt can be stitched from the available fragments.",
        abspath,
    )


def on_worker_process(data, task_data_store=None, file_metadata=None):
    """
    Runner function - enables additional configured processing jobs during the worker stages of a task.

    The 'data' object argument includes:
        task_id                 - Integer, unique identifier of the task.
        worker_log              - Array, the log lines that are being tailed by the frontend. Can be left empty.
        library_id              - Number, the library that the current task is associated with.
        exec_command            - Array, a subprocess command that Unmanic should execute. Can be empty.
        current_command         - Array, shared list for updating the worker's "current command" text in the UI (last entry wins).
        command_progress_parser - Function, a function that Unmanic can use to parse the STDOUT of the command to collect progress stats. Can be empty.
        file_in                 - String, the source file to be processed by the command.
        file_out                - String, the destination that the command should output (may be the same as the file_in if necessary).
        original_file_path      - String, the absolute path to the original file.
        repeat                  - Boolean, should this runner be executed again once completed with the same variables.

    :param data:
    :return:
    """
    data["exec_command"] = []
    data["repeat"] = False

    settings_dict = load_settings(data)

    abspath = Path(data.get("file_in"))
    cache_abspath = Path(data.get("file_out"))
    logger.debug(
        "Worker invoked for '%s' with task_id=%s", abspath, data.get("task_id")
    )
    existing_metadata = repaired_metadata_for_path(abspath, file_metadata=file_metadata)
    if existing_metadata:
        logger.debug(
            "Worker skipping '%s' because it already has repaired metadata: %s",
            abspath,
            existing_metadata,
        )
        return
    if is_copy_fragment_name(abspath.name):
        logger.debug("Worker invoked for copy fragment %s, skipping", abspath)
        return

    job_state = build_job_state(abspath, settings_dict)
    if job_state is None:
        return

    child = PluginChildProcess(plugin_id=PLUGIN_ID, data=data)
    success = child.run(
        run_repair_job,
        str(abspath),
        str(cache_abspath),
        settings_dict,
        data.get("task_id"),
    )
    expected_cache_output = build_cache_output_path(
        cache_abspath, job_state["output_path"]
    )
    if not success or not expected_cache_output.exists():
        logger.error(
            "Plex DVR Repair worker did not produce the expected cache output. success=%s missing=%s",
            success,
            not expected_cache_output.exists(),
        )
        raise RuntimeError("Plex DVR Repair worker failed")

    # PluginChildProcess runners do not automatically advance file_in for the next
    # worker plugin in the chain, so publish the repaired cache artifact as both
    # the current output and the next input.
    data["file_out"] = str(expected_cache_output)
    data["file_in"] = str(expected_cache_output)

    if task_data_store:
        cleanup_paths = []
        for group in job_state["all_groups"]:
            for fragment in group:
                cleanup_paths.append(str(fragment.path))
        manifest = {
            "original_file_paths": cleanup_paths,
            "final_output_path": str(job_state["output_path"]),
        }
        task_data_store.set_task_state(TASK_STATE_KEY, manifest)
        logger.debug(
            "Stored repair manifest for task '%s': %s", data.get("task_id"), manifest
        )


def on_postprocessor_file_movement(data, task_data_store=None, file_metadata=None):
    """
    Runner function - configures additional postprocessor file movements during the postprocessor stage of a task.

    The 'data' object argument includes:
        library_id              - Integer, the library that the current task is associated with.
        task_id                 - Integer, unique identifier of the task.
        source_data             - Dictionary, data pertaining to the original source file.
        remove_source_file      - Boolean, should Unmanic remove the original source file after all copy operations are complete.
        copy_file               - Boolean, should Unmanic run a copy or move operation with the returned data variables.
        file_in                 - String, the converted cache file to be copied by the postprocessor.
        file_out                - String, the destination file that the file will be copied to.
        run_default_file_copy   - Boolean, should Unmanic run the default post-process file movement.

    :param data:
    :param task_data_store:
    :param file_metadata:
    :return:
    """
    manifest = None
    if task_data_store:
        manifest = task_data_store.get_task_state(TASK_STATE_KEY)
    if not manifest:
        logger.debug(
            "No repair manifest found during file movement for task '%s'",
            data.get("task_id"),
        )
        return

    # Run a custom file copy
    repaired_destination = Path(manifest["final_output_path"])
    data["copy_file"] = True
    data["file_out"] = str(repaired_destination)
    # Dont' let Unmanic remove the source file (this plugin will handle all cleanup)
    data["remove_source_file"] = False
    # Don't let Unmanic run its default file copy operation
    data["run_default_file_copy"] = False

    if not (file_metadata and hasattr(file_metadata, "set")):
        logger.debug(
            "file_metadata helper unavailable during file movement for task '%s'",
            data.get("task_id"),
        )
        return

    payload = {
        "status": "repaired",
        "repaired": True,
        "marker": REPAIRED_FILE_MARKER,
        "source_path": data.get("source_data", {}).get("abspath"),
        "destination_path": str(repaired_destination),
        "cleanup_original_fragment_count": len(manifest.get("original_file_paths", [])),
    }
    file_metadata.set(payload)
    logger.debug("Staged repaired destination metadata: %s", payload)


def on_postprocessor_task_results(data, task_data_store=None):
    """
    Runner function - provides a means for additional postprocessor functions based on the task success.

    The 'data' object argument includes:
        library_id                      - The library that the current task is associated with.
        task_id                         - Integer, unique identifier of the task.
        task_type                       - String, "local" or "remote".
        final_cache_path                - The path to the final cache file that was then used as the source for all destination files.
        task_processing_success         - Boolean, did all task processes complete successfully.
        file_move_processes_success     - Boolean, did all postprocessor movement tasks complete successfully.
        destination_files               - List containing all file paths created by postprocessor file movements.
        source_data                     - Dictionary containing data pertaining to the original source file.
        start_time                      - Float, UNIX timestamp when the task began.
        finish_time                     - Float, UNIX timestamp when the task completed.

    :param data:
    :param task_data_store:
    :return:
    """
    manifest = None
    if task_data_store:
        manifest = task_data_store.get_task_state(TASK_STATE_KEY)
    if not manifest:
        logger.debug(
            "No repair manifest found during task results for task '%s'",
            data.get("task_id"),
        )
        return

    if not data.get("task_processing_success") or not data.get(
        "file_move_processes_success"
    ):
        logger.warning(
            "Skipping Plex DVR Repair cleanup because task or file movement did not complete successfully for task '%s'",
            data.get("task_id"),
        )
        return

    destination_files = set(data.get("destination_files") or [])
    final_output_path = manifest.get("final_output_path")
    if not final_output_path:
        logger.debug(
            "No repaired final output path was recorded for task '%s'",
            data.get("task_id"),
        )
        return

    if final_output_path not in destination_files:
        logger.warning(
            "Skipping Plex DVR Repair cleanup because the repaired destination was not moved successfully: %s",
            final_output_path,
        )
        return

    for fragment_path in manifest.get("original_file_paths", []):
        fragment_abspath = Path(fragment_path)
        if fragment_abspath.exists():
            fragment_abspath.unlink()
            logger.info("Removed original fragment file '%s'", fragment_abspath)
