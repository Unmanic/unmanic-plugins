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
import sys
import subprocess

from unmanic.libs.unplugins.settings import PluginSettings

# Add lib to path
sys.path.append(os.path.join(os.path.dirname(__file__), "lib"))
try:
    from ffmpeg.probe import ffprobe_file
    from ffmpeg.probe import Probe
    from upscale_runner import UpscaleRunner
    from helpers import get_latest_waifu2x_dir
except ImportError:
    UpscaleRunner = None
    Probe = None

    def get_latest_waifu2x_dir(_share_dir):
        return None

# Configure plugin logger
logger = logging.getLogger("Unmanic.Plugin.video_ai_upscaler")
COMMON_TARGET_HEIGHTS = [480, 720, 1080, 1440, 2048, 2160]


class Settings(PluginSettings):
    settings = {
        "upscaler_tool": "dandere2x",
        "realesrgan_model": "realesrgan-x4plus",
        "waifu2x_model": "models-cunet",
        "waifu2x_noise_level": 0,
        "dandere2x_block_size": 30,
        "dandere2x_quality": 85,
        "dandere2x_scale_factor": 2,
        "dandere2x_noise_level": 3,
        "dandere2x_processing_type": "single",
        "tile_size": 0,
        "gpu_id": "auto",
        "target_height": 1080,
        "ignore_near_target_height": True,
        "extra_encoding_args": "-c:v libx264 -crf 20 -preset fast"
    }

    def __init__(self, *args, **kwargs):
        super(Settings, self).__init__(*args, **kwargs)
        # Dynamically build form settings
        self.form_settings = self.__build_form_settings_object()

    def __build_form_settings_object(self):
        """
        Dynamically build form settings based on current state
        """
        form = {}

        # 1. Upscaler Tool
        form["upscaler_tool"] = {
            "label": "Upscaler Tool",
            "input_type": "select",
            "select_options": [
                {"value": "dandere2x", "label": "Dandere2x"},
                {"value": "realesrgan", "label": "realesrgan-ncnn-vulkan"},
                {"value": "waifu2x", "label": "waifu2x-ncnn-vulkan"},
            ],
        }

        # 2. GPU ID (Dynamic)
        gpu_options = [{"value": "auto", "label": "Auto"}]
        try:
            if subprocess.call("command -v vulkaninfo", shell=True, stdout=subprocess.DEVNULL) == 0:
                output = subprocess.check_output(["vulkaninfo", "--summary"], stderr=subprocess.STDOUT).decode("utf-8")
                current_gpu = None
                for line in output.splitlines():
                    line = line.strip()
                    if line.startswith("GPU"):
                        parts = line.split(":")
                        if len(parts) > 0 and parts[0].startswith("GPU"):
                            current_gpu = parts[0].replace("GPU", "")
                    if current_gpu is not None and line.startswith("deviceName"):
                        name = line.split("=")[1].strip()
                        gpu_options.append({"value": current_gpu, "label": f"{current_gpu}: {name}"})
                        current_gpu = None
        except Exception as e:
            logger.debug(f"Failed to get vulkan info: {e}")

        form["gpu_id"] = {
            "label": "GPU ID",
            "input_type": "select",
            "select_options": gpu_options,
        }

        # 3. Models (Conditional Visibility)
        selected_tool = self.get_setting("upscaler_tool")

        # Dandere2x Settings
        form["dandere2x_block_size"] = {
            "label": "Dandere2x Block Size",
            "input_type": "number",
            "description": "Block size for Dandere2x (default 30).",
            "display": "visible" if selected_tool == "dandere2x" else "hidden",
            "sub_setting": True,
        }

        form["dandere2x_quality"] = {
            "label": "Dandere2x Image Quality",
            "input_type": "number",
            "description": "Image quality for Dandere2x output (default 85).",
            "display": "visible" if selected_tool == "dandere2x" else "hidden",
            "sub_setting": True,
        }

        form["dandere2x_scale_factor"] = {
            "label": "Dandere2x Scale Factor",
            "input_type": "select",
            "select_options": [
                {"value": 0, "label": "0 (auto)"},
                {"value": 1, "label": "1"},
                {"value": 2, "label": "2"},
            ],
            "description": "Dandere2x scale factor (0 omits the flag, default 2).",
            "display": "visible" if selected_tool == "dandere2x" else "hidden",
            "sub_setting": True,
        }

        form["dandere2x_noise_level"] = {
            "label": "Dandere2x Noise Level",
            "input_type": "select",
            "select_options": [
                {"value": 0, "label": "0 (off)"},
                {"value": 1, "label": "1"},
                {"value": 2, "label": "2"},
                {"value": 3, "label": "3"},
            ],
            "description": "Dandere2x denoise level (0 omits the flag, default 3).",
            "display": "visible" if selected_tool == "dandere2x" else "hidden",
            "sub_setting": True,
        }

        form["dandere2x_processing_type"] = {
            "label": "Dandere2x Processing Type",
            "input_type": "select",
            "select_options": [
                {"value": "single", "label": "single"},
                {"value": "multi", "label": "multi"},
            ],
            "description": "Processing mode for Dandere2x (single or multi).",
            "display": "visible" if selected_tool == "dandere2x" else "hidden",
            "sub_setting": True,
        }

        # Real-ESRGAN Model
        form["realesrgan_model"] = {
            "label": "Real-ESRGAN Model",
            "input_type": "select",
            "select_options": [
                {
                    "value": "realesrgan-x4plus",
                    "label": "realesrgan-x4plus (default)"
                },
                {
                    "value": "realesrnet-x4plus",
                    "label": "realesrnet-x4plus"
                },
                {
                    "value": "realesrgan-x4plus-anime",
                    "label": "realesrgan-x4plus-anime (optimized for anime images, small model size)"
                },
                {
                    "value": "realesr-animevideov3",
                    "label": "realesr-animevideov3 (animation video)"
                },
            ],
            "display": "visible" if selected_tool == "realesrgan" else "hidden",
            "sub_setting": True,
        }

        # Waifu2x Model
        waifu2x_options = []
        profile_dir = self.get_profile_directory()
        share_dir = os.path.join(profile_dir, "share")
        waifu2x_base_dir = get_latest_waifu2x_dir(share_dir)
        if not waifu2x_base_dir:
            waifu2x_base_dir = os.path.join(share_dir, "waifu2x-ncnn-vulkan")
        if waifu2x_base_dir and os.path.exists(waifu2x_base_dir):
            for item in os.listdir(waifu2x_base_dir):
                if item.startswith("models-"):
                    waifu2x_options.append({"value": item, "label": item})

        form["waifu2x_model"] = {
            "label": "Waifu2x Model",
            "input_type": "select",
            "select_options": waifu2x_options if waifu2x_options else [{"value": "models-cunet", "label": "models-cunet"}],
            "display": "visible" if selected_tool == "waifu2x" else "hidden",
            "sub_setting": True,
        }

        form["waifu2x_noise_level"] = {
            "label": "Waifu2x Noise Level",
            "input_type": "select",
            "select_options": [
                {"value": -1, "label": "-1 (none)"},
                {"value": 0, "label": "0 (low)"},
                {"value": 1, "label": "1"},
                {"value": 2, "label": "2"},
                {"value": 3, "label": "3 (high)"},
            ],
            "description": "Noise reduction level passed to waifu2x (-1 disables denoise).",
            "display": "visible" if selected_tool == "waifu2x" else "hidden",
            "sub_setting": True,
        }

        form["tile_size"] = {
            "label": "Tile Size",
            "input_type": "slider",
            "slider_options": {
                "min": 0,
                "max": 32,
                "step": 1,
                "suffix": "px",
            },
            "description": "Tile size for the upscaler. Use 0 for auto. Lower values reduce VRAM usage but may be slower.",
            "display": "hidden" if selected_tool == "dandere2x" else "visible",
        }

        form["target_height"] = {
            "label": "Target Height (Output Resolution)",
            "input_type": "select",
            "select_options": [
                {"value": height, "label": "2k" if height == 2048 else "4k" if height == 2160 else f"{height}p"}
                for height in COMMON_TARGET_HEIGHTS
            ],
            "description": (
                "Set the output height in pixels (e.g., 1080 or 2160). "
                "If the source height is already >= this value, the file is skipped. "
                "Upscaled frames are scaled to this height for the final encode."
            ),
            "tooltip": "Pick a target height (pixels). Invalid values fall back to the default.",
        }

        form["ignore_near_target_height"] = {
            "label": "Ignore files whose height is close to the selected target height",
            "input_type": "checkbox",
            "description": (
                "When enabled, files within 20% of the target height are skipped."
            ),
            "sub_setting": True,
        }

        form["extra_encoding_args"] = {
            "label": "FFmpeg Video Encoder Args",
            "input_type": "string",
            "description": (
                "FFmpeg arguments for the final video encode. "
                "Example: -c:v libx264 -crf 20 -preset fast. "
                "Audio and subtitles are copied from the source."
            ),
        }

        return form

    def get_target_height(self):
        value = self.get_setting("target_height")
        try:
            value = int(str(value).strip())
        except (TypeError, ValueError):
            logger.warning(
                "Invalid target_height %r; falling back to default %s",
                value,
                self.settings["target_height"],
            )
            value = self.settings["target_height"]
        if value < 1:
            logger.warning(
                "target_height %r is < 1; falling back to default %s",
                value,
                self.settings["target_height"],
            )
            value = self.settings["target_height"]
        return value


