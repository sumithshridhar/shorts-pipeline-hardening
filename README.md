# Shorts Pipeline Hardening

Three modules from a Shorts content pipeline that runs on a scheduler with no one watching it. Each one exists because the pipeline broke in production first, in a way that looked fine in the logs.

## 1. [`pipeline/script_ids.py`](pipeline/script_ids.py) — the bug that deleted a finished video and reported success

The id allocator used to pick "the first gap in the script log." That log gets trimmed over time, so the first gap was an id the channel had *already used* — retired, not free.

Here's what that actually did: the editor renders the video under the reused id, quality-checks it, approves it — and then the uploader's own orphan-cleanup step sees that id in its used-ids record, concludes the file is a leftover from a crashed run, and **deletes it**. The uploader then finds nothing left to upload, exits 0, and the pipeline counts the run as a successful upload. A fully rendered video, destroyed, logged as a win.

The fix doesn't fill gaps at all — it allocates strictly above the highest id ever seen across every record the system keeps (the script log, the used-ids file, and the upload log), because a gap means retired, not available.

## 2. [`pipeline/safe_write.py`](pipeline/safe_write.py) — the file that couldn't afford `open(path, "w")`

Most of this pipeline's state is disposable — videos re-render, stats re-fetch, dashboards regenerate. One file isn't: the script queue is the actual written work, and it was being saved with a plain `open(path, "w")` in three separate places.

`"w"` mode truncates the file to zero bytes *before* writing the new content. A Ctrl+C, a killed process, a power cut, or the scheduled task ending mid-write in that window leaves a 0-byte file — every ready script, every held script, every "already used" marker, gone. And this particular write happens on every single pipeline round, so the window isn't rare, it's constant.

The fix: write to a sibling temp file, `fsync` it to disk, then `os.replace()` it over the target. `os.replace` is atomic on both Windows and POSIX when source and destination share a volume, which a sibling file always does — so a crash mid-write leaves either the complete old file or the complete new one, never a truncated one.

## 3. [`pipeline/niche.py`](pipeline/niche.py) — what happens when you copy a codebase without copying its assumptions

This pipeline's code was reused to spin up a second channel in a different content niche. Every hardcoded assumption from the first channel came along for the ride, and each one surfaced in production, not in testing: the generation prompt still asked for a personal secret, so the new channel auto-generated sentimental stories; the id prefix was hardcoded, so ids collided with the original channel's; tags and background music from the wrong niche shipped on real videos.

Every one of those was the same root cause — channel identity scattered across the codebase instead of declared in one place — so it's now declared in exactly one file, with a guard function that checks content two ways before it's allowed to reach the channel: it must *not* contain another niche's vocabulary, and it must *contain* this niche's. A one-directional blocklist isn't enough on its own — an early version of this guard happily accepted an off-topic script simply because it contained none of the banned words, which is why the second, positive check exists.

The file also documents a real debugging call: when this channel's view count fell, the obvious suspect (a content pivot) turned out to be a red herring — the numbers had already started dropping a week *before* the pivot happened. Correlation pointed at the wrong cause, and the file records why, so the next person (also me) doesn't re-litigate it from scratch.

## Why these three

Nothing here is a tutorial pattern — each fix exists because a specific, real failure happened first: a video silently destroyed and logged as a success, a queue file that could be zeroed out by an interrupted write, and a copy-pasted codebase that let one channel post another's content. The code and the comments documenting *why* are exactly as they run in production, apart from anything that identifies the channel or its metrics beyond what's needed to tell the story.
