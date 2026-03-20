#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Written by:               Josh.5 <jsunnex@gmail.com>
Date:                     20 March 2026, (12:00 AM)

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

import datetime
import json
import os
import re
import shlex
import subprocess
import uuid
from copy import deepcopy

from peewee import (
    BooleanField,
    DateTimeField,
    FloatField,
    IntegerField,
    Model,
    OperationalError,
    SqliteDatabase,
    TextField,
)
from playhouse.shortcuts import model_to_dict
from unmanic.libs.logs import UnmanicLogging
from unmanic.libs.unplugins.child_process import PluginChildProcess
from unmanic.libs.unplugins.settings import PluginSettings

PLUGIN_ID = "vmaf_quality_audit"
STATE_KEY_RESULT = "analysis_result"
DEFAULT_FFMPEG = "/usr/lib/btbn-ffmpeg/bin/ffmpeg"
DEFAULT_FFPROBE = "/usr/lib/btbn-ffmpeg/bin/ffprobe"


logger = UnmanicLogging.get_logger(name=f"Unmanic.Plugin.{PLUGIN_ID}")
FFMPEG_TIME_RE = re.compile(r"(?:\btime=|\bout_time=)(\d+):(\d+):(\d+(?:\.\d+)?)")


class Settings(PluginSettings):
    settings = {
        "enabled": True,
        "ffmpeg_path": DEFAULT_FFMPEG,
        "ffprobe_path": DEFAULT_FFPROBE,
        "threads": 0,
        "frame_subsample": 1,
        "max_chart_points": 800,
        "fail_on_analysis_error": False,
    }

    def __init__(self, *args, **kwargs):
        super(Settings, self).__init__(*args, **kwargs)
        self.form_settings = {
            "enabled": {
                "label": "Enable VMAF Audit",
                "input_type": "checkbox",
                "description": "Run a VMAF quality audit after the worker pipeline has produced its final cached output for this task.",
            },
            "ffmpeg_path": {
                "label": "FFmpeg Path",
                "input_type": "text",
                "description": "Path to an FFmpeg binary that includes the libvmaf filter.",
            },
            "ffprobe_path": {
                "label": "FFprobe Path",
                "input_type": "text",
                "description": "Path to the FFprobe binary used for source/output diagnostics.",
            },
            "threads": {
                "label": "VMAF Threads",
                "input_type": "number",
                "description": "Number of threads FFmpeg/libvmaf may use during scoring. Set 0 to let FFmpeg choose automatically.",
            },
            "frame_subsample": {
                "label": "Frame Subsample",
                "input_type": "slider",
                "slider_options": {
                    "min": 1,
                    "max": 10,
                    "step": 1,
                    "suffix": "x",
                },
                "description": "Analyze every Nth frame. 1 scores every frame. Higher values reduce runtime and CPU cost, but make the VMAF result less precise.",
            },
            "max_chart_points": {
                "label": "Max Chart Points",
                "input_type": "number",
                "description": "Maximum number of frame score points to keep for the data panel chart. Lower values store less detail and use less space.",
            },
            "fail_on_analysis_error": {
                "label": "Fail Task On Analysis Error",
                "input_type": "checkbox",
                "description": "If the VMAF run fails, fail the overall task instead of saving the task result without VMAF data.",
            },
        }


settings = Settings()
profile_directory = settings.get_profile_directory()
db_file = os.path.abspath(os.path.join(profile_directory, "history.db"))
db = SqliteDatabase(
    db_file,
    pragmas=(
        ("foreign_keys", 1),
        ("journal_mode", "wal"),
    ),
)


class BaseModel(Model):
    class Meta:
        database = db

    def model_to_dict(self):
        return model_to_dict(self, backrefs=True)


class AuditRecord(BaseModel):
    task_id = IntegerField(unique=True, null=False)
    library_id = IntegerField(null=True)
    task_type = TextField(null=False, default="local")
    task_label = TextField(null=False, default="UNKNOWN")
    source_abspath = TextField(null=False, default="")
    source_basename = TextField(null=False, default="")
    analyzed_abspath = TextField(null=True)
    analyzed_basename = TextField(null=True)
    final_cache_path = TextField(null=True)
    destination_files_json = TextField(null=False, default="[]")
    task_processing_success = BooleanField(null=False, default=False)
    file_move_processes_success = BooleanField(null=False, default=False)
    overall_status = TextField(null=False, default="unknown")
    analysis_success = BooleanField(null=False, default=False)
    analysis_error = TextField(null=True)
    ffmpeg_command = TextField(null=True)
    source_video_json = TextField(null=False, default="{}")
    output_video_json = TextField(null=False, default="{}")
    vmaf_summary_json = TextField(null=False, default="{}")
    vmaf_frames_json = TextField(null=False, default="[]")
    vmaf_mean = FloatField(null=True)
    vmaf_harmonic_mean = FloatField(null=True)
    vmaf_min = FloatField(null=True)
    vmaf_max = FloatField(null=True)
    frame_count = IntegerField(null=True)
    test_duration_seconds = FloatField(null=True)
    start_time = DateTimeField(null=True)
    finish_time = DateTimeField(null=True)
    created_at = DateTimeField(null=False, default=datetime.datetime.now)
    updated_at = DateTimeField(null=False, default=datetime.datetime.now)


