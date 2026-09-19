#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Archive Extractor plugin for Unmanic.

Implements the workflow requested in Unmanic/unmanic#612:
queue supported archives, extract the primary video, pass it to the remaining
worker flow, and place the final processed media beside the source archive.
"""

import os
import re
import shutil
import subprocess
import zipfile

from unmanic.libs.unplugins.settings import PluginSettings


PLUGIN_ID = "archive_extractor"
PART_RAR_RE = re.compile(r"(?i)\.part(\d+)\.rar$")
RXX_RE = re.compile(r"(?i)\.r(\d\d)$")


class Settings(PluginSettings):
    settings = {
        "Enable ZIP archives": True,
        "Enable RAR archives": True,
        "Delete archive after successful processing": False,
        "Video extensions": "mkv,mp4,m4v,avi,mov,ts,m2ts,webm,mpg,mpeg",
    }


def _log(data, message):
    data.setdefault("worker_log", []).append("\n[Archive Extractor] {}".format(message))


def _video_extensions(settings):
    raw = settings.get_setting("Video extensions") or ""
    return {
        ".{}".format(ext.strip().lower().lstrip("."))
        for ext in str(raw).split(",")
        if ext.strip()
    }


def _archive_kind(path, settings):
    lower = path.lower()

    if lower.endswith(".zip") and settings.get_setting("Enable ZIP archives"):
        return "zip"

    if settings.get_setting("Enable RAR archives"):
        if lower.endswith(".rar") or RXX_RE.search(lower):
            return "rar"

    return None


def _is_primary_archive(path):
    """
    Avoid queueing every volume of the same multipart RAR set.

    New-style multipart sets use *.part01.rar / *.part1.rar as the primary.
    Old-style sets normally use *.rar as the primary followed by *.r00, *.r01.
    A lone .r00 is accepted only when the matching .rar is absent, so users can
    still diagnose/process sets presented that way without duplicate tasks.
    """
    lower = path.lower()

    part_match = PART_RAR_RE.search(lower)
    if part_match:
        return int(part_match.group(1)) == 1

    rxx_match = RXX_RE.search(lower)
    if rxx_match:
        if int(rxx_match.group(1)) != 0:
            return False
        matching_rar = re.sub(r"(?i)\.r00$", ".rar", path)
        return not os.path.exists(matching_rar)

    return True


def _safe_member_basename(member_name):
    # Flatten archive member paths into the task cache. This prevents archive
    # path traversal and makes the final destination deterministic.
    return os.path.basename(member_name.replace("\\", "/"))


def _pick_zip_video(zf, extensions):
    candidates = []
    for info in zf.infolist():
        if info.is_dir():
            continue
        ext = os.path.splitext(info.filename)[1].lower()
        if ext not in extensions:
            continue
        base = _safe_member_basename(info.filename)
        if not base:
            continue
        candidates.append((info.file_size, info, base))

    if not candidates:
        return None

    # Prefer the largest media file. This naturally avoids most sample files.
    candidates.sort(key=lambda item: item[0], reverse=True)
    return candidates[0][1], candidates[0][2]


def _find_extracted_video(root, extensions):
    candidates = []
    if not os.path.isdir(root):
        return None

    for current_root, _, files in os.walk(root):
        for name in files:
            path = os.path.join(current_root, name)
            if os.path.splitext(name)[1].lower() not in extensions:
                continue
            try:
                size = os.path.getsize(path)
            except OSError:
                continue
            candidates.append((size, path))

    if not candidates:
        return None

    candidates.sort(key=lambda item: item[0], reverse=True)
    return candidates[0][1]


def _settings_for(data):
    library_id = data.get("library_id")
    return Settings(library_id=library_id) if library_id else Settings()


def _source_archive_path(data):
    source_data = data.get("source_data") or {}
    return source_data.get("abspath") or data.get("original_file_path") or data.get("file_in") or ""


def on_library_management_file_test(data):
    settings = _settings_for(data)
    path = data.get("path", "")

    if _archive_kind(path, settings) and _is_primary_archive(path):
        data["add_file_to_pending_tasks"] = True

    return data


def on_worker_process(data):
    settings = _settings_for(data)
    source = data.get("file_in") or ""
    original = data.get("original_file_path") or source
    kind = _archive_kind(original, settings)

    # For non-archive inputs this plugin is a no-op, allowing normal media tasks
    # to continue through the rest of the configured worker flow.
    if not kind:
        return data

    extensions = _video_extensions(settings)

    if kind == "zip":
        try:
            with zipfile.ZipFile(original, "r") as zf:
                selected = _pick_zip_video(zf, extensions)
                if not selected:
                    raise RuntimeError("No supported video file was found inside the ZIP archive.")

                info, basename = selected
                out_dir = os.path.dirname(os.path.abspath(data["file_out"]))
                os.makedirs(out_dir, exist_ok=True)
                destination = os.path.join(out_dir, basename)

                _log(data, "Extracting '{}' from ZIP archive.".format(info.filename))
                with zf.open(info, "r") as src, open(destination, "wb") as dst:
                    shutil.copyfileobj(src, dst)

                data["file_in"] = destination
                data["file_out"] = destination
                _log(data, "Selected video: {}".format(basename))
                return data
        except Exception as exc:
            _log(data, "ZIP extraction failed: {}".format(exc))
            raise

    # RAR extraction requires an extractor available in the Unmanic runtime.
    extractor = shutil.which("7z") or shutil.which("7zz") or shutil.which("unrar")
    if not extractor:
        raise RuntimeError(
            "RAR support requires '7z', '7zz', or 'unrar' inside the Unmanic container/runtime."
        )

    base_cache_dir = os.path.dirname(os.path.abspath(data["file_out"]))
    extraction_dir = os.path.join(base_cache_dir, "archive_extractor")
    os.makedirs(extraction_dir, exist_ok=True)

    exe_name = os.path.basename(extractor).lower()
    if exe_name in ("7z", "7zz"):
        command = [extractor, "x", "-y", "-o{}".format(extraction_dir), original]
    else:
        command = [extractor, "x", "-o+", original, extraction_dir + os.sep]

    _log(data, "Using '{}' to extract RAR archive.".format(exe_name))
    result = subprocess.run(
        command,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        universal_newlines=True,
        errors="replace",
    )
    if result.returncode != 0:
        output = (result.stdout or "").strip()
        raise RuntimeError(
            "RAR extraction failed with exit code {}{}.".format(
                result.returncode,
                ": " + output[-1000:] if output else "",
            )
        )

    selected = _find_extracted_video(extraction_dir, extensions)
    if not selected:
        raise RuntimeError(
            "RAR extraction completed but no supported video file was found in '{}'.".format(extraction_dir)
        )

    basename = os.path.basename(selected)
    data["file_in"] = selected
    data["file_out"] = selected
    _log(data, "Selected extracted video: {}".format(basename))
    return data

def on_postprocessor_file_movement(data):
    """
    Put the processed media beside the archive, using the selected archive
    member's filename rather than overwriting the .zip/.rar source.
    """
    archive_path = _source_archive_path(data)
    processed_file = data.get("file_in") or ""

    if not archive_path or not processed_file:
        return data

    # Preserve the final worker output name/extension and place it beside the
    # original archive rather than trying to overwrite the archive itself.
    destination = os.path.join(os.path.dirname(archive_path), os.path.basename(processed_file))

    data["copy_file"] = True
    data["file_out"] = destination
    data["run_default_file_copy"] = False

    # Archive deletion is deferred until task_result confirms all file movement
    # succeeded, preventing data loss when processing or copying fails.
    data["remove_source_file"] = False
    return data


def _rar_related_parts(primary_path):
    directory = os.path.dirname(primary_path)
    name = os.path.basename(primary_path)
    lower = name.lower()
    related = []

    part_match = PART_RAR_RE.search(lower)
    if part_match:
        prefix = name[:part_match.start()]
        pattern = re.compile(r"^{}\.part\d+\.rar$".format(re.escape(prefix)), re.IGNORECASE)
        for entry in os.listdir(directory):
            if pattern.match(entry):
                related.append(os.path.join(directory, entry))
        return related

    if lower.endswith(".rar") or RXX_RE.search(lower):
        base = re.sub(r"(?i)(\.rar|\.r\d\d)$", "", name)
        pattern = re.compile(r"^{}\.(?:rar|r\d\d)$".format(re.escape(base)), re.IGNORECASE)
        for entry in os.listdir(directory):
            if pattern.match(entry):
                related.append(os.path.join(directory, entry))
        return related

    return [primary_path]


def on_postprocessor_task_results(data):
    settings = _settings_for(data)
    archive_path = _source_archive_path(data)
    archive_kind = _archive_kind(archive_path, settings)

    if not archive_path:
        return data

    if not settings.get_setting("Delete archive after successful processing"):
        return data

    if not data.get("task_processing_success") or not data.get("file_move_processes_success"):
        return data

    paths = [archive_path]
    if archive_kind == "rar":
        try:
            paths = _rar_related_parts(archive_path)
        except OSError:
            paths = [archive_path]

    for path in paths:
        try:
            if os.path.isfile(path):
                os.remove(path)
        except OSError:
            # Do not convert a successfully processed task into a failure just
            # because optional archive cleanup could not be completed.
            pass

    return data
