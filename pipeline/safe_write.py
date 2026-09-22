"""Atomic text writes — for files that cannot be regenerated if lost.

scripts.md is the only irreplaceable file in this project. Everything else can be
rebuilt: videos re-render, stats re-fetch, dashboards regenerate. The script queue
cannot — it is the written work.

It was being rewritten with a plain open(path, "w") in three places
(editor._mark_script_used, learn.py, comment_loop.py). open("w") truncates the file
to zero bytes FIRST and writes afterwards, so a Ctrl+C, taskkill, power cut, or the
scheduled task being ended during that window leaves a 0-byte scripts.md: every
ready script, every held script and every `used` marker, gone. _mark_script_used
runs on every single round, so the window is hit constantly.

status.json, performance.json and posts.json already went through os.replace.
The one file that actually matters did not.
"""

import os


def write_text_atomic(path, text, encoding="utf-8", newline=None):
    """Write text so the destination is never observed truncated or partial.

    Writes a sibling temp file, flushes it to disk, then os.replace()s it over the
    target. os.replace is atomic on Windows and POSIX when both paths are on the
    same volume, which a sibling always is. A crash leaves either the old complete
    file or the new complete file - never an empty one.

    `newline` defaults to None, matching a plain open(path, "w") - so on Windows
    "\\n" is still translated to "\\r\\n" and scripts.md keeps its CRLF endings.
    Passing newline="" here instead silently rewrote the whole file with LF, which
    is a format change disguised as a safety fix. Pass newline="" only when the
    caller already read the file with newline="" and wants byte-exact round-trip.
    """
    directory = os.path.dirname(os.path.abspath(path)) or "."
    tmp = os.path.join(directory, f".{os.path.basename(path)}.tmp")
    with open(tmp, "w", encoding=encoding, newline=newline) as f:
        f.write(text)
        f.flush()
        os.fsync(f.fileno())
    os.replace(tmp, path)
