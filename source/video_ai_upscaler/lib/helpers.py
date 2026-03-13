#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
    Written by:               Josh.5 <jsunnex@gmail.com>
    Date:                     22 December 2025, (11:57 AM)

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
import logging
import subprocess
import threading
import time


logger = logging.getLogger("Unmanic.Plugin.video_ai_upscaler")


def get_plugin_path():
    return os.path.dirname(os.path.dirname(__file__))


def get_latest_waifu2x_dir(share_dir):
    base_dir = os.path.join(share_dir, "waifu2x-ncnn-vulkan")
    if os.path.isdir(base_dir):
        candidates = [
            name for name in os.listdir(base_dir)
            if name.startswith("waifu2x-ncnn-vulkan-")
        ]
        if candidates:
            latest = sorted(candidates)[-1]
            return os.path.join(base_dir, latest)
    return None


def count_png_files(path):
    if not path or not os.path.isdir(path):
        return 0
    return sum(1 for entry in os.scandir(path) if entry.is_file() and entry.name.endswith(".png"))


def scale_percent(phase_start, phase_end, percent):
    percent_value = max(0.0, min(100.0, float(percent)))
    return phase_start + (phase_end - phase_start) * (percent_value / 100.0)


def pick_realesrgan_scale(source_height, target_height):
    if not source_height or not target_height:
        return 4
    ratio = float(target_height) / float(source_height)
    if ratio <= 2:
        return 2
    if ratio <= 3:
        return 3
    return 4


def pick_waifu2x_scale(source_height, target_height):
    if not source_height or not target_height:
        return 2
    ratio = float(target_height) / float(source_height)
    for scale in (1, 2, 4, 8, 16, 32):
        if ratio <= scale:
            return scale
    return 32


def run_command_with_ffmpeg_progress(cmd_args, parser, prog_queue, log_queue, phase_start, phase_end):
    logger.debug("Running command with ffmpeg progress: %s", cmd_args)
    process = subprocess.Popen(
        cmd_args,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        bufsize=1,
    )
    if process.stdout:
        for line in process.stdout:
            stripped = line.rstrip()
            log_queue.put(stripped)
            logger.debug("Command output: %s", stripped)
            try:
                progress = parser.parse_progress(line)
                percent = progress.get("percent", 0)
                prog_queue.put(scale_percent(phase_start, phase_end, percent))
            except Exception as exc:
                logger.debug("Progress parse failed for line '%s': %s", stripped, exc)
    return_code = process.wait()
    logger.debug("Command completed with exit code %s: %s", return_code, cmd_args)
    if return_code != 0:
        logger.error("Command failed with exit code %s: %s", return_code, cmd_args)
        raise RuntimeError(f"Command failed with exit code {return_code}.")


def run_bulk_images_upscale_with_progress(cmd_args, total_frames, frames_out_dir, prog_queue, log_queue, phase_start, phase_end):
    logger.debug(
        "Running bulk upscale: cmd=%s total_frames=%s out_dir=%s",
        cmd_args,
        total_frames,
        frames_out_dir,
    )
    process = subprocess.Popen(
        cmd_args,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        bufsize=1,
    )

    def _drain_stdout():
        if process.stdout:
            for line in process.stdout:
                stripped = line.rstrip()
                log_queue.put(stripped)
                logger.debug("Upscaler output: %s", stripped)

    stdout_thread = threading.Thread(target=_drain_stdout, daemon=True)
    stdout_thread.start()

    while process.poll() is None:
        if total_frames > 0:
            out_frames = count_png_files(frames_out_dir)
            percent = (out_frames / total_frames) * 100.0
            prog_queue.put(scale_percent(phase_start, phase_end, percent))
        time.sleep(0.5)

    stdout_thread.join(timeout=2)
    return_code = process.returncode
    logger.debug("Bulk upscale completed with exit code %s: %s", return_code, cmd_args)
    if return_code != 0:
        logger.error("Upscaler command failed with exit code %s: %s", return_code, cmd_args)
        raise RuntimeError("Upscaler command failed with exit code {}.".format(return_code))
