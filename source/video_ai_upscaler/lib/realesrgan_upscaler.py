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

import logging
import os
import shlex
import shutil

from unmanic.libs.unplugins.child_process import PluginChildProcess
from ffmpeg.parser import Parser

from helpers import (
    count_png_files,
    get_plugin_path,
    pick_realesrgan_scale,
    run_bulk_images_upscale_with_progress,
    run_command_with_ffmpeg_progress,
)

logger = logging.getLogger("Unmanic.Plugin.video_ai_upscaler")


class RealEsrganUpscaler:
    def __init__(self, settings, data):
        self.settings = settings
        self.data = data
        self.proc = PluginChildProcess(plugin_id="video_ai_upscaler", data=data)
        profile_dir = settings.get_profile_directory()
        self.bin_dir = os.path.join(profile_dir, "bin")
        self.share_dir = os.path.join(profile_dir, "share")
        os.makedirs(self.bin_dir, exist_ok=True)
        os.makedirs(self.share_dir, exist_ok=True)
        plugin_path = get_plugin_path()
        self.wrapper_dir = os.path.join(plugin_path, "lib", "wrappers")
        self.extract_script = os.path.join(self.wrapper_dir, "extract-frames.sh")
        self.encode_script = os.path.join(self.wrapper_dir, "encode-frames.sh")

    def _resolve_tool(self, scale):
        tool_bin = os.path.join(self.bin_dir, "realesrgan-ncnn-vulkan")
        tool_script = os.path.join(self.wrapper_dir, "realesrgan-upscale.sh")
        model_arg = self.settings.get_setting("realesrgan_model")
        logger.debug(
            "Resolved Real-ESRGAN tool: bin=%s script=%s model=%s scale=%s",
            tool_bin,
            tool_script,
            model_arg,
            scale,
        )
        return tool_bin, tool_script, model_arg, scale

    def _validate_assets(self, tool_bin, tool_script, log_queue):
        if not os.path.exists(tool_bin):
            log_queue.put(f"Tool binary/directory not found at {tool_bin}. Run init.d script?")
            return False
        if not os.path.exists(tool_script):
            log_queue.put(f"Upscale script not found at {tool_script}.")
            return False
        if not os.path.exists(self.extract_script):
            log_queue.put(f"Frame extraction script not found at {self.extract_script}.")
            return False
        if not os.path.exists(self.encode_script):
            log_queue.put(f"Frame encoding script not found at {self.encode_script}.")
            return False
        return True

    def _gpu_arg(self):
        gpu_id = self.settings.get_setting("gpu_id")
        if str(gpu_id).lower() != "auto":
            return f"-g {gpu_id}"
        return ""

    def run(self):
        def _runner(log_queue, prog_queue):
            file_in = self.data.get("file_in")
            file_out = self.data.get("file_out")
            info = self.data.get("probe_info")
            target_height = int(self.settings.get_setting("target_height"))
            tile_size = self.settings.get_setting("tile_size")
            encoding_args = self.settings.get_setting("extra_encoding_args")
            success = True
            source_height = int(self.data.get("source_height", 0) or 0)
            source_width = int(self.data.get("source_width", 0) or 0)
            scale = pick_realesrgan_scale(source_height, target_height)

            log_queue.put(
                "Real-ESRGAN settings: model={}, target_height={}, tile_size={}, gpu_id={}".format(
                    self.settings.get_setting("realesrgan_model"),
                    target_height,
                    tile_size,
                    self.settings.get_setting("gpu_id"),
                )
            )
            log_queue.put(
                "Real-ESRGAN source: {}x{}, selected scale {}".format(
                    source_width,
                    source_height,
                    scale,
                )
            )

            if not file_in or not file_out:
                log_queue.put("Missing file_in/file_out in plugin data.")
                success = False
            if not info:
                log_queue.put("Missing probe_info in plugin data.")
                success = False

            tool_bin, tool_script, model_arg, scale = self._resolve_tool(scale)
            if not self._validate_assets(tool_bin, tool_script, log_queue):
                success = False

            cache_dir = os.path.dirname(file_out)
            temp_dir = os.path.join(cache_dir, "realesrgan_tmp")
            frames_in_dir = os.path.join(temp_dir, "in")
            frames_out_dir = os.path.join(temp_dir, "out")
            gpu_arg = self._gpu_arg()

            try:
                if not success:
                    return
                log_queue.put(
                    "Real-ESRGAN paths: cache_dir={}, frames_in={}, frames_out={}".format(
                        cache_dir,
                        frames_in_dir,
                        frames_out_dir,
                    )
                )
                os.makedirs(frames_in_dir, exist_ok=True)
                os.makedirs(frames_out_dir, exist_ok=True)

                extract_cmd = [
                    "/bin/bash",
                    self.extract_script,
                    file_in,
                    frames_in_dir,
                ]
                extract_cmd_str = " ".join([shlex.quote(str(arg)) for arg in extract_cmd])
                log_queue.put(f"Extract command: {extract_cmd_str}")

                extract_parser = Parser(logger)
                extract_parser.set_probe(info)
                run_command_with_ffmpeg_progress(
                    extract_cmd,
                    extract_parser,
                    prog_queue,
                    log_queue,
                    0,
                    20,
                )

                total_frames = count_png_files(frames_in_dir)
                log_queue.put(f"Extracted {total_frames} frames.")
                if total_frames == 0:
                    raise RuntimeError("No extracted frames found. Aborting upscaler stage.")

                upscale_cmd = [
                    "/bin/bash",
                    tool_script,
                    tool_bin,
                    frames_in_dir,
                    frames_out_dir,
                    model_arg,
                    str(scale),
                    gpu_arg,
                    str(tile_size),
                ]
                upscale_cmd_str = " ".join([shlex.quote(str(arg)) for arg in upscale_cmd])
                log_queue.put(f"Upscale command: {upscale_cmd_str}")

                run_bulk_images_upscale_with_progress(
                    upscale_cmd,
                    total_frames,
                    frames_out_dir,
                    prog_queue,
                    log_queue,
                    20,
                    80,
                )

                encode_cmd = [
                    "/bin/bash",
                    self.encode_script,
                    frames_out_dir,
                    file_in,
                    file_out,
                    str(target_height),
                    encoding_args,
                ]
                encode_cmd_str = " ".join([shlex.quote(str(arg)) for arg in encode_cmd])
                log_queue.put(f"Encode command: {encode_cmd_str}")

                encode_parser = Parser(logger)
                encode_parser.set_probe(info)
                run_command_with_ffmpeg_progress(
                    encode_cmd,
                    encode_parser,
                    prog_queue,
                    log_queue,
                    80,
                    100,
                )
            except Exception as exc:
                log_queue.put(f"Upscale pipeline failed: {exc}")
                logger.exception("Real-ESRGAN pipeline failed")
                success = False
            finally:
                shutil.rmtree(temp_dir, ignore_errors=True)
                if not success:
                    os._exit(1)

        success = self.proc.run(_runner)
        if not success:
            logger.error("Real-ESRGAN upscale failed.")
        return success
