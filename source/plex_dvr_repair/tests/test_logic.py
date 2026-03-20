"""
plugins.plex_dvr_repair.tests.test_logic.py

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

import tempfile
import time
import unittest
from pathlib import Path
from unittest import mock

from plex_dvr_repair.lib.logic import (
    REPAIRED_FILE_MARKER,
    Fragment,
    build_ffmpeg_command,
    choose_groups_to_keep,
    detect_hardware_acceleration_methods,
    discover_candidate_fragments,
    find_active_sidecars,
    group_fragments_by_recording_window,
    guess_output_paths,
    is_copy_fragment_name,
    parse_fragment_path,
    select_dominant_profile,
)


class PlexDvrRepairLogicTests(unittest.TestCase):
    def test_detects_copy_name(self):
        self.assertTrue(is_copy_fragment_name("Episode (copy 1).ts"))
        self.assertTrue(is_copy_fragment_name("Episode (Copy 12).ts"))
        self.assertFalse(is_copy_fragment_name("Episode.ts"))

    def test_parse_fragment(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "Episode (copy 3).ts"
            path.write_bytes(b"abc")
            fragment = parse_fragment_path(path)
            self.assertEqual(fragment.base_stem, "Episode")
            self.assertTrue(fragment.is_copy)
            self.assertEqual(fragment.copy_number, 3)

    def test_discovers_matching_fragments(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            base = Path(temp_dir) / "Episode.ts"
            copy1 = Path(temp_dir) / "Episode (copy 1).ts"
            other = Path(temp_dir) / "Episode (copy 1).mkv"
            for path in [base, copy1, other]:
                path.write_bytes(b"abc")
            fragments = discover_candidate_fragments(base)
            self.assertEqual(
                [fragment.path.name for fragment in fragments],
                ["Episode.ts", "Episode (copy 1).ts"],
            )

    def test_groups_by_recording_window(self):
        now = time.time()
        fragments = [
            Fragment(Path("/tmp/a.ts"), "Episode", ".ts", False, 0, 100, now, 1200.0),
            Fragment(
                Path("/tmp/b.ts"), "Episode", ".ts", True, 1, 100, now + 1800, 1800.0
            ),
            Fragment(
                Path("/tmp/c.ts"),
                "Episode",
                ".ts",
                True,
                2,
                100,
                now + (60 * 60 * 5),
                1800.0,
            ),
        ]
        groups = group_fragments_by_recording_window(fragments)
        self.assertEqual(len(groups), 2)
        self.assertEqual(len(groups[0]), 2)
        self.assertEqual(len(groups[1]), 1)

    def test_groups_when_later_fragment_start_overlaps_prior_fragment_end(self):
        copy4_end = 1_700_000_000.0
        copy5_end = copy4_end + (51 * 60)
        fragments = [
            Fragment(
                Path("/tmp/copy4.ts"),
                "Episode",
                ".ts",
                True,
                4,
                100,
                copy4_end,
                513.2,
            ),
            Fragment(
                Path("/tmp/copy5.ts"),
                "Episode",
                ".ts",
                True,
                5,
                100,
                copy5_end,
                3075.2,
            ),
        ]
        groups = group_fragments_by_recording_window(fragments)
        self.assertEqual(len(groups), 1)
        self.assertEqual(
            [fragment.path.name for fragment in groups[0]],
            ["copy4.ts", "copy5.ts"],
        )

    def test_detects_recent_sidecars(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            base = Path(temp_dir) / "Episode.ts"
            sidecar = Path(temp_dir) / "Episode.txt"
            base.write_bytes(b"abc")
            sidecar.write_text("sidecar", encoding="utf-8")
            active = find_active_sidecars(
                base, grace_minutes=120, ignore_when_sidecars_exist=True
            )
            self.assertEqual([path.name for path in active], ["Episode.txt"])

    def test_output_name_for_single_canonical_result(self):
        base = Path("/library/Episode.ts")
        outputs = guess_output_paths(
            base,
            groups=[[1], [2]],
            keep_multiple=False,
            replace_original_base_file=True,
            output_suffix_template="stitched {index}",
        )
        self.assertEqual(len(outputs), 1)
        self.assertEqual(
            str(outputs[0]), f"/library/Episode - {REPAIRED_FILE_MARKER}.ts"
        )

    def test_output_name_for_h264_mkv_profile(self):
        base = Path("/library/Episode.ts")
        outputs = guess_output_paths(
            base,
            groups=[[1]],
            keep_multiple=False,
            replace_original_base_file=True,
            output_suffix_template="stitched {index}",
            output_profile="h264_mkv",
            source_video_codec="h264",
        )
        self.assertEqual(
            str(outputs[0]), f"/library/Episode - {REPAIRED_FILE_MARKER}.mkv"
        )

    def test_latest_group_selection_wins(self):
        now = time.time()
        group1 = [Fragment(Path("/tmp/a.ts"), "Episode", ".ts", False, 0, 100, now)]
        group2 = [
            Fragment(Path("/tmp/b.ts"), "Episode", ".ts", False, 0, 200, now - 10)
        ]
        selected = choose_groups_to_keep([group1, group2], keep_multiple=False)
        self.assertEqual(selected, [group1])

    def test_hardware_detection_falls_back_to_software(self):
        with mock.patch(
            "plex_dvr_repair.lib.logic._list_ffmpeg_encoders", return_value=""
        ), mock.patch("plex_dvr_repair.lib.logic.Path.exists", return_value=False):
            methods = detect_hardware_acceleration_methods("hevc")
        self.assertEqual(methods, ["software"])

    def test_build_ffmpeg_command_adds_repair_flags(self):
        fragment = Fragment(
            Path("/tmp/a.ts"), "Episode", ".ts", False, 0, 100, time.time(), 60.0
        )
        probe = {
            "streams": [
                {"codec_type": "video", "codec_name": "h264", "avg_frame_rate": "25/1"},
                {
                    "codec_type": "audio",
                    "codec_name": "aac",
                    "sample_rate": "48000",
                    "channels": 2,
                },
            ]
        }
        command = build_ffmpeg_command(
            concat_file=Path("/tmp/list.txt"),
            output_file=Path("/tmp/out.ts"),
            fragment_probes=[(fragment, probe)],
            metadata_file=None,
            encoder_mode="software",
        )
        self.assertIn("-fflags", command)
        self.assertIn("+discardcorrupt+genpts", command)
        self.assertIn("-probesize", command)
        self.assertIn("-analyzeduration", command)
        self.assertIn("-fpsprobesize", command)
        self.assertIn("-mpegts_flags", command)
        self.assertIn("+resend_headers", command)

    def test_build_ffmpeg_command_for_h265_mkv_profile(self):
        fragment = Fragment(
            Path("/tmp/a.ts"), "Episode", ".ts", False, 0, 100, time.time(), 60.0
        )
        probe = {
            "streams": [
                {
                    "index": 0,
                    "codec_type": "video",
                    "codec_name": "h264",
                    "avg_frame_rate": "25/1",
                    "height": 1080,
                },
                {
                    "index": 1,
                    "codec_type": "audio",
                    "codec_name": "aac",
                    "sample_rate": "48000",
                    "channels": 2,
                },
                {"index": 2, "codec_type": "subtitle", "codec_name": "subrip"},
            ],
            "format": {"bit_rate": "8000000", "duration": "60"},
        }
        command = build_ffmpeg_command(
            concat_file=Path("/tmp/list.txt"),
            output_file=Path("/tmp/out.mkv"),
            fragment_probes=[(fragment, probe)],
            metadata_file=None,
            encoder_mode="software",
            output_profile="h265_mkv",
        )
        self.assertIn("libx265", command)
        self.assertIn("matroska", command)
        self.assertIn("-map", command)
        self.assertIn("0:2?", command)
        self.assertIn("-c:s", command)
        self.assertIn("copy", command)
        self.assertIn("-avoid_negative_ts", command)
        self.assertIn("make_zero", command)

    def test_select_dominant_profile_prefers_longest_video_fragment(self):
        short_fragment = Fragment(
            Path("/tmp/short.ts"), "Episode", ".ts", True, 6, 100, time.time(), 5.12
        )
        long_fragment = Fragment(
            Path("/tmp/long.ts"), "Episode", ".ts", True, 5, 100, time.time(), 3075.2
        )
        short_probe = {
            "streams": [
                {
                    "index": 0,
                    "codec_type": "video",
                    "codec_name": "h264",
                    "duration": "5.120000",
                    "width": 1920,
                    "height": 1080,
                },
                {
                    "index": 1,
                    "codec_type": "audio",
                    "codec_name": "aac",
                    "duration": "4.928000",
                },
            ]
        }
        long_probe = {
            "streams": [
                {
                    "index": 0,
                    "codec_type": "video",
                    "codec_name": "h264",
                    "duration": "3075.200000",
                    "width": 1920,
                    "height": 1080,
                },
                {
                    "index": 1,
                    "codec_type": "audio",
                    "codec_name": "aac",
                    "duration": "3075.093333",
                },
            ]
        }
        dominant_video, dominant_audio, all_equal = select_dominant_profile(
            [(short_fragment, short_probe), (long_fragment, long_probe)]
        )
        self.assertEqual(dominant_video.get("duration"), "3075.200000")
        self.assertEqual(dominant_audio.get("duration"), "3075.093333")
        self.assertTrue(all_equal)


if __name__ == "__main__":
    unittest.main()