def _safe_json_dumps(data):
    return json.dumps(data or {}, indent=2, sort_keys=True)


def _safe_json_loads(data, fallback):
    try:
        return json.loads(data)
    except Exception:
        return deepcopy(fallback)


def _decode_argument(value, default=None):
    if value is None:
        return default
    if isinstance(value, list):
        if not value:
            return default
        value = value[0]
    if isinstance(value, bytes):
        return value.decode("utf-8")
    return value


def _normalize_path(path):
    if not path:
        return ""
    return os.path.abspath(path)


def _parse_ratio(value):
    if not value or value in {"0/0", "N/A"}:
        return None
    if "/" in str(value):
        numerator, denominator = str(value).split("/", 1)
        try:
            denominator_value = float(denominator)
            if denominator_value == 0:
                return None
            return float(numerator) / denominator_value
        except Exception:
            return None
    try:
        return float(value)
    except Exception:
        return None


def _coerce_int(value, default):
    try:
        return int(value)
    except Exception:
        return default


def _coerce_float(value):
    try:
        return float(value)
    except Exception:
        return None


def _format_datetime(value):
    if not value:
        return ""
    return value.strftime("%Y-%m-%d %H:%M:%S")


def _duration_seconds(start_time, finish_time):
    if not start_time or not finish_time:
        return None
    try:
        duration = (finish_time - start_time).total_seconds()
    except Exception:
        return None
    if duration < 0:
        return None
    return round(duration, 3)


def _video_stream_from_probe(probe_data):
    for stream in probe_data.get("streams", []):
        if stream.get("codec_type") == "video":
            return stream
    return {}


def _probe_media(ffprobe_path, file_path):
    command = [
        ffprobe_path,
        "-v",
        "error",
        "-print_format",
        "json",
        "-show_format",
        "-show_streams",
        file_path,
    ]
    result = subprocess.run(command, capture_output=True, text=True, check=True)
    return json.loads(result.stdout or "{}")


def _summarize_probe(probe_data, file_path):
    stream = _video_stream_from_probe(probe_data)
    format_info = probe_data.get("format", {})
    return {
        "path": _normalize_path(file_path),
        "codec_name": stream.get("codec_name"),
        "codec_long_name": stream.get("codec_long_name"),
        "profile": stream.get("profile"),
        "width": stream.get("width"),
        "height": stream.get("height"),
        "pix_fmt": stream.get("pix_fmt"),
        "bit_rate": _coerce_int(
            stream.get("bit_rate") or format_info.get("bit_rate"), None
        ),
        "duration": _coerce_float(
            stream.get("duration") or format_info.get("duration")
        ),
        "avg_frame_rate": _parse_ratio(stream.get("avg_frame_rate")),
        "sample_aspect_ratio": stream.get("sample_aspect_ratio"),
        "display_aspect_ratio": stream.get("display_aspect_ratio"),
        "color_space": stream.get("color_space"),
        "color_transfer": stream.get("color_transfer"),
        "color_primaries": stream.get("color_primaries"),
    }


def _build_vmaf_filter(log_path, thread_count, frame_subsample):
    options = [
        "log_fmt=json",
        f"log_path={log_path}",
    ]
    if thread_count and int(thread_count) > 0:
        options.append(f"n_threads={int(thread_count)}")
    if frame_subsample and int(frame_subsample) > 1:
        options.append(f"n_subsample={int(frame_subsample)}")

    return (
        "[0:v][1:v]scale2ref=flags=bicubic[distorted][reference];"
        "[distorted]settb=AVTB,setpts=PTS-STARTPTS[dist];"
        "[reference]settb=AVTB,setpts=PTS-STARTPTS[ref];"
        f"[dist][ref]libvmaf={':'.join(options)}"
    )


def _analysis_duration_seconds(source_probe, encoded_probe):
    durations = [
        _coerce_float(_video_stream_from_probe(source_probe).get("duration")),
        _coerce_float(source_probe.get("format", {}).get("duration")),
        _coerce_float(_video_stream_from_probe(encoded_probe).get("duration")),
        _coerce_float(encoded_probe.get("format", {}).get("duration")),
    ]
    durations = [value for value in durations if value and value > 0]
    return max(durations) if durations else 0.0


def _parse_ffmpeg_progress_percent(line, duration_seconds):
    if not line or duration_seconds <= 0:
        return None
    match = FFMPEG_TIME_RE.search(line)
    if not match:
        return None
    hours, minutes, seconds = match.groups()
    try:
        current_seconds = (int(hours) * 3600) + (int(minutes) * 60) + float(seconds)
    except Exception:
        return None
    return max(0, min(int((current_seconds / duration_seconds) * 100), 100))


def _write_json_file(path, payload):
    with open(path, "w", encoding="utf-8") as file_handle:
        json.dump(payload, file_handle, indent=2, sort_keys=True)