def is_already_target_height(settings, info):
    """
    Return True when a file should be treated as already at target height.
    """
    if not info:
        logger.info("No ffprobe data available; treating file as already at target height.")
        return True
    video_stream = None
    for stream in info.get('streams', []):
        if stream.get('codec_type') == 'video' and video_stream is None:
            video_stream = stream
            break
    if not video_stream:
        logger.info("No video stream found in ffprobe data; treating file as already at target height.")
        return True
    src_height = int(video_stream.get('height', 0) or 0)
    target_height = settings.get_target_height()
    if src_height <= 0 or target_height <= 0:
        logger.info(
            "Invalid source/target height (source=%s target=%s); treating file as already at target height.",
            src_height,
            target_height,
        )
        return True
    if src_height >= target_height:
        logger.info(
            "Source height %s is at or above target %s; treating file as already at target height.",
            src_height,
            target_height,
        )
        return True
    if settings.get_setting("ignore_near_target_height") and src_height >= int(target_height * 0.8):
        logger.info(
            "Source height %s is within 20%% of target %s; treating file as already at target height.",
            src_height,
            target_height,
        )
        return True
    logger.info(
        "Source height %s is below target %s; file should be processed.",
        src_height,
        target_height,
    )
    return False


def on_library_management_file_test(data):
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
    settings = Settings(library_id=data.get('library_id'))
    if Probe is None:
        logger.error("Probe helper not available. Ensure lib/ffmpeg/probe.py is installed.")
        return

    data.setdefault("issues", [])
    probe_info = None
    probe = Probe(logger, allowed_mimetypes=['video'])
    if 'ffprobe' in data.get('shared_info', {}):
        if not probe.set_probe(data.get('shared_info', {}).get('ffprobe')):
            return
        probe_info = probe.get_probe()
    elif probe.file(data.get('path')):
        probe_info = probe.get_probe()
        if 'shared_info' not in data:
            data['shared_info'] = {}
        data['shared_info']['ffprobe'] = probe_info
    else:
        return

    src_height = 0
    target_height = settings.get_target_height()
    for stream in probe_info.get('streams', []):
        if stream.get('codec_type') == 'video':
            src_height = int(stream.get('height', 0) or 0)
            break

    if is_already_target_height(settings, probe_info):
        issue_id = "height_at_or_above_target"
        message = "File '{}' is already at or above target height ({})."
        if settings.get_setting("ignore_near_target_height") and src_height < target_height:
            issue_id = "near_target_height"
            message = "File '{}' is within 20% of the target height ({})."
        data["issues"].append({
            "id": issue_id,
            "message": message.format(data.get("path"), settings.get_target_height()),
        })
        return
    data["add_file_to_pending_tasks"] = True


