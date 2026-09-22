"""Script id allocation — shared by learn.py and comment_loop.py.

Both used to pick "the first gap in scripts.md", which is actively dangerous:
scripts.md gets trimmed over time (it currently starts at s021), so the first gap
is s001 — an id range the channel ALREADY USED and recorded in logs/used_posts.txt.

What happened next, if nothing had changed: the editor renders ready_queue/s010.mp4,
quality approves it into approved/s010.mp4, and then uploader.startup_orphan_cleanup()
sees s010 in used_posts.txt, concludes the file is a leftover from a crashed run, and
DELETES it. The uploader then finds approved/ empty, exits 0, and pipeline.py counts
it as an upload. A fully rendered video, destroyed silently, reported as success.

So: never reuse an id. Allocate strictly above the highest id ever seen anywhere.

THE PREFIX MUST COME FROM niche.py, NOT BE HARDCODED
----------------------------------------------------
This file used to hardcode "s". After mango changed niche to money, that meant new
money scripts were handed ids like s138 - the OLD story channel's prefix. That is not
cosmetic:

  - learn.py now decides "is this winner from my own niche?" by testing the id prefix.
    Money videos carrying an s-id look like story videos, so the channel can never
    learn from its own results and EXP-001b becomes unmeasurable.
  - the two id spaces silently merge, which is the same class of bug as reusing an id.

The prefix is declared once in niche.py and read here. Projects without a niche.py
keep the historical "s" so nothing breaks while they are migrated.
"""

import os
import re

try:
    from niche import ID_PREFIX as PREFIX
except Exception:                      # noqa: BLE001 - a project that has no niche.py yet
    PREFIX = "s"

ID_RE = re.compile(rf"{PREFIX}(\d+)")


def _ids_in_scripts_md(path):
    try:
        with open(path, encoding="utf-8", errors="replace") as f:
            text = f.read()
    except OSError:
        return set()
    return {int(n) for n in re.findall(rf"^id:\s*{PREFIX}(\d+)", text, flags=re.M)}


def _ids_in_used_posts(path):
    """used_posts.txt mixes Reddit post ids with script ids; take only PREFIX+NNN."""
    out = set()
    try:
        with open(path, encoding="utf-8", errors="replace") as f:
            for line in f:
                m = re.fullmatch(rf"{PREFIX}(\d+)", line.strip())
                if m:
                    out.add(int(m.group(1)))
    except OSError:
        pass
    return out


def _ids_in_upload_log(path):
    """Anything ever uploaded, even if its block has since left scripts.md."""
    out = set()
    try:
        with open(path, encoding="utf-8", errors="replace") as f:
            for line in f:
                m = re.search(rf"UPLOADED\s+{PREFIX}(\d+)", line)
                if m:
                    out.add(int(m.group(1)))
    except OSError:
        pass
    return out


def all_known_ids(root="."):
    """Every script id this project has ever used, from every record we keep."""
    return (
        _ids_in_scripts_md(os.path.join(root, "scripts.md"))
        | _ids_in_used_posts(os.path.join(root, "logs", "used_posts.txt"))
        | _ids_in_upload_log(os.path.join(root, "logs", "upload_log.txt"))
    )


def next_free_id(root=".", count=1):
    """Return `count` fresh ids as 'PREFIX+NNN' strings, above every known id.

    Deliberately does NOT fill gaps. A gap means an id was retired, and retired
    ids are still referenced by used_posts.txt, upload_log.txt and performance.json.

    Only ids sharing this niche's prefix are considered, so a channel that changed
    niche starts its new prefix at 001 instead of inheriting the old channel's count.
    """
    known = all_known_ids(root)
    start = (max(known) + 1) if known else 1
    return [f"{PREFIX}{n:03d}" for n in range(start, start + count)]
