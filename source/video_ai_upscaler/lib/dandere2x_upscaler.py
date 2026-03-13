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
import re
import shlex
import shutil
import subprocess
import time
import yaml

from unmanic.libs.unplugins.child_process import PluginChildProcess
from ffmpeg.parser import Parser

from helpers import run_command_with_ffmpeg_progress, scale_percent

logger = logging.getLogger("Unmanic.Plugin.video_ai_upscaler")


class Dandere2xUpscaler:
    def __init__(self, settings, data):
        self.settings = settings
        self.data = data
        self.proc = PluginChildProcess(plugin_id="video_ai_upscaler", data=data)
        profile_dir = settings.get_profile_directory()
        self.bin_dir = os.path.join(profile_dir, "bin")
        self.share_dir = os.path.join(profile_dir, "share")
        os.makedirs(self.bin_dir, exist_ok=True)
        os.makedirs(self.share_dir, exist_ok=True)
        self.dandere2x_bin = os.path.join(self.bin_dir, "dandere2x")

    def run(self):
        def _runner(log_queue, prog_queue):
            file_in = self.data.get("file_in")
            file_out = self.data.get("file_out")
            target_height = int(self.settings.get_setting("target_height"))
            encoding_args = self.settings.get_setting("extra_encoding_args")
            block_size = self.settings.get_setting("dandere2x_block_size")
            quality = self.settings.get_setting("dandere2x_quality")
            scale_factor = self.settings.get_setting("dandere2x_scale_factor")
            noise_level = self.settings.get_setting("dandere2x_noise_level")
            processing_type = self.settings.get_setting("dandere2x_processing_type")
            processing_type_arg = processing_type
            if processing_type == "single":
                processing_type_arg = "singleprocess"
            elif processing_type == "multi":
                processing_type_arg = "multiprocess"
            if isinstance(scale_factor, int) and scale_factor not in (0, 1, 2):
                log_queue.put(
                    f"Dandere2x scale factor {scale_factor} is unsupported; falling back to 2."
                )
                scale_factor = 2
            d2x_dir = os.path.join(self.share_dir, "dandere2x")
            d2x_src_dir = os.path.join(d2x_dir, "dandere2x", "src")
            success = True

            log_queue.put(
                "Dandere2x settings: block_size={}, quality={}, scale_factor={}, noise_level={}, processing_type={}".format(
                    block_size,
                    quality,
                    scale_factor,
                    noise_level,
                    processing_type_arg,
                )
            )
            log_queue.put(
                "Dandere2x paths: bin_dir={}, share_dir={}, binary={}".format(
                    self.bin_dir,
                    self.share_dir,
                    self.dandere2x_bin,
                )
            )
            log_queue.put(
                "Dandere2x dirs: base_dir={}, cache_dir={}".format(
                    d2x_dir,
                    os.path.dirname(file_out) if file_out else "unknown",
                )
            )
            if os.path.isdir(d2x_src_dir):
                log_queue.put(f"Dandere2x working dir: {d2x_src_dir}")

            if not file_in or not file_out:
                log_queue.put("Missing file_in/file_out in plugin data.")
                success = False
            if not os.path.exists(self.dandere2x_bin):
                log_queue.put(f"Dandere2x binary not found at {self.dandere2x_bin}. Run init.d script?")
                success = False
            if not os.path.isdir(d2x_dir):
                log_queue.put(f"Dandere2x directory not found at {d2x_dir}. Run init.d script?")
                success = False
            if os.path.isdir(d2x_src_dir):
                config_path = os.path.join(d2x_src_dir, "config_files", "output_options.yaml")
                if not os.path.exists(config_path):
                    log_queue.put(f"Dandere2x config not found at {config_path}. Run init.d script?")
                    success = False
                else:
                    # Patch config if needed using YAML parser
                    try:
                        with open(config_path, "r") as f:
                            config = yaml.safe_load(f)
                        
                        modified = False
                        # Navigate to ffmpeg -> pipe_video -> output_options
                        pipe_video = config.get('ffmpeg', {}).get('pipe_video', {})
                        output_options = pipe_video.get('output_options', {})
                        
                        if output_options:
                            # 1. Log level
                            if output_options.get('-loglevel') != 'info':
                                output_options['-loglevel'] = 'info'
                                modified = True
                                log_queue.put("Patched Dandere2x config: Enabled info logging.")
                            
                            # 2. Input codec (-vcodec mjpeg)
                            # We must ensure output codec doesn't conflict. 
                            # If -vcodec is libx264, it's definitely the output codec.
                            if output_options.get('-vcodec') == 'libx264':
                                output_options['-c:v'] = 'libx264'
                                del output_options['-vcodec']
                                modified = True
                                log_queue.put("Patched Dandere2x config: Renamed output codec key to -c:v.")

                            if output_options.get('-vcodec') != 'mjpeg':
                                # To ensure it's an input option for FFmpeg, it ideally should be early.
                                # Python dicts (3.7+) preserve order. We'll just set it.
                                output_options['-vcodec'] = 'mjpeg'
                                modified = True
                                log_queue.put("Patched Dandere2x config: Set input codec to mjpeg.")

                            if modified:
                                with open(config_path, "w") as f:
                                    yaml.dump(config, f, default_flow_style=False)
                    except Exception as e:
                        log_queue.put(f"Error patching Dandere2x config with YAML: {e}")

            cache_dir = os.path.dirname(file_out) if file_out else None
            temp_dir = os.path.join(cache_dir, "dandere2x_tmp") if cache_dir else None
            os.makedirs(temp_dir, exist_ok=True)
            intermediate = os.path.join(temp_dir, "dandere2x_intermediate.mkv")

            cmd = [
                self.dandere2x_bin,
                "-i",
                file_in,
                "-o",
                intermediate,
                "-ws",
                temp_dir,
            ]
            if block_size is not None:
                cmd.extend(["-b", str(block_size)])
            if quality is not None:
                cmd.extend(["-q", str(quality)])
            cmd.extend(["-w", "vulkan"])
            if isinstance(scale_factor, int) and scale_factor > 0:
                cmd.extend(["-s", str(scale_factor)])
            if isinstance(noise_level, int) and noise_level > 0:
                cmd.extend(["-n", str(noise_level)])
            if processing_type_arg:
                cmd.extend(["-p", str(processing_type_arg)])
            cmd_str = " ".join([shlex.quote(str(arg)) for arg in cmd])
            log_queue.put(f"Dandere2x command: {cmd_str}")
            logger.debug(f"Dandere2x command: {cmd_str}")

            try:
                if not success:
                    return
                prog_queue.put(0)

                process = subprocess.Popen(
                    cmd,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT,
                    text=True,
                    bufsize=1,
                    cwd=d2x_src_dir if os.path.isdir(d2x_src_dir) else None,
                )

                error_detected = False
                error_time = 0
                error_message = ""

                if process.stdout:
                    for line in process.stdout:
                        stripped = line.rstrip()
                        log_queue.put(stripped)
                        logger.debug("Dandere2x output: %s", stripped)

                        if "Exception" in stripped or "Traceback" in stripped or "BrokenPipeError" in stripped:
                            if not error_detected:
                                logger.error(f"Dandere2x Error Detected: {stripped}")
                                error_detected = True
                                error_time = time.time()
                                error_message = stripped

                        if error_detected:
                            if time.time() - error_time > 10:
                                logger.error("Dandere2x error timeout reached. Killing process.")
                                process.kill()
                                raise RuntimeError(f"Dandere2x failed: {error_message}")

                        match = re.search(r"Frame: \[\d+\] (\d+)%", stripped)
                        if match:
                            try:
                                percent = int(match.group(1))
                                prog_queue.put(scale_percent(0, 80, percent))
                            except (ValueError, IndexError):
                                pass
                
                return_code = process.wait()
                
                if error_detected:
                    raise RuntimeError(f"Dandere2x failed (detected in logs): {error_message}")

                if return_code != 0:
                    raise RuntimeError(f"Dandere2x command failed with exit code {return_code}.")
                prog_queue.put(80)

                if not os.path.exists(intermediate):
                    raise RuntimeError("Dandere2x output file not found after run.")

                encode_cmd = [
                    "ffmpeg",
                    "-hide_banner",
                    "-loglevel",
                    "info",
                    "-y",
                    "-i",
                    intermediate,
                    "-i",
                    file_in,
                    "-map",
                    "0:v",
                    "-map",
                    "1:a?",
                    "-map",
                    "1:s?",
                ]
                if encoding_args:
                    encode_cmd.extend(shlex.split(encoding_args))
                encode_cmd.extend([
                    "-vf",
                    f"scale=-2:{target_height}",
                    "-c:a",
                    "copy",
                    "-c:s",
                    "copy",
                    file_out,
                ])
                encode_cmd_str = " ".join([shlex.quote(str(arg)) for arg in encode_cmd])
                log_queue.put(f"Encode command: {encode_cmd_str}")
                logger.debug(f"Encode command: {encode_cmd_str}")

                encode_parser = Parser(logger)
                encode_parser.set_probe(self.data.get("probe_info"))
                run_command_with_ffmpeg_progress(
                    encode_cmd,
                    encode_parser,
                    prog_queue,
                    log_queue,
                    80,
                    100,
                )
            except Exception as exc:
                log_queue.put(f"Dandere2x pipeline failed: {exc}")
                logger.exception("Dandere2x pipeline failed")
                success = False
            finally:
                shutil.rmtree(temp_dir, ignore_errors=True)
                if not success:
                    os._exit(1)

        success = self.proc.run(_runner)
        if not success:
            logger.error("Dandere2x upscale failed.")
        return success