def _extract_vmaf_summary(vmaf_data):
    pooled = vmaf_data.get("pooled_metrics", {})
    vmaf_metric = pooled.get("vmaf", {})
    frame_scores = []
    for frame in vmaf_data.get("frames", []):
        frame_metrics = frame.get("metrics", {})
        score = _coerce_float(frame_metrics.get("vmaf"))
        if score is None:
            continue
        frame_scores.append(
            {
                "frame_num": frame.get("frameNum"),
                "vmaf": score,
            }
        )

    if frame_scores:
        frame_values = [item["vmaf"] for item in frame_scores]
        frame_min = min(frame_values)
        frame_max = max(frame_values)
    else:
        frame_min = None
        frame_max = None

    return {
        "mean": _coerce_float(vmaf_metric.get("mean")),
        "harmonic_mean": _coerce_float(vmaf_metric.get("harmonic_mean")),
        "min": frame_min,
        "max": frame_max,
        "frame_count": len(frame_scores),
        "frames": frame_scores,
    }


def _downsample_frames(frame_scores, max_points):
    if not frame_scores:
        return []
    if max_points <= 0 or len(frame_scores) <= max_points:
        return frame_scores

    sampled = []
    last_index = len(frame_scores) - 1
    for point_index in range(max_points):
        source_index = round(point_index * last_index / max(max_points - 1, 1))
        sampled.append(frame_scores[source_index])
    return sampled


def _build_analysis_paths(encoded_path, task_id):
    cache_dir = os.path.dirname(_normalize_path(encoded_path))
    os.makedirs(cache_dir, exist_ok=True)
    task_label = task_id or "task"
    return {
        "cache_dir": cache_dir,
        "log_path": os.path.join(cache_dir, f"{PLUGIN_ID}-{task_label}-vmaf.json"),
        "result_path": os.path.join(cache_dir, f"{PLUGIN_ID}-{task_label}-result.json"),
    }


def _build_vmaf_command(source_path, encoded_path, settings_payload, log_path):
    thread_count = _coerce_int(settings_payload.get("threads"), 0)
    frame_subsample = max(_coerce_int(settings_payload.get("frame_subsample"), 1), 1)
    filter_complex = _build_vmaf_filter(log_path, thread_count, frame_subsample)
    return [
        settings_payload.get("ffmpeg_path") or DEFAULT_FFMPEG,
        "-hide_banner",
        "-nostdin",
        "-y",
        "-i",
        encoded_path,
        "-i",
        source_path,
        "-lavfi",
        filter_complex,
        "-f",
        "null",
        "-",
    ]


def _run_vmaf_audit_child(
    source_path, encoded_path, settings_payload, paths, log_queue=None, prog_queue=None
):
    ffprobe_path = settings_payload.get("ffprobe_path") or DEFAULT_FFPROBE
    max_chart_points = max(
        _coerce_int(settings_payload.get("max_chart_points"), 800), 10
    )
    log_path = paths["log_path"]
    result_path = paths["result_path"]
    try:
        if not os.path.exists(settings_payload.get("ffmpeg_path") or DEFAULT_FFMPEG):
            raise FileNotFoundError(
                f"Configured FFmpeg binary was not found: {settings_payload.get('ffmpeg_path') or DEFAULT_FFMPEG}"
            )
        if not os.path.exists(ffprobe_path):
            raise FileNotFoundError(
                f"Configured FFprobe binary was not found: {ffprobe_path}"
            )

        source_probe = _probe_media(ffprobe_path, source_path)
        encoded_probe = _probe_media(ffprobe_path, encoded_path)

        if not _video_stream_from_probe(source_probe):
            raise RuntimeError(
                "The original source file does not contain a video stream."
            )
        if not _video_stream_from_probe(encoded_probe):
            raise RuntimeError(
                "The analyzed cached output does not contain a video stream."
            )

        command = _build_vmaf_command(
            source_path, encoded_path, settings_payload, log_path
        )
        command_string = shlex.join(command)
        duration_seconds = _analysis_duration_seconds(source_probe, encoded_probe)
        output_tail = []
        if log_queue is not None:
            log_queue.put(f"[{PLUGIN_ID}] Executing VMAF audit:")
            log_queue.put(command_string)
            if duration_seconds > 0:
                log_queue.put(
                    f"[{PLUGIN_ID}] Progress tracking duration: {duration_seconds:.3f} seconds"
                )
        if prog_queue is not None:
            prog_queue.put(0)

        process = subprocess.Popen(
            command,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            universal_newlines=True,
            errors="replace",
        )

        last_percent = None
        try:
            while True:
                line = process.stdout.readline()
                if line:
                    stripped = line.rstrip()
                    if stripped:
                        output_tail.append(stripped)
                        output_tail = output_tail[-20:]
                        if log_queue is not None:
                            log_queue.put(stripped)
                        percent = _parse_ffmpeg_progress_percent(
                            stripped, duration_seconds
                        )
                        if (
                            percent is not None
                            and prog_queue is not None
                            and percent != last_percent
                        ):
                            prog_queue.put(percent)
                            last_percent = percent
                if line == "" and process.poll() is not None:
                    break
        finally:
            if process.stdout:
                process.stdout.close()

        if process.returncode != 0:
            raise RuntimeError(
                "FFmpeg VMAF command failed with exit code {}. {}".format(
                    process.returncode,
                    "\n".join(output_tail) or "No command output was captured.",
                )
            )

        if prog_queue is not None:
            prog_queue.put(100)

        if not os.path.exists(log_path):
            raise RuntimeError(
                f"FFmpeg completed without writing the expected VMAF log: {log_path}"
            )

        with open(log_path, "r", encoding="utf-8") as file_handle:
            vmaf_data = json.load(file_handle)

        summary = _extract_vmaf_summary(vmaf_data)
        frame_scores = _downsample_frames(summary.pop("frames"), max_chart_points)
        result_payload = {
            "analysis_success": True,
            "analysis_error": "",
            "ffmpeg_command": command_string,
            "source_video": _summarize_probe(source_probe, source_path),
            "output_video": _summarize_probe(encoded_probe, encoded_path),
            "vmaf_summary": summary,
            "vmaf_frames": frame_scores,
            "source_abspath": _normalize_path(source_path),
            "analyzed_abspath": _normalize_path(encoded_path),
            "captured_at": datetime.datetime.utcnow().isoformat() + "Z",
        }
        _write_json_file(result_path, result_payload)
    except Exception as exc:
        failure_payload = {
            "analysis_success": False,
            "analysis_error": str(exc),
            "ffmpeg_command": shlex.join(
                _build_vmaf_command(
                    source_path, encoded_path, settings_payload, log_path
                )
            ),
            "source_video": {},
            "output_video": {},
            "vmaf_summary": {},
            "vmaf_frames": [],
            "source_abspath": _normalize_path(source_path),
            "analyzed_abspath": _normalize_path(encoded_path),
            "captured_at": datetime.datetime.utcnow().isoformat() + "Z",
        }
        _write_json_file(result_path, failure_payload)
        raise


