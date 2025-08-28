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
import shlex
import subprocess
from collections import Counter
from typing import List, Optional, Iterable

from video_transcoder.lib.encoders.libx import LibxEncoder
from video_transcoder.lib.encoders.libsvtav1 import LibsvtAv1Encoder
from video_transcoder.lib.encoders.qsv import QsvEncoder
from video_transcoder.lib.encoders.vaapi import VaapiEncoder
from video_transcoder.lib.encoders.nvenc import NvencEncoder
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


def available_encoders(settings=None, probe=None):
    return_encoders = {}
    encoder_libs = [
        LibxEncoder,
        LibsvtAv1Encoder,
        QsvEncoder,
        VaapiEncoder,
        NvencEncoder,
    ]
    for encoder_class in encoder_libs:
        encoder_lib = encoder_class(settings=settings, probe=probe)
        for encoder in encoder_lib.provides():
            return_encoders[encoder] = encoder_lib
    return return_encoders


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


def format_command_multiline(mapper, max_width=120, indent="  "):
    """
    Prints command for debugging...
    Pretty-print a shell command with flag/value grouping and hard wraps.

    - max_width: wrap line when it would exceed this width
    - indent: indent used at the start of wrapped lines
    """

    ffmpeg_args = mapper.get_ffmpeg_args()
    cmd = ['ffmpeg']
    cmd += ffmpeg_args

    # Quote everything for safe copy/paste
    q = [shlex.quote(x) for x in cmd]

    # Head is the binary; tail are the arguments we want to group/wrap
    head, tail = q[0], q[1:]

    # Group (flag + value) when it's "-something" followed by a non-flag token
    chunks = []
    i = 0
    while i < len(tail):
        cur = tail[i]
        nxt = tail[i + 1] if i + 1 < len(tail) else None
        if cur.startswith("-") and nxt is not None and not nxt.startswith("-"):
            chunks.append(f"{cur} {nxt}")
            i += 2
        else:
            chunks.append(cur)
            i += 1

    # Now wrap into lines <= max_width
    lines = [head]  # start with the binary on the first line
    cur = head
    for chunk in chunks:
        # try to append to current line
        attempt = f"{cur} {chunk}"
        if len(attempt) <= max_width:
            cur = attempt
            lines[-1] = cur
        else:
            # wrap to a new line
            cur = f"{indent}{chunk}"
            lines.append(cur)

    # Join with line continuations
    return " \\\n".join(lines)


def join_filtergraph(filter_id, filter_args, stream_id):
    """
    Joins a filtergraph from a collection of args
    """
    filtergraph = ''
    count = 1
    for filter_string in filter_args:
        # If we are appending to existing filters, separate by a semicolon to start a new chain
        if filtergraph:
            filtergraph += ';'
        # Add the input for this filter
        filtergraph += '[{}]'.format(filter_id)
        # Add filtergraph
        filtergraph += '{}'.format(filter_string)
        # Update filter ID and add it to the end
        filter_id = '0:vf:{}-{}'.format(stream_id, count)
        filtergraph += '[{}]'.format(filter_id)
        # Increment filter ID counter
        count += 1
    return filter_id, filtergraph


