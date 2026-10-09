"""Tests for pipeline/safe_write.py: the target file is never left empty or half-written."""

import os
import pathlib
import tempfile
import unittest
from unittest import mock

import _paths  # noqa: F401  (puts ../pipeline on sys.path)
from safe_write import write_text_atomic


def temp_files(directory):
    return sorted(name for name in os.listdir(directory) if name.endswith(".tmp"))


class WriteTextAtomicTests(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.dir = self._tmp.name
        self.path = os.path.join(self.dir, "scripts.md")
        self.addCleanup(self._tmp.cleanup)

    def read_bytes(self):
        with open(self.path, "rb") as f:
            return f.read()

    def test_creates_a_new_file(self):
        write_text_atomic(self.path, "hello", newline="")
        self.assertEqual(self.read_bytes(), b"hello")

    def test_replaces_the_whole_old_content(self):
        write_text_atomic(self.path, "a much longer first version\n" * 10, newline="")
        write_text_atomic(self.path, "short", newline="")
        self.assertEqual(self.read_bytes(), b"short")

    def test_leaves_no_temp_file_after_success(self):
        write_text_atomic(self.path, "x")
        self.assertEqual(temp_files(self.dir), [])

    def test_a_failed_flush_to_disk_keeps_the_old_file_intact(self):
        write_text_atomic(self.path, "OLD", newline="")
        with mock.patch("os.fsync", side_effect=OSError("disk full")):
            with self.assertRaises(OSError):
                write_text_atomic(self.path, "NEW", newline="")
        self.assertEqual(self.read_bytes(), b"OLD")

    def test_a_failed_replace_keeps_the_old_file_intact(self):
        write_text_atomic(self.path, "OLD", newline="")
        with mock.patch("os.replace", side_effect=PermissionError("locked")):
            with self.assertRaises(PermissionError):
                write_text_atomic(self.path, "NEW", newline="")
        self.assertEqual(self.read_bytes(), b"OLD")

    def test_the_file_is_never_empty_while_it_is_being_replaced(self):
        # open(path, "w") truncates first. Here the target must still hold the full old
        # content at the moment the new content is being written to the temp file.
        write_text_atomic(self.path, "OLD CONTENT", newline="")
        seen_during_write = []
        real_fsync = os.fsync

        def spy(fd):
            with open(self.path, "rb") as f:
                seen_during_write.append(f.read())
            return real_fsync(fd)

        with mock.patch("os.fsync", side_effect=spy):
            write_text_atomic(self.path, "NEW CONTENT", newline="")
        self.assertEqual(seen_during_write, [b"OLD CONTENT"])
        self.assertEqual(self.read_bytes(), b"NEW CONTENT")

    def test_default_newline_handling_matches_a_plain_open_w(self):
        reference = os.path.join(self.dir, "reference.txt")
        with open(reference, "w", encoding="utf-8") as f:
            f.write("a\nb\n")
        write_text_atomic(self.path, "a\nb\n")
        with open(reference, "rb") as f:
            self.assertEqual(self.read_bytes(), f.read())

    def test_newline_empty_string_writes_the_text_byte_for_byte(self):
        write_text_atomic(self.path, "a\nb\r\nc\n", newline="")
        self.assertEqual(self.read_bytes(), b"a\nb\r\nc\n")

    def test_explicit_crlf(self):
        write_text_atomic(self.path, "a\nb\n", newline="\r\n")
        self.assertEqual(self.read_bytes(), b"a\r\nb\r\n")

    def test_utf8_round_trip(self):
        text = "café — ₹5,00,000 \U0001F514"
        write_text_atomic(self.path, text, newline="")
        self.assertEqual(self.read_bytes().decode("utf-8"), text)

    def test_accepts_pathlib_paths(self):
        write_text_atomic(pathlib.Path(self.path), "ok", newline="")
        self.assertEqual(self.read_bytes(), b"ok")

    def test_relative_path_in_the_current_folder(self):
        previous = os.getcwd()
        os.chdir(self.dir)
        try:
            write_text_atomic("relative.txt", "ok", newline="")
        finally:
            os.chdir(previous)
        with open(os.path.join(self.dir, "relative.txt"), "rb") as f:
            self.assertEqual(f.read(), b"ok")


class KnownLimitations(unittest.TestCase):
    """Things the review found. They fail today; remove the decorator once fixed."""

    @unittest.expectedFailure
    def test_a_failed_write_should_clean_up_its_temp_file(self):
        with tempfile.TemporaryDirectory() as directory:
            path = os.path.join(directory, "scripts.md")
            with mock.patch("os.fsync", side_effect=OSError("disk full")):
                with self.assertRaises(OSError):
                    write_text_atomic(path, "NEW")
            self.assertEqual(temp_files(directory), [])


if __name__ == "__main__":
    unittest.main()