def _run_vmaf_audit(source_path, encoded_path, plugin_settings, data):
    settings_payload = {
        "ffmpeg_path": plugin_settings.get_setting("ffmpeg_path") or DEFAULT_FFMPEG,
        "ffprobe_path": plugin_settings.get_setting("ffprobe_path") or DEFAULT_FFPROBE,
        "threads": _coerce_int(plugin_settings.get_setting("threads"), 0),
        "frame_subsample": max(
            _coerce_int(plugin_settings.get_setting("frame_subsample"), 1), 1
        ),
        "max_chart_points": max(
            _coerce_int(plugin_settings.get_setting("max_chart_points"), 800), 10
        ),
    }
    paths = _build_analysis_paths(encoded_path, data.get("task_id"))
    command = _build_vmaf_command(
        source_path, encoded_path, settings_payload, paths["log_path"]
    )
    command_string = shlex.join(command)

    current_command = data.get("current_command")
    if isinstance(current_command, list):
        current_command.clear()
        current_command.append(command_string)

    child = PluginChildProcess(plugin_id=PLUGIN_ID, data=data)
    success = child.run(
        _run_vmaf_audit_child, source_path, encoded_path, settings_payload, paths
    )

    if not os.path.exists(paths["result_path"]):
        raise RuntimeError(
            "VMAF audit child process completed without writing a result payload."
        )

    with open(paths["result_path"], "r", encoding="utf-8") as file_handle:
        result_payload = json.load(file_handle)

    if not success and result_payload.get("analysis_success"):
        result_payload["analysis_success"] = False
        result_payload["analysis_error"] = "VMAF child process failed unexpectedly."
    return result_payload