def detect_black_bars(abspath, probe_data, settings):
    """
    Detect black bars via ffmpeg cropdetect using quorum logic across multiple samples.

    Quorum rules:
      - Need at least 2 passes; if first two are identical => stop with that result.
      - If first two differ, take a 3rd pass; if 2-of-3 agree => use that.
      - If still inconclusive, continue sampling on the cadence until a majority emerges,
        or we exhaust feasible windows. 'No crop' is a valid quorum result.

    Sampling rules:
      - If duration < 60s: one pass over the WHOLE file (no -t window).
      - If duration unknown: start at 0s, sample 10s every 30s.
      - If 60s ≤ duration ≤ 5min: sample 10s every 60s, starting at 30s.
      - If duration > 5min: sample 20s, starting at 60s, every 5 minutes (assumption; see note).

    Returns:
      - crop string "w:h:x:y" if a non-trivial crop quorum is reached,
      - None if quorum yields 'no crop' or we cannot determine a stable crop.
    """
    logger = logging.getLogger("Unmanic.Plugin.video_transcoder")

    # -------------------------
    # Helpers
    # -------------------------
    def _get_video_duration_seconds_from_probe(_probe) -> Optional[float]:
        fmt = _probe.get("format") if isinstance(_probe, dict) else None
        if isinstance(fmt, dict):
            dur = fmt.get("duration")
            if dur is not None:
                try:
                    return float(dur)
                except (TypeError, ValueError):
                    pass
        streams = _probe.get("streams") if isinstance(_probe, dict) else None
        if isinstance(streams, list):
            for s in streams:
                if s.get("codec_type") == "video":
                    dur = s.get("duration")
                    if dur is not None:
                        try:
                            return float(dur)
                        except (TypeError, ValueError):
                            pass
        if isinstance(fmt, dict) and isinstance(fmt.get("tags"), dict):
            t = fmt["tags"]
            ts = t.get("DURATION")
            if ts and isinstance(ts, str):
                parts = ts.split(":")
                if len(parts) >= 3:
                    try:
                        h = float(parts[0]);
                        m = float(parts[1]);
                        s = float(parts[2])
                        return h * 3600 + m * 60 + s
                    except (TypeError, ValueError):
                        pass
        return None

    def _parse_last_cropdetect(output_text: str) -> Optional[str]:
        # Extract the last reported crop=WxH:X:Y
        m = re.findall(r'\[Parsed_cropdetect.*\].*crop=(\d+:\d+:\d+:\d+)', output_text)
        return m[-1] if m else None

    def _get_pix_fmt(streams) -> Optional[str]:
        if isinstance(streams, list):
            for s in streams:
                if s.get("codec_type") == "video":
                    return s.get("pix_fmt")
        return None

    def _choose_round_and_minbar(pix_fmt: Optional[str]) -> tuple[int, int]:
        """
        Pick crop rounding & minimum bar threshold:
          - 4:2:0 or 4:2:2 -> even alignment (mod 2) is required for safe chroma placement
          - min_bar_px guards against 1–2 px micro-crops causing loops
        """
        if pix_fmt and ("420" in pix_fmt or "422" in pix_fmt):
            return 2, 6  # round to even; ignore <6 px bars
        # 4:4:4 or unknown: even is still safe everywhere
        return 2, 6

    def _normalise_crop_or_nocrop(crop_str: str, src_w: int, src_h: int,
                                  min_sum_tb: int,
                                  r_to: int,
                                  min_bar_lr: int = 6) -> str:
        """
        Normalize crop from cropdetect. Enforces:
          - vertical guard: if (top + bottom) < min_sum_tb -> no vertical crop
          - horizontal guard: left/right < min_bar_lr individually -> zero them (optional safety)
          - round offsets/dims down to multiples of r_to
        Returns 'w:h:x:y' or 'NO_CROP'.
        """
        if not crop_str or ":" not in crop_str:
            return "NO_CROP"

        w_s, h_s, x_s, y_s = crop_str.split(":")
        w, h, x, y = int(w_s), int(h_s), int(x_s), int(y_s)

        # Native size -> no crop
        if w == src_w and h == src_h and x == 0 and y == 0:
            return "NO_CROP"

        # Bars from the raw suggestion
        top = y
        left = x
        bottom = src_h - (y + h)
        right = src_w - (x + w)

        # --- Vertical "sum" rule ---
        if (top + bottom) < min_sum_tb:
            top = 0
            bottom = 0

        # --- Horizontal micro-crop guard (optional but prevents 1–2 px pillarbox loops) ---
        def too_small(v: int, thr: int) -> bool:
            return 0 < v < thr

        if too_small(left, min_bar_lr):  left = 0
        if too_small(right, min_bar_lr):  right = 0

        # If nothing remains to trim, skip
        if top == 0 and bottom == 0 and left == 0 and right == 0:
            return "NO_CROP"

        # Rebuild crop rectangle from (possibly modified) bars
        x_n = left
        y_n = top
        w_n = src_w - left - right
        h_n = src_h - top - bottom
        if w_n <= 0 or h_n <= 0:
            return "NO_CROP"

        # Round down for alignment
        def rdown(v: int, m: int) -> int:
            return (v // m) * m if m > 1 else v

        x_r = rdown(x_n, r_to)
        y_r = rdown(y_n, r_to)
        w_r = rdown(w_n, r_to)
        h_r = rdown(h_n, r_to)

        # Keep inside frame
        if x_r + w_r > src_w:
            w_r = rdown(src_w - x_r, r_to)
        if y_r + h_r > src_h:
            h_r = rdown(src_h - y_r, r_to)

        # Recompute bars after rounding
        top_r = y_r
        left_r = x_r
        bottom_r = src_h - (y_r + h_r)
        right_r = src_w - (x_r + w_r)

        # Re-apply vertical sum guard AFTER rounding (rounding can lower the sum)
        if (top_r + bottom_r) < min_sum_tb:
            # remove vertical crop, keep horizontal if any
            top_r = 0
            bottom_r = 0
            y_r = 0
            h_r = src_h - (top_r + bottom_r)
            # re-round height to alignment
            h_r = rdown(h_r, r_to)
            if y_r + h_r > src_h:
                h_r = rdown(src_h - y_r, r_to)
            # recompute bars after adjusting verticals
            bottom_r = src_h - (y_r + h_r)

        # Re-apply horizontal micro guard after rounding
        if too_small(left_r, min_bar_lr):
            left_r = 0
            x_r = 0
            w_r = rdown(src_w - right_r, r_to)
        if too_small(right_r, min_bar_lr):
            right_r = 0
            w_r = rdown(src_w - x_r, r_to)

        # If after all guards there's no crop left, bail
        if top_r == 0 and bottom_r == 0 and left_r == 0 and right_r == 0:
            return "NO_CROP"

        # Native after rounding? -> no crop
        if w_r == src_w and h_r == src_h and x_r == 0 and y_r == 0:
            return "NO_CROP"

        # Log normalization if the rect changed
        if (x_r, y_r, w_r, h_r) != (x, y, w, h):
            logger.debug("[BB Detection][Safety] Normalised crop %s -> %d:%d:%d:%d (bars t=%d,b=%d,l=%d,r=%d)",
                         crop_str, w_r, h_r, x_r, y_r, top_r, bottom_r, left_r, right_r)

        return f"{w_r}:{h_r}:{x_r}:{y_r}"

    def _ffmpeg_sample(ss: int, t_seconds: Optional[int], r_to: Optional[int], enable_hw_accel=False) -> str:
        # NOTE: After adding HW accel, I actually found it to be slower.
        #   I am leaving the code here with a switch enable_hw_accel incase I come back to test further later on.
        mapper = StreamMapper(logger, ['video', 'audio', 'subtitle', 'data', 'attachment'])
        mapper.set_input_file(abspath)

        # Figure out which video stream we're filtering
        _, _, video_stream_index = get_video_stream_data(probe_data.get('streams'))
        # Fallback to 0 if probe didn't return a valid index
        stream_id = str(video_stream_index if video_stream_index is not None else 0)

        # Configure the cropdetect filter
        filter_args = [f"cropdetect=mode=black:round={r_to}:reset=0"]

        # Build hardware acceleration args based on encoder
        # Note: these are not applied to advanced mode - advanced mode was returned above
        encoder_name = settings.get_setting('video_encoder')
        encoder_lib = available_encoders(settings=settings).get(encoder_name)
        if enable_hw_accel and encoder_lib:
            encoder_lib.set_probe(probe_info=probe_data)
            generic_kwargs, advanced_kwargs = encoder_lib.generate_default_args()
            mapper.set_ffmpeg_generic_options(**generic_kwargs)
            mapper.set_ffmpeg_advanced_options(**advanced_kwargs)

            filtergraph_config = encoder_lib.generate_filtergraphs(
                filter_args,
                [],
                encoder_name
            )

            generic_kwargs = filtergraph_config.get('generic_kwargs', {})
            mapper.set_ffmpeg_generic_options(**generic_kwargs)

            advanced_kwargs = filtergraph_config.get('advanced_kwargs', {})
            mapper.set_ffmpeg_advanced_options(**advanced_kwargs)

            start_filter_args = filtergraph_config.get('start_filter_args', [])
            end_filter_args = filtergraph_config.get('end_filter_args', [])
            filter_args = start_filter_args + filter_args + end_filter_args

        # Join filtergraph
        filter_id = '0:v:{}'.format(stream_id)
        filter_id, filtergraph = join_filtergraph(filter_id, filter_args, stream_id)

        # Seek to the sample start
        mapper.set_ffmpeg_generic_options(**{"-ss": str(int(ss))})

        # Ingore non-video streams and insert filter
        adv_args = ["-an", "-sn", "-dn"]
        adv_kwargs = {
            "-filter_complex": filtergraph,
            "-map":            f"[{filter_id}]",
        }
        if t_seconds and t_seconds > 0:
            mapper.set_ffmpeg_generic_options(**{"-t": str(int(t_seconds))})
        mapper.set_ffmpeg_advanced_options(*adv_args, **adv_kwargs)
        mapper.set_output_null()

        ffmpeg_command = ['ffmpeg'] + mapper.get_ffmpeg_args()
        pipe = subprocess.Popen(ffmpeg_command, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        out, _ = pipe.communicate()
        raw = out.decode("utf-8", errors="replace")

        crop = _parse_last_cropdetect(raw)
        return crop if crop else "NO_CROP"

    def _gen_starts_known(total: float, first_start: int, step_between_starts: int, window: int, limit: int) -> Iterable[int]:
        """
        Generate start times so that each window fits within media (best-effort), up to 'limit' samples.
        'step_between_starts' is the distance between window starts, *not* the gap itself.
        """
        # Ensure we don't start too close to EOF; keep a 1s buffer
        max_start = max(0, int(total) - (window if window else 0) - 1)
        s = max(0, int(first_start))
        count = 0
        while s <= max_start and count < limit:
            yield s
            s += int(step_between_starts)
            count += 1

    def _quorum(last_three: List[str]) -> Optional[str]:
        """
        Given up to the last 3 observations, return:
          - crop string if ≥2 agree on a non-'NO_CROP' value
          - None if ≥2 are 'NO_CROP'
          - None if no majority yet
        """
        if len(last_three) < 2:
            return None
        if len(last_three) == 2:
            a, b = last_three
            if a == b:
                return None if a == "NO_CROP" else a
            return None  # need a third to decide
        # len == 3
        counts = Counter(last_three)
        # Prefer a non-trivial crop
        for val, cnt in counts.most_common():
            if val != "NO_CROP" and cnt >= 2:
                return val
        if counts.get("NO_CROP", 0) >= 2:
            return None
        return None

    # -------------------------
    # Probe & scheduling
    # -------------------------
    vid_width, vid_height, _ = get_video_stream_data(probe_data.get('streams'))
    src_w, src_h = int(vid_width), int(vid_height)

    pix_fmt = _get_pix_fmt(probe_data.get('streams'))
    round_to, min_bar_px = _choose_round_and_minbar(pix_fmt)

    total_duration = _get_video_duration_seconds_from_probe(probe_data)

    MAX_SAMPLES = 7
    logger.info("[BB Detection] Sampling video file '%s' (width:%s, height:%s) to detect black bars",
                abspath, src_w, src_h)

    # Special case: very short videos (<60s) → single, capped pass (max 20s)
    if total_duration is not None and total_duration < 60:
        # Cap runtime to avoid slow software decode on whole-file scans
        t_cap = int(min(20, max(1, total_duration)))
        logger.debug("[BB Detection] Duration < 60s. Sampling capped to %ss from start (ss=0).", t_cap)
        observed_raw = _ffmpeg_sample(ss=0, t_seconds=t_cap, r_to=round_to)
        logger.debug("[BB Detection] Sample #1 @ 0s (t=%ss) → %s", t_cap, observed_raw)
        if observed_raw != "NO_CROP":
            observed = _normalise_crop_or_nocrop(
                observed_raw, src_w, src_h,
                min_sum_tb=12,
                r_to=round_to,
            )
            if observed == "NO_CROP":
                logger.debug("[BB Detection] Decision: NO_CROP (normalised from %s).", observed_raw)
                return None

            if observed != observed_raw:
                logger.debug("[BB Detection] Decision: CROP=%s (normalised from %s).", observed, observed_raw)
            else:
                logger.debug("[BB Detection] Decision: CROP=%s.", observed)
            return observed

        # observed_raw == NO_CROP
        logger.debug("[BB Detection] Decision: NO_CROP (short-video capped sample).")
        return None

    # Define sampling parameters
    if total_duration is None:
        # Unknown duration → 10s every 30s starting at 0s
        sample_len = 10
        first_start = 0
        start_step = 30  # starts at 0,30,60,...
        starts_iter = (first_start + i * start_step for i in range(MAX_SAMPLES))
        logger.debug("[BB Detection] Unknown video duration. Sampling 10s every 30s starting at 0s (max %d samples)",
                     MAX_SAMPLES)

    elif total_duration <= 5 * 60:
        # 60s .. 5min → 10s windows, small gap (~5s) between windows, start at 30s
        sample_len = 10
        small_gap = 5
        first_start = 30
        start_step = sample_len + small_gap  # 10s window + ~5s gap → next start +15s
        starts_iter = _gen_starts_known(total_duration, first_start, start_step, sample_len, MAX_SAMPLES)
        logger.debug("[BB Detection] Video duration 60s–5min. Sampling 10s windows, ~5s gap (start step=%ss) starting at 30s",
                     start_step)

    elif total_duration <= 10 * 60:
        # 5–10min → 20s windows, ~30s gap, start at 90s (hopefully skip any intros)
        sample_len = 20
        long_gap = 30
        first_start = 90
        start_step = sample_len + long_gap  # 20 + 30 = 50s between starts
        starts_iter = _gen_starts_known(total_duration, first_start, start_step, sample_len, MAX_SAMPLES)
        logger.debug("[BB Detection] Video duration 5–10min. Sampling %ss windows, ~%ss gap (start step=%ss) starting at %ss",
                     sample_len,
                     long_gap, start_step, first_start)

    else:
        # >10min → 20s windows, ~30s gap, start at 5:00 (should skip any intros)
        sample_len = 20
        long_gap = 90
        first_start = 300
        start_step = sample_len + long_gap  # 20 + 90 = 1:50s between starts
        starts_iter = _gen_starts_known(total_duration, first_start, start_step, sample_len, MAX_SAMPLES)
        logger.debug("[BB Detection] Video duration >10min. Sampling %ss windows, ~%ss gap (start step=%ss) starting at %ss",
                     sample_len,
                     long_gap, start_step, first_start)

    # -------------------------
    # Rolling quorum loop (last 3)
    # -------------------------
    last_three: List[str] = []
    third_sample_value: Optional[str] = None  # for fallback
    samples_taken = 0

    for ss in starts_iter:
        if samples_taken >= MAX_SAMPLES:
            break

        raw_observed = _ffmpeg_sample(ss=int(ss), t_seconds=sample_len, r_to=round_to)
        if raw_observed == "NO_CROP":
            observed = "NO_CROP"
            logger.debug("[BB Detection] Sample #%d @ %ss → raw=NO_CROP", samples_taken + 1, ss)
        else:
            observed = _normalise_crop_or_nocrop(
                raw_observed, src_w, src_h,
                min_sum_tb=12,
                r_to=round_to,
            )
            if observed == "NO_CROP":
                logger.debug("[BB Detection] Sample #%d @ %ss → raw=%s, normalised=NO_CROP",
                             samples_taken + 1, ss, raw_observed)
            elif observed != raw_observed:
                logger.debug("[BB Detection] Sample #%d @ %ss → raw=%s, normalised=%s",
                             samples_taken + 1, ss, raw_observed, observed)
            else:
                logger.debug("[BB Detection] Sample #%d @ %ss → %s", samples_taken + 1, ss, observed)

        samples_taken += 1
        if samples_taken == 3:
            third_sample_value = observed

        # Rolling window…
        last_three.append(observed)
        if len(last_three) > 3:
            last_three.pop(0)

        logger.debug("[BB Detection] Current sample results=%s", last_three)

        # Early stop after 2…
        if len(last_three) == 2 and last_three[0] == last_three[1]:
            if last_three[0] == "NO_CROP":
                logger.debug("[BB Detection] Decision: NO_CROP (2/2 agreement).")
                return None
            logger.debug("[BB Detection] Decision: CROP=%s (2/2 agreement).", last_three[0])
            return last_three[0]

        # 2-of-3 quorum…
        if len(last_three) == 3:
            decision = _quorum(last_three)
            if decision is not None:
                logger.debug("[BB Detection] Decision: CROP=%s (2/3 majority on %s).", decision, last_three)
                return decision
            if last_three.count("NO_CROP") >= 2:
                logger.debug("[BB Detection] Decision: NO_CROP (2/3 majority on %s).", last_three)
                return None

    # -------------------------
    # Fallbacks
    # -------------------------
    # No quorum reached within cap/available windows → use the 3rd sample's result
    if third_sample_value is not None:
        if third_sample_value == "NO_CROP":
            logger.debug("[BB Detection] No quorum after %d sample(s); fallback to 3rd sample → NO_CROP.",
                         samples_taken)
            return None
        logger.debug("[BB Detection] No quorum after %d sample(s); fallback to 3rd sample → CROP=%s.",
                     samples_taken, third_sample_value)
        return third_sample_value

    # If we never reached 3 samples, use whatever we have.
    # NOTE: this would only happen if we hit a video that was not long enough to take 3 samples
    if last_three:
        # If any non-NO_CROP present, pick the most recent one
        for v in reversed(last_three):
            if v != "NO_CROP":
                logger.debug("[BB Detection] Best-effort fallback after %d sample(s) → CROP=%s.",
                             samples_taken, v)
                return v

    logger.debug("[BB Detection] Decision: NO_CROP (no majority, no usable fallback after %d sample(s)).",
                 samples_taken)
    return None
