# Shorts Pipeline Hardening

Three small Python modules that stop an unattended YouTube Shorts pipeline from reusing ids, losing its script queue, or publishing off-topic scripts.

They are taken from a private pipeline that runs on a scheduler. This repo holds only these modules and their tests. The editor, uploader and learning loop they work with are not included.

## In 30 seconds

| Module | Problem | Fix |
|---|---|---|
| [`script_ids.py`](pipeline/script_ids.py) | The old allocator took the first gap in the script log, which can be an id that was already used. The docstring traces what follows: the uploader's cleanup deletes the finished video, and the run still counts as a success. | Hand out ids above the highest id seen in any record. Never fill gaps. |
| [`safe_write.py`](pipeline/safe_write.py) | `open(path, "w")` empties the file first. A crash mid-write leaves the script queue at 0 bytes. | Write a temp file, flush it to disk, then swap it in with `os.replace`. |
| [`niche.py`](pipeline/niche.py) | A copied codebase kept the old channel's prompt, id prefix, tags and music. | Declare the channel's identity in one file, and check every script against it before it can be published. |

## Why it matters

When a job runs with nobody watching, the worst bugs are quiet ones. The logs look fine and the data is wrong. The comments at the top of each file describe the failure it was written for (in `niche.py`, problems the author says were found in production). The fixes are small, and each one is covered by tests.

## How it fits together

```
 records the pipeline keeps                     what the modules do
 ───────────────────────────                    ───────────────────
 scripts.md            (the queue)  ──┐
 logs/used_posts.txt   (used ids)   ──┼──►  script_ids.next_free_id()  ──►  new ids, above all of these
 logs/upload_log.txt   (uploads)    ──┘

 scripts.md  ◄──  safe_write.write_text_atomic()      (temp file ► flush ► os.replace)

 generated script  ──►  niche.check_script()  ──►  None (ok)  or  a reason to reject it
```

## The three modules

### `pipeline/script_ids.py`

`next_free_id(root, count)` returns the next `count` ids, for example `["s311", "s312"]`.

It reads three records under `root`:

- `scripts.md`: lines that start with `id: s123`.
- `logs/used_posts.txt`: one entry per line. Reddit post ids are mixed in and are ignored.
- `logs/upload_log.txt`: lines containing `UPLOADED s123`.

It returns ids above the highest one found. A gap means "retired", not "free", because retired ids are still referenced by the other records. The prefix (`s`) comes from `niche.ID_PREFIX`, so a second channel gets its own id space. Without a `niche` module it falls back to `s`.

### `pipeline/safe_write.py`

```python
from safe_write import write_text_atomic
write_text_atomic("scripts.md", text)
```

It writes `.scripts.md.tmp` in the same folder, calls `fsync`, then `os.replace`s it over the target. If the process dies, the target is either the old complete file or the new complete file. On POSIX the replace is atomic. On Windows it is a single replace call, which Python does not document as atomic.

`newline=None` (the default) behaves like a plain `open(path, "w")`, so on Windows `\n` is still written as `\r\n`. Pass `newline=""` for byte-exact output.

### `pipeline/niche.py`

One file that declares the channel: name, id prefix, hashtags, tags, call-to-action lines and content rules.

`check_script(text)` returns `None` when a script fits the channel, or a reason string when it does not. It checks both ways:

- The script must not contain another niche's vocabulary (`FOREIGN_TERMS`) or a forbidden claim (`FORBIDDEN_CLAIMS`).
- The script must contain a relationship phrase such as "my mother" (`REQUIRED_TERMS`).

The second check exists because a blocklist alone accepted an off-topic script that simply used none of the banned words.

The file also holds one rule that the code cannot enforce by itself: `SOURCE_REQUIRED = True`. A first-person story may only be published if it retells a real, credited source. Nothing in this repo checks that flag.

## Run the tests

Standard library only. No install step. Written and run with Python 3.13.

```bash
python -m unittest discover -s tests -v
```

Expected result: `OK (expected failures=6)`.

The 6 expected failures are tests of the limitations listed below. They fail today on purpose. When a limitation is fixed, its test starts to pass, and `unittest` then reports it as an unexpected success so the decorator can be removed.

## Known limitations

Found while reviewing the code. None of them is fixed in this repo yet.

- **`check_script` matches substrings, not words.**
  - "skill" trips the forbidden word "kill", and "paradox" trips "dox".
  - "in my experience", "my song" and "my moment" count as relationships, because they contain "my ex", "my son" and "my mom".
  - A foreign term right after a quote or bracket (`"recipe`) is not caught, because those terms only match after a space.
- **`script_ids` ignores a record it cannot read.** A locked or unreadable `used_posts.txt` is treated as empty. The ids in it can then be handed out again, which is the bug the module exists to prevent. A missing file is fine; an unreadable one should raise.
- **Two callers can get the same ids.** `learn.py` and `comment_loop.py` both allocate ids (per the docstring), and nothing locks the allocation.
- **`safe_write` leaves its temp file behind if a write fails.** The temp name is fixed, so two writers to the same file at once can collide. On Windows, `os.replace` raises `PermissionError` if another program has the target open. There is no retry.

## About the source

- The code comments mention files that are not in this repo (`editor`, `uploader`, `learn.py`, `comment_loop.py`, `experiments.md`, `playbook.md`).
- `niche.py` includes the channel's name and some audience figures in its comments. They are the author's own notes and cannot be checked from this repo.

## Layout

```
pipeline/
  niche.py         channel identity and the check_script() guard
  safe_write.py    atomic text writes
  script_ids.py    id allocation
tests/
  _paths.py        puts pipeline/ on sys.path for the tests
  test_niche.py
  test_safe_write.py
  test_script_ids.py
```