class DataStore(object):
    def __init__(self):
        self.create_db_schema()

    def db_start(self):
        try:
            db.connect(reuse_if_open=True)
        except OperationalError:
            pass

    def db_stop(self):
        try:
            if not db.is_closed():
                db.close()
        except OperationalError:
            pass

    def create_db_schema(self):
        self.db_start()
        db.create_tables([AuditRecord], safe=True)
        self.db_stop()

    def clear_all_data(self):
        self.db_start()
        try:
            AuditRecord.delete().execute()
            success = True
        except Exception:
            logger.exception("Failed clearing VMAF audit history.")
            success = False
        self.db_stop()
        return success

    def save_record(self, payload):
        self.db_start()
        try:
            record = (
                AuditRecord.select()
                .where(AuditRecord.task_id == payload["task_id"])
                .first()
            )
            if record is None:
                record = AuditRecord(task_id=payload["task_id"])
            for key, value in payload.items():
                setattr(record, key, value)
            record.updated_at = datetime.datetime.now()
            record.save()
            record_id = record.id
        except Exception:
            logger.exception("Failed saving VMAF audit history.")
            record_id = None
        self.db_stop()
        return record_id

    def _base_query(self):
        return AuditRecord.select().order_by(
            AuditRecord.finish_time.desc(), AuditRecord.id.desc()
        )

    def get_summary(self):
        self.db_start()
        records = list(self._base_query())
        summary = {
            "total_records": len(records),
            "completed_records": 0,
            "failed_records": 0,
            "analysis_failures": 0,
            "average_vmaf": None,
            "latest_finish_time": "",
        }
        scores = []
        for record in records:
            if record.task_processing_success and record.file_move_processes_success:
                summary["completed_records"] += 1
            else:
                summary["failed_records"] += 1
            if not record.analysis_success:
                summary["analysis_failures"] += 1
            if record.vmaf_mean is not None:
                scores.append(record.vmaf_mean)
            if not summary["latest_finish_time"] and record.finish_time:
                summary["latest_finish_time"] = _format_datetime(record.finish_time)
        if scores:
            summary["average_vmaf"] = round(sum(scores) / len(scores), 3)
        self.db_stop()
        return summary

    def list_records(self):
        self.db_start()
        results = []
        for record in self._base_query():
            output_video = _safe_json_loads(record.output_video_json, {})
            results.append(
                {
                    "id": record.id,
                    "task_id": record.task_id,
                    "task_label": record.task_label,
                    "source_basename": record.source_basename,
                    "analyzed_basename": record.analyzed_basename,
                    "overall_status": record.overall_status,
                    "task_processing_success": record.task_processing_success,
                    "file_move_processes_success": record.file_move_processes_success,
                    "analysis_success": record.analysis_success,
                    "vmaf_mean": record.vmaf_mean,
                    "vmaf_harmonic_mean": record.vmaf_harmonic_mean,
                    "frame_count": record.frame_count,
                    "test_duration_seconds": record.test_duration_seconds,
                    "codec_name": output_video.get("codec_name"),
                    "resolution": (
                        "{}x{}".format(
                            output_video.get("width"), output_video.get("height")
                        )
                        if output_video.get("width") and output_video.get("height")
                        else ""
                    ),
                    "finish_time": _format_datetime(record.finish_time),
                    "start_time": _format_datetime(record.start_time),
                    "analysis_error": record.analysis_error or "",
                }
            )
        self.db_stop()
        return results

    def get_record_detail(self, record_id):
        self.db_start()
        try:
            record = AuditRecord.get_by_id(record_id)
            result = {
                "id": record.id,
                "task_id": record.task_id,
                "library_id": record.library_id,
                "task_type": record.task_type,
                "task_label": record.task_label,
                "source_abspath": record.source_abspath,
                "source_basename": record.source_basename,
                "analyzed_abspath": record.analyzed_abspath,
                "analyzed_basename": record.analyzed_basename,
                "final_cache_path": record.final_cache_path,
                "destination_files": _safe_json_loads(
                    record.destination_files_json, []
                ),
                "task_processing_success": record.task_processing_success,
                "file_move_processes_success": record.file_move_processes_success,
                "overall_status": record.overall_status,
                "analysis_success": record.analysis_success,
                "analysis_error": record.analysis_error or "",
                "ffmpeg_command": record.ffmpeg_command or "",
                "source_video": _safe_json_loads(record.source_video_json, {}),
                "output_video": _safe_json_loads(record.output_video_json, {}),
                "vmaf_summary": _safe_json_loads(record.vmaf_summary_json, {}),
                "vmaf_frames": _safe_json_loads(record.vmaf_frames_json, []),
                "vmaf_mean": record.vmaf_mean,
                "vmaf_harmonic_mean": record.vmaf_harmonic_mean,
                "vmaf_min": record.vmaf_min,
                "vmaf_max": record.vmaf_max,
                "frame_count": record.frame_count,
                "test_duration_seconds": record.test_duration_seconds,
                "start_time": _format_datetime(record.start_time),
                "finish_time": _format_datetime(record.finish_time),
                "created_at": _format_datetime(record.created_at),
                "updated_at": _format_datetime(record.updated_at),
            }
        except AuditRecord.DoesNotExist:
            result = {}
        self.db_stop()
        return result


def _build_destination_file_data(destination_files):
    results = []
    for path in destination_files or []:
        abspath = _normalize_path(path)
        item = {
            "path": abspath,
            "basename": os.path.basename(abspath),
            "exists": os.path.exists(abspath),
            "size": os.path.getsize(abspath) if os.path.exists(abspath) else None,
        }
        results.append(item)
    return results


def _destination_log_fields(destination_files):
    existing_files = [item for item in destination_files if item.get("exists")]
    existing_sizes = [
        item.get("size") for item in existing_files if item.get("size") is not None
    ]
    primary_destination = destination_files[0] if destination_files else {}
    fields = {
        "destination_primary_abspath": primary_destination.get("path", ""),
        "destination_primary_basename": primary_destination.get("basename", ""),
        "destination_files_count": len(destination_files),
        "destination_existing_count": len(existing_files),
        "destination_total_size": sum(existing_sizes) if existing_sizes else None,
    }
    for index, item in enumerate(destination_files, start=1):
        fields[f"destination_{index}_abspath"] = item.get("path", "")
        fields[f"destination_{index}_basename"] = item.get("basename", "")
        fields[f"destination_{index}_exists"] = item.get("exists")
        fields[f"destination_{index}_size"] = item.get("size")
    return fields


