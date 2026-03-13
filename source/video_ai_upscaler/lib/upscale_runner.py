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

try:
    from realesrgan_upscaler import RealEsrganUpscaler
    from waifu2x_upscaler import Waifu2xUpscaler
    from dandere2x_upscaler import Dandere2xUpscaler
except ImportError:
    RealEsrganUpscaler = None
    Waifu2xUpscaler = None
    Dandere2xUpscaler = None

logger = logging.getLogger("Unmanic.Plugin.video_ai_upscaler")


class UpscaleRunner:
    def __init__(self, settings, data):
        self.settings = settings
        self.data = data

    def execute_waifu2x(self):
        if Waifu2xUpscaler is None:
            logger.error("Waifu2x helper not available. Ensure lib/waifu2x_upscaler.py is installed.")
            return False
        upscaler = Waifu2xUpscaler(self.settings, self.data)
        return self._run_in_child(upscaler, "waifu2x")

    def execute_realesrgan(self):
        if RealEsrganUpscaler is None:
            logger.error("Real-ESRGAN helper not available. Ensure lib/realesrgan_upscaler.py is installed.")
            return False
        upscaler = RealEsrganUpscaler(self.settings, self.data)
        return self._run_in_child(upscaler, "realesrgan")

    def execute_dandere2x(self):
        if Dandere2xUpscaler is None:
            logger.error("Dandere2x helper not available. Ensure lib/dandere2x_upscaler.py is installed.")
            return False
        upscaler = Dandere2xUpscaler(self.settings, self.data)
        return self._run_in_child(upscaler, "dandere2x")

    def _run_in_child(self, upscaler, label):
        logger.info(f"Starting {label} upscaling")
        logger.debug("Runner starting with data keys: %s", sorted(self.data.keys()))
        success = upscaler.run()
        if not success:
            logger.error("Upscale command failed.")
        return success
