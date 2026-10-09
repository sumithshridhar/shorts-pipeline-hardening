"""Tests for pipeline/script_ids.py: ids are never reused and never fill gaps."""

import os
import tempfile
import types
import unittest

import _paths
import script_ids


def write(root, relative, text):
    path = os.path.join(root, relative)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write(text)


class NextFreeIdTests(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.root = self._tmp.name
        self.addCleanup(self._tmp.cleanup)

    def test_fresh_project_starts_at_001(self):
        self.assertEqual(script_ids.next_free_id(self.root), ["s001"])

    def test_count_returns_consecutive_ids(self):
        write(self.root, "scripts.md", "id: s010\n")
        self.assertEqual(script_ids.next_free_id(self.root, 3), ["s011", "s012", "s013"])

    def test_allocates_above_the_highest_id_in_any_record(self):
        write(self.root, "scripts.md", "id: s021\n\nid: s022\n\nid: s140\n")
        write(self.root, "logs/used_posts.txt", "s005\ns200\n")
        write(self.root, "logs/upload_log.txt", "2026-01-01 UPLOADED s150 ok\nUPLOADED s310\n")
        self.assertEqual(script_ids.all_known_ids(self.root), {5, 21, 22, 140, 150, 200, 310})
        self.assertEqual(script_ids.next_free_id(self.root), ["s311"])

    def test_does_not_fill_gaps(self):
        write(self.root, "scripts.md", "id: s001\n\nid: s002\n\nid: s010\n")
        self.assertEqual(script_ids.next_free_id(self.root), ["s011"])

    def test_id_retired_from_scripts_md_is_not_handed_out_again(self):
        # The original bug: scripts.md had been trimmed to start at s021, so "the first
        # gap" was s001..s020, ids the channel had already used and recorded elsewhere.
        write(self.root, "scripts.md", "id: s021\n\nid: s022\n")
        write(self.root, "logs/used_posts.txt", "".join(f"s{n:03d}\n" for n in range(1, 21)))
        (new_id,) = script_ids.next_free_id(self.root)
        self.assertEqual(new_id, "s023")
        self.assertNotIn(int(new_id[1:]), range(1, 21))

    def test_ignores_reddit_post_ids_in_used_posts(self):
        write(self.root, "logs/used_posts.txt", "1abc2de\nt9999\nxyz\ns007\n")
        self.assertEqual(script_ids.all_known_ids(self.root), {7})

    def test_tolerates_whitespace_around_ids_in_used_posts(self):
        write(self.root, "logs/used_posts.txt", "  s042  \r\n")
        self.assertEqual(script_ids.all_known_ids(self.root), {42})

    def test_upload_log_only_counts_UPLOADED_lines(self):
        write(self.root, "logs/upload_log.txt", "FAILED s999\nUPLOADED    s050\nnote s777\n")
        self.assertEqual(script_ids.all_known_ids(self.root), {50})

    def test_scripts_md_id_must_start_the_line(self):
        write(self.root, "scripts.md", "note: see id: s900 above\nid:s012\n")
        self.assertEqual(script_ids.all_known_ids(self.root), {12})

    def test_ids_grow_past_three_digits(self):
        write(self.root, "scripts.md", "id: s999\n")
        self.assertEqual(script_ids.next_free_id(self.root, 2), ["s1000", "s1001"])

    def test_missing_files_and_folders_are_tolerated(self):
        write(self.root, "scripts.md", "id: s003\n")  # no logs/ folder at all
        self.assertEqual(script_ids.next_free_id(self.root), ["s004"])

    def test_bytes_that_are_not_utf8_do_not_crash(self):
        path = os.path.join(self.root, "scripts.md")
        with open(path, "wb") as f:
            f.write(b"id: s008\n\xff\xfe\n")
        self.assertEqual(script_ids.all_known_ids(self.root), {8})


class PrefixTests(unittest.TestCase):
    def test_prefix_is_read_from_niche_not_hardcoded(self):
        fake = types.ModuleType("niche")
        fake.ID_PREFIX = "f"
        with _paths.fake_niche_module(fake):
            module = _paths.load_fresh_script_ids()
        with tempfile.TemporaryDirectory() as root:
            write(root, "scripts.md", "id: s500\n\nid: f012\n")  # the other niche's ids
            write(root, "logs/used_posts.txt", "s600\nf013\n")
            self.assertEqual(module.all_known_ids(root), {12, 13})
            self.assertEqual(module.next_free_id(root), ["f014"])

    def test_a_new_niche_starts_its_own_count_at_001(self):
        fake = types.ModuleType("niche")
        fake.ID_PREFIX = "m"
        with _paths.fake_niche_module(fake):
            module = _paths.load_fresh_script_ids()
        with tempfile.TemporaryDirectory() as root:
            write(root, "scripts.md", "id: s138\n")
            self.assertEqual(module.next_free_id(root), ["m001"])

    def test_without_a_niche_module_the_historical_s_prefix_is_used(self):
        with _paths.fake_niche_module(None):
            module = _paths.load_fresh_script_ids()
        self.assertEqual(module.PREFIX, "s")


class KnownLimitations(unittest.TestCase):
    """Things the review found. They fail today; remove the decorator once fixed."""

    @unittest.expectedFailure
    def test_an_unreadable_record_should_not_be_silently_ignored(self):
        # A record that exists but cannot be read (permissions, a file lock, a folder in
        # its place) is treated as empty. The ids in it are then free to be reused,
        # which is the exact bug this module exists to prevent.
        with tempfile.TemporaryDirectory() as root:
            write(root, "scripts.md", "id: s001\n")
            os.makedirs(os.path.join(root, "logs", "used_posts.txt"))  # a folder, not a file
            with self.assertRaises(OSError):
                script_ids.all_known_ids(root)


if __name__ == "__main__":
    unittest.main()