def _video_log_fields(prefix, video_data):
    video_data = video_data or {}
    return {
        f"{prefix}_video_codec_name": video_data.get("codec_name"),
        f"{prefix}_video_codec_long_name": video_data.get("codec_long_name"),
        f"{prefix}_video_profile": video_data.get("profile"),
        f"{prefix}_video_width": video_data.get("width"),
        f"{prefix}_video_height": video_data.get("height"),
        f"{prefix}_video_pix_fmt": video_data.get("pix_fmt"),
        f"{prefix}_video_bit_rate": video_data.get("bit_rate"),
        f"{prefix}_video_duration": video_data.get("duration"),
        f"{prefix}_video_avg_frame_rate": video_data.get("avg_frame_rate"),
        f"{prefix}_video_sample_aspect_ratio": video_data.get("sample_aspect_ratio"),
        f"{prefix}_video_display_aspect_ratio": video_data.get("display_aspect_ratio"),
        f"{prefix}_video_color_space": video_data.get("color_space"),
        f"{prefix}_video_color_transfer": video_data.get("color_transfer"),
        f"{prefix}_video_color_primaries": video_data.get("color_primaries"),
    }


def _percentile(values, percentile):
    if not values:
        return None
    if len(values) == 1:
        return values[0]
    position = (len(values) - 1) * percentile
    lower_index = int(position)
    upper_index = min(lower_index + 1, len(values) - 1)
    if lower_index == upper_index:
        return values[lower_index]
    lower_value = values[lower_index]
    upper_value = values[upper_index]
    fraction = position - lower_index
    return round(lower_value + (upper_value - lower_value) * fraction, 6)


def _vmaf_log_fields(summary, frames):
    summary = summary or {}
    frames = frames or []
    values = sorted(item.get("vmaf") for item in frames if item.get("vmaf") is not None)
    first_frame = frames[0] if frames else {}
    last_frame = frames[-1] if frames else {}
    return {
        "vmaf_mean": _coerce_float(summary.get("mean")),
        "vmaf_harmonic_mean": _coerce_float(summary.get("harmonic_mean")),
        "vmaf_min": _coerce_float(summary.get("min")),
        "vmaf_max": _coerce_float(summary.get("max")),
        "vmaf_frame_count": _coerce_int(summary.get("frame_count"), 0),
        "vmaf_frames_points_count": len(frames),
        "vmaf_p05": _percentile(values, 0.05),
        "vmaf_p10": _percentile(values, 0.10),
        "vmaf_p25": _percentile(values, 0.25),
        "vmaf_p50": _percentile(values, 0.50),
        "vmaf_p75": _percentile(values, 0.75),
        "vmaf_p90": _percentile(values, 0.90),
        "vmaf_p95": _percentile(values, 0.95),
        "vmaf_first_frame_num": first_frame.get("frame_num"),
        "vmaf_first_frame_score": first_frame.get("vmaf"),
        "vmaf_last_frame_num": last_frame.get("frame_num"),
        "vmaf_last_frame_score": last_frame.get("vmaf"),
    }


def _event_destination_files(data):
    destination_files = data.get("destination_files") or []
    if destination_files:
        return destination_files

    destination_data = data.get("destination_data") or {}
    destination_path = destination_data.get("abspath")
    return [destination_path] if destination_path else []


def _build_overall_status(data, analysis_success):
    if "task_success" in data:
        if data.get("task_success") and not data.get(
            "file_move_processes_success", True
        ):
            return (
                "postprocess_failed"
                if analysis_success
                else "postprocess_failed_without_vmaf"
            )
        if data.get("task_success"):
            return "completed" if analysis_success else "completed_without_vmaf"
        return "failed" if analysis_success else "failed_without_vmaf"
    if data.get("task_processing_success") and data.get("file_move_processes_success"):
        return "completed" if analysis_success else "completed_without_vmaf"
    if data.get("task_processing_success") and not data.get(
        "file_move_processes_success"
    ):
        return (
            "postprocess_failed"
            if analysis_success
            else "postprocess_failed_without_vmaf"
        )
    return "processing_failed" if analysis_success else "processing_failed_without_vmaf"