def on_worker_process(data):
    """
    Runner function - enables additional configured processing jobs during the worker stages of a task.

    The 'data' object argument includes:
        task_id                 - Integer, unique identifier of the task.
        worker_log              - Array, the log lines that are being tailed by the frontend. Can be left empty.
        library_id              - Number, the library that the current task is associated with.
        exec_command            - Array, a subprocess command that Unmanic should execute. Can be empty.
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

        from unmanic.libs.unplugins.child_process import PluginChildProcess

        proc = PluginChildProcess(plugin_id="<your_plugin_id>", data=data)

        def child_work(log_queue, prog_queue):
            # any Python code here
            for i in range(10):
                # emit a UI log line:
                log_queue.put(f"step {i}/10 completed")
                # emit progress 0–100:
                prog_queue.put((i + 1) * 10)
                time.sleep(1)

        # Runs child_work in its own process, returns True if exit code==0
        success = proc.run(child_work)

    In this mode the `PluginChildProcess` helper:
      1. Spawns the child via `multiprocessing.Process`.  
      2. Registers its PID & start‐time with the worker’s `default_progress_parser`.  
      3. Drains `log_queue` → `data["worker_log"]` for UI tail.  
      4. Drains `prog_queue` → `command_progress_parser(line_text)` to update the progress bar.  
      5. Will unset the child process PID on exit to reset all tracked subprocess metrics in the Unmanic Worker (CPU, memory, progress, etc.).

    :param data:
    :return:
    """
    settings = Settings(library_id=data.get('library_id'))

    file_in = data['file_in']
    file_out = data['file_out']
    profile_dir = settings.get_profile_directory()
    bin_dir = os.path.join(profile_dir, "bin")
    share_dir = os.path.join(profile_dir, "share")
    os.makedirs(bin_dir, exist_ok=True)
    os.makedirs(share_dir, exist_ok=True)

    # 1. Probe the file
    try:
        from ffmpeg.probe import ffprobe_file
        info = ffprobe_file(file_in)
    except Exception as e:
        logger.error(f"Failed to probe file '{file_in}': {e}")
        return
    data["probe_info"] = info

    # 2. Get video stream info
    video_stream = None
    for stream in info.get('streams', []):
        if stream.get('codec_type') == 'video' and video_stream is None:
            video_stream = stream
            break

    if not video_stream:
        logger.warning(f"No video stream found in '{file_in}'.")
        return

    src_height = int(video_stream.get('height', 0))
    src_width = int(video_stream.get('width', 0))
    data["source_height"] = src_height
    data["source_width"] = src_width
    target_height = settings.get_target_height()

    if is_already_target_height(settings, info):
        if settings.get_setting("ignore_near_target_height") and src_height < target_height:
            logger.info(
                "File height is within 20%% of target height (%s). Skipping upscaling.",
                settings.get_target_height(),
            )
        else:
            logger.info(
                f"File resolution {src_width}x{src_height} is already >= target height {target_height}. Skipping upscaling.")
        return

    source_step = 0
    for index, height in enumerate(COMMON_TARGET_HEIGHTS):
        if src_height >= height:
            source_step = index
        else:
            break
    try:
        target_step = COMMON_TARGET_HEIGHTS.index(target_height)
    except ValueError:
        target_step = source_step
    if target_step - source_step > 2:
        logger.warning(
            "Target height %sp is more than two steps above source %sp; expect longer runtimes.",
            target_height,
            src_height,
        )

    # 4. Prepare paths and commands
    upscaler_tool = settings.get_setting("upscaler_tool")
    logger.info(
        "Upscaler selection: tool=%s target_height=%s tile_size=%s gpu_id=%s",
        upscaler_tool,
        target_height,
        settings.get_setting("tile_size"),
        settings.get_setting("gpu_id"),
    )

    if UpscaleRunner is None:
        logger.error("Upscale helper class not available. Ensure lib/upscale_runner.py is installed.")
        return

    logger.info(f"Starting {upscaler_tool} upscaling: {src_height}p -> {target_height}p")
    runner = UpscaleRunner(settings, data)
    if upscaler_tool == "dandere2x":
        runner.execute_dandere2x()
    elif upscaler_tool == "realesrgan":
        runner.execute_realesrgan()
    elif upscaler_tool == "waifu2x":
        runner.execute_waifu2x()
