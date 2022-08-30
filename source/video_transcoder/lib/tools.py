#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
    plugins.tools.py

    Written by:               Josh.5 <jsunnex@gmail.com>
    Date:                     04 Jun 2022, (1:52 PM)

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
import subprocess

from video_transcoder.lib.ffmpeg import StreamMapper

image_video_codecs = [
    'alias_pix',
    'apng',
    'brender_pix',
    'dds',
    'dpx',
    'exr',
    'fits',
    'gif',
    'mjpeg',
    'mjpegb',
    'pam',
    'pbm',
    'pcx',
    'pfm',
    'pgm',
    'pgmyuv',
    'pgx',
    'photocd',
    'pictor',
    'pixlet',
    'png',
    'ppm',
    'ptx',
    'sgi',
    'sunrast',
    'tiff',
    'vc1image',
    'wmv3image',
    'xbm',
    'xface',
    'xpm',
    'xwd',
]

resolution_map = {
    '480p_sdtv':   {
        'width':  854,
        'height': 480,
        'label':  "480p (SDTV)",
    },
    '576p_sdtv':   {
        'width':  1024,
        'height': 576,
        'label':  "576p (SDTV)",
    },
    '720p_hdtv':   {
        'width':  1280,
        'height': 720,
        'label':  "720p (HDTV)",
    },
    '1080p_hdtv':  {
        'width':  1920,
        'height': 1080,
        'label':  "1080p (HDTV)",
    },
    'dci_2k_hdtv': {
        'width':  2048,
        'height': 1080,
        'label':  "DCI 2K (HDTV)",
    },
    '1440p':       {
        'width':  2560,
        'height': 1440,
        'label':  "1440p (WQHD)",
    },
    '4k_uhd':      {
        'width':  3840,
        'height': 2160,
        'label':  "4K (UHD)",
    },
    'dci_4k':      {
        'width':  4096,
        'height': 2160,
        'label':  "DCI 4K",
    },
    '8k_uhd':      {
        'width':  8192,
        'height': 4608,
        'label':  "8k (UHD)",
    },
}


def get_video_stream_data(streams):
    width = 0
    height = 0
    video_stream_index = 0

    for stream in streams:
        if stream.get('codec_type') == 'video':
            width = stream.get('width', stream.get('coded_width', 0))
            height = stream.get('height', stream.get('coded_height', 0))
            video_stream_index = stream.get('index')
            break

    return width, height, video_stream_index


def detect_plack_bars(abspath, probe_data):
    """
    Detect if black bars exist

    Fetch the current video width/height from the file probe


    :param abspath:
    :param probe_data:
    :return:
    """
    logger = logging.getLogger("Unmanic.Plugin.video_transcoder")

    # Fetch the current video width/height from the file probe
    vid_width, vid_height, video_stream_index = get_video_stream_data(probe_data.get('streams'))

    # TODO: Detect video duration. Base the ss param off the duration of the video in the probe data
    duration = 10

    # Run a ffmpeg command to cropdetect
    mapper = StreamMapper(logger, ['video', 'audio', 'subtitle', 'data', 'attachment'])
    mapper.set_input_file(abspath)
    mapper.set_ffmpeg_generic_options(**{"-ss": str(duration)})
    mapper.set_ffmpeg_advanced_options(**{"-vframes": '10', '-vf': 'cropdetect'})
    mapper.set_output_null()

    # Build ffmpeg command for detecting black bars
    # TODO: See if we can support hardware decoding here
    ffmpeg_args = mapper.get_ffmpeg_args()
    ffmpeg_command = ['ffmpeg'] + ffmpeg_args
    # Execute ffmpeg
    pipe = subprocess.Popen(ffmpeg_command, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    out, err = pipe.communicate()
    raw_results = out.decode("utf-8")

    # Parse the output of the ffmpeg command -read the crop value, crop width and crop height into variables
    crop_value = None
    regex = re.compile(r'\[Parsed_cropdetect.*\].*crop=(\d+:\d+:\d+:\d+)')
    findall = re.findall(regex, raw_results)
    if findall:
        crop_value = findall[-1]
    else:
        logger.error("Unable to parse cropdetect from FFmpeg on file %s.", abspath)

    if crop_value:
        crop_width = crop_value.split(':')[0]
        crop_height = crop_value.split(':')[1]

        # If the crop width and crop height are the same as the current video width/height, return None
        if str(crop_width) == str(vid_width) and str(crop_height) == str(vid_height):
            # Video is already cropped to the correct resolution
            logger.debug("File '%s' is already cropped to the resolution %sx%s.", abspath, crop_width, crop_height)
            return None

    return crop_value