def _persist_audit_record(task_data_store, data):
    analysis = task_data_store.get_task_state(STATE_KEY_RESULT, default={}) or {}
    source_path = _normalize_path(data.get("source_data", {}).get("abspath"))
    destination_files = _build_destination_file_data(_event_destination_files(data))
    finish_time = (
        datetime.datetime.fromtimestamp(data["finish_time"])
        if data.get("finish_time")
        else None
    )
    start_time = (
        datetime.datetime.fromtimestamp(data["start_time"])
        if data.get("start_time")
        else None
    )
    test_duration_seconds = _duration_seconds(start_time, finish_time)

    source_video = analysis.get("source_video") or {}
    output_video = analysis.get("output_video") or {}
    vmaf_summary = analysis.get("vmaf_summary") or {}
    vmaf_frames = analysis.get("vmaf_frames") or []
    analysis_success = bool(analysis.get("analysis_success"))

    payload = {
        "task_id": data.get("task_id"),
        "library_id": data.get("library_id"),
        "task_type": data.get("task_type", "local"),
        "task_label": os.path.basename(source_path)
        or source_path
        or f"Task {data.get('task_id')}",
        "source_abspath": source_path,
        "source_basename": os.path.basename(source_path),
        "analyzed_abspath": _normalize_path(
            analysis.get("analyzed_abspath") or data.get("final_cache_path")
        ),
        "analyzed_basename": os.path.basename(
            analysis.get("analyzed_abspath") or data.get("final_cache_path") or ""
        ),
        "final_cache_path": _normalize_path(data.get("final_cache_path")),
        "destination_files_json": _safe_json_dumps(destination_files),
        "task_processing_success": bool(data.get("task_success")),
        "file_move_processes_success": bool(data.get("file_move_processes_success")),
        "overall_status": _build_overall_status(data, analysis_success),
        "analysis_success": analysis_success,
        "analysis_error": analysis.get("analysis_error") or "",
        "ffmpeg_command": analysis.get("ffmpeg_command") or "",
        "source_video_json": _safe_json_dumps(source_video),
        "output_video_json": _safe_json_dumps(output_video),
        "vmaf_summary_json": _safe_json_dumps(vmaf_summary),
        "vmaf_frames_json": _safe_json_dumps(vmaf_frames),
        "vmaf_mean": _coerce_float(vmaf_summary.get("mean")),
        "vmaf_harmonic_mean": _coerce_float(vmaf_summary.get("harmonic_mean")),
        "vmaf_min": _coerce_float(vmaf_summary.get("min")),
        "vmaf_max": _coerce_float(vmaf_summary.get("max")),
        "frame_count": _coerce_int(vmaf_summary.get("frame_count"), 0),
        "test_duration_seconds": test_duration_seconds,
        "start_time": start_time,
        "finish_time": finish_time,
    }

    source_bit_rate = _coerce_int(source_video.get("bit_rate"), None)
    output_bit_rate = _coerce_int(output_video.get("bit_rate"), None)
    bit_rate_delta = None
    bit_rate_ratio = None
    if source_bit_rate is not None and output_bit_rate is not None:
        bit_rate_delta = output_bit_rate - source_bit_rate
        if source_bit_rate > 0:
            bit_rate_ratio = round(output_bit_rate / source_bit_rate, 6)

    log_payload = {
        "task_id": payload["task_id"],
        "library_id": payload["library_id"],
        "task_type": payload["task_type"],
        "task_label": payload["task_label"],
        "source_abspath": payload["source_abspath"],
        "source_basename": payload["source_basename"],
        "analyzed_abspath": payload["analyzed_abspath"],
        "analyzed_basename": payload["analyzed_basename"],
        "final_cache_path": payload["final_cache_path"],
        "task_processing_success": payload["task_processing_success"],
        "file_move_processes_success": payload["file_move_processes_success"],
        "overall_status": payload["overall_status"],
        "analysis_success": payload["analysis_success"],
        "analysis_error": payload["analysis_error"],
        "ffmpeg_command": payload["ffmpeg_command"],
        "start_time": _format_datetime(payload["start_time"]),
        "finish_time": _format_datetime(payload["finish_time"]),
        "test_duration_seconds": payload["test_duration_seconds"],
        "processed_by_worker": data.get("processed_by_worker"),
        "task_log": data.get("log"),
        "source_output_bit_rate_delta": bit_rate_delta,
        "source_output_bit_rate_ratio": bit_rate_ratio,
    }
    log_payload.update(_destination_log_fields(destination_files))
    log_payload.update(_video_log_fields("source", source_video))
    log_payload.update(_video_log_fields("output", output_video))
    log_payload.update(_vmaf_log_fields(vmaf_summary, vmaf_frames))

    UnmanicLogging.data(
        PLUGIN_ID,
        data_search_key="{} | {} | {}".format(
            data.get("task_id"), data.get("library_id"), source_path
        ),
        **log_payload,
    )

    return DataStore().save_record(payload)


def on_worker_process(data, task_data_store=None):
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

    **Shared task & runner state**
    Plugins can store shared, cross‐plugin and even cross‐process state via `TaskDataStore`:

        from unmanic.libs.task import TaskDataStore

        # Store mutable per‐task values:
        TaskDataStore.set_task_state("source_file_size", source_file_size)
        # read it back later (same or other plugin):
        p = TaskDataStore.get_task_state("source_file_size")

        # Store immutable runner‐scoped values:
        TaskDataStore.set_runner_value("probe_info", {...})
        val = TaskDataStore.get_runner_value("probe_info")

    **Spawning your own child process**
    Instead of setting `exec_command`, you can perform complex or Python‐only work in a separate process while still reporting logs & progress:

        import time

        from unmanic.libs.unplugins.child_process import PluginChildProcess

        proc = PluginChildProcess(plugin_id="<your_plugin_id>", data=data)

        def child_work(source_path, log_queue=None, prog_queue=None):
            # PluginChildProcess injects log_queue and prog_queue as keyword args.
            # any positional args should be passed to proc.run(...) first
            log_queue.put(f"Starting work for {source_path}")
            for i in range(10):
                # emit a UI log line:
                log_queue.put(f"step {i}/10 completed")
                # emit progress 0–100:
                prog_queue.put((i + 1) * 10)
                time.sleep(1)

        # Runs child_work in its own process, returns True if exit code==0
        success = proc.run(child_work, data["file_in"])

    In this mode the `PluginChildProcess` helper:
      1. Spawns the child via `multiprocessing.Process`.
      2. Calls your target with `target(*args, **kwargs)` after injecting `log_queue` and `prog_queue` into the keyword arguments.
      3. Registers its PID & start‐time with the worker’s `default_progress_parser`.
      4. Drains `log_queue` → `data["worker_log"]` for UI tail.
      5. Drains `prog_queue` → `command_progress_parser(line_text)` to update the progress bar.
      6. Will unset the child process PID on exit to reset all tracked subprocess metrics in the Unmanic Worker (CPU, memory, progress, etc.).

    :param data:
    :return:

    """
    plugin_settings = Settings(library_id=data.get("library_id"))
    if not plugin_settings.get_setting("enabled"):
        logger.debug(
            "VMAF Quality Audit disabled for library '%s'.", data.get("library_id")
        )
        return

    source_path = _normalize_path(data.get("original_file_path"))
    encoded_path = _normalize_path(data.get("file_in"))
    result = {
        "analysis_success": False,
        "analysis_error": "",
        "ffmpeg_command": "",
        "source_abspath": source_path,
        "analyzed_abspath": encoded_path,
        "source_video": {},
        "output_video": {},
        "vmaf_summary": {},
        "vmaf_frames": [],
    }

    try:
        result = _run_vmaf_audit(source_path, encoded_path, plugin_settings, data)
        logger.info("Stored VMAF analysis state for task '%s'.", data.get("task_id"))
    except Exception as err:
        result["analysis_error"] = str(err)
        logger.warning("VMAF audit failed for task '%s': %s", data.get("task_id"), err)
        data.get("worker_log", []).append(f"\n[{PLUGIN_ID}] VMAF audit failed: {err}\n")
        if plugin_settings.get_setting("fail_on_analysis_error"):
            raise
    finally:
        if task_data_store is not None:
            task_data_store.set_task_state(STATE_KEY_RESULT, result)


def emit_postprocessor_complete(data, task_data_store=None):
    """
    Runner function - emit data when a task has been fully post-processed and recorded in history.

    The 'data' object argument includes:
        library_id           - Integer, the ID of the library.
        task_id              - Integer, unique identifier of the task.
        task_type            - String, "local" or "remote".
        source_data          - Dict, information about the source file for the task.
        destination_data     - Dict, information about the final output file after postprocessing for the task.
        destination_files    - List, all file paths created by postprocessor file movements.
        task_success         - Boolean, True if the task succeeded.
        file_move_processes_success - Boolean, True if all postprocessor movement tasks completed successfully.
        start_time           - Float, UNIX timestamp when the task began.
        finish_time          - Float, UNIX timestamp when the task completed.
        processed_by_worker  - String, identifier of the worker that processed it.
        log                  - String, full text of the task log.

    :param data:
    :return:

    """
    if task_data_store is None:
        logger.error("TaskDataStore was not provided to the plugin runner.")
        return

    record_id = _persist_audit_record(task_data_store, data)
    if record_id is None:
        logger.error(
            "Failed writing VMAF audit result for task '%s'.", data.get("task_id")
        )


def _panel_payload_records():
    store = DataStore()
    return {
        "summary": store.get_summary(),
        "data": store.list_records(),
    }


def _panel_payload_detail(data):
    record_id = _decode_argument(data.get("arguments", {}).get("id"))
    if not record_id:
        return {}
    return DataStore().get_record_detail(int(record_id))


def _panel_payload_reset():
    success = DataStore().clear_all_data()
    return {
        "success": success,
        "message": (
            "Audit history cleared." if success else "Failed to clear audit history."
        ),
    }


def render_frontend_panel(data, task_data_store=None):
    """
    Runner function - display a custom data panel in the frontend.

    The 'data' object argument includes:
        content_type                    - The content type to be set when writing back to the browser.
        content                         - The content to print to the browser.
        path                            - The path received after the '/unmanic/panel' path.
        arguments                       - A dictionary of GET arguments received.

    :param data:
    :return:

    """
    path = (data.get("path") or "").strip("/")

    if path == "records":
        data["content_type"] = "application/json"
        data["content"] = json.dumps(_panel_payload_records(), indent=2)
        return data

    if path == "detail":
        data["content_type"] = "application/json"
        data["content"] = json.dumps(_panel_payload_detail(data), indent=2)
        return data

    if path == "reset":
        data["content_type"] = "application/json"
        data["content"] = json.dumps(_panel_payload_reset(), indent=2)
        return data

    index_path = os.path.abspath(
        os.path.join(os.path.dirname(__file__), "static", "index.html")
    )
    with open(index_path, "r", encoding="utf-8") as file_handle:
        content = file_handle.read()
        data["content"] = content.replace("{cache_buster}", str(uuid.uuid4()))

    return data
