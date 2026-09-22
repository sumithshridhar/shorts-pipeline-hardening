"""The channel's identity. ONE place, read by everything.

WHY THIS FILE EXISTS
--------------------
The food project was created by copying this codebase. Copying carried across every
hardcoded channel assumption, and each one had to be found the hard way, in production:

  - the generation prompt still asked for "a family/relationship secret", so a
    COOKING channel auto-generated sentimental stories and queued three to publish
  - the id prefix was hardcoded, so a food queue filled with s022/s023/s024
  - YouTube tags read "reddit, reddit stories, storytime" on a burger video
  - the music library was all horror and epic-trailer cues, so a thriller track
    played under scrambled eggs
  - a fake Reddit post card was drawn over the opening of every food video

Every one of those was the same bug: channel identity scattered through the code
instead of declared once. So it is declared here, and the guard below refuses to let
content from the wrong niche reach the channel.

WHEN STARTING A NEW CHANNEL: copy the project, then edit THIS FILE FIRST.

-------------------------------------------------------------------------------
REVERTED TO THE STORY NICHE ON 11 AUG 2026. Read this before changing it back.

Mango ran story content until 7 Aug, pivoted to money mechanics, and money never
worked: six money videos, best 249 views, worst 1. But the money pivot was not the
cause of the decline - see experiments.md FINDING-002. Mango fell from a ~1,100
median to 249 on 31 JULY, a week BEFORE the pivot, and it fell on its own native
story format.

So reverting the niche fixes the second problem, not the first. Two things are
believed to have caused the 1,100 -> 249 slide, and reverting alone addresses
neither:

  1. A month of dormancy (26 Jun - 30 Jul) with nothing published.
  2. The switch from hand-curated REAL Reddit posts to auto-generated imitations
     of them. Food shows automation is fine for explainer content (956 median,
     still steady); it appears not to survive emotional storytelling, which needs
     an authentic source to be worth watching.

Point 2 is the one that matters here, and it is also an honesty requirement, not
only a quality one. See SOURCE_REQUIRED below.
-------------------------------------------------------------------------------
"""

# ── Identity ─────────────────────────────────────────────────────────────────
NICHE = "story"
CHANNEL_NAME = "Mango Shorts"
ID_PREFIX = "s"          # script ids look like s138. Never reuse another niche's.

PREMISE = (
    "Short retellings of real posted stories - someone discovers a family or "
    "relationship secret through an ordinary object, and the discovery unravels "
    "something they thought they knew."
)

# ── The honesty rule this channel lives or dies by ───────────────────────────
# These videos are first person: "My mother just called me from the hospital...",
# and the CTA asks viewers to vote on what the narrator should DO. That framing
# tells the viewer this is a real person's real situation.
#
# That is TRUE and fine when the script retells a real posted story and the
# description credits it. It is a lie when a language model invents the story and
# it goes out with the same first-person framing.
#
# So: a script may only be published on this channel if it came from a real source
# that is credited in the description, OR it is explicitly framed as fiction.
# Never auto-generate first-person testimony and publish it as though it happened.
#
# This is also what the numbers say: the credited-Reddit era ran ~1,100 views; the
# auto-generated-imitation era ran 249.
SOURCE_REQUIRED = True
SOURCE_CREDIT = "Story shared publicly on Reddit. Retold and read aloud."

# ── Hard content rules ───────────────────────────────────────────────────────
# The story format is emotionally charged by design, which is exactly why it needs
# limits. These stories involve real people who posted them; the retelling must not
# add cruelty, name anyone, or turn a private situation into a target.
FORBIDDEN_CLAIMS = [
    "kill", "suicide", "kys", "she deserved it", "he deserved it",
    "dox", "her address is", "his address is", "full name is",
]

# Words that mean a script belongs to a DIFFERENT channel. Used by the guard.
FOREIGN_TERMS = [
    # food channel
    "recipe", "cooking", "preheat", "saucepan", "frying pan", "the oven",
    "marinade", "simmer", "sear the", "caramelise", "caramelize",
    # money channel - these are the money-mechanics explainer's vocabulary, and a
    # script built on them is an explainer, not a story
    "compound interest", "credit score", "interest rate", "the spread",
    "no cost emi", "minimum due", "cashback", "merchant fee", "fixed deposit",
]

HASHTAGS = ["#shorts", "#story", "#storytime"]
MOOD_HASHTAGS = {
    "shocking":      ["#storytime", "#familysecrets", "#plottwist", "#truestory"],
    "controversial": ["#aita", "#amitheasshole", "#hottake", "#storytime"],
    "relatable":     ["#storytime", "#relatable", "#family", "#truestory"],
    "funny":         ["#storytime", "#relatable", "#funny", "#family"],
    "emotional":     ["#storytime", "#familysecrets", "#emotional", "#truestory"],
}

YOUTUBE_TAGS = [
    "story", "storytime", "reddit stories", "family secrets", "true story",
    "reddit", "story time", "plot twist", "family drama", "confession",
    "reddit readings", "shocking stories", "real stories",
]
MOOD_TAGS = {
    "shocking":      ["plot twist", "shocking story", "family secret", "did not see it coming"],
    "controversial": ["aita", "am i the asshole", "unpopular opinion", "you decide"],
    "relatable":     ["relatable", "family", "storytime", "true story"],
    "funny":         ["funny story", "relatable", "storytime"],
    "emotional":     ["emotional story", "family secrets", "true story"],
}

# TWO-PARTER CTAs: never name a clock time or a weekday.
#
# The first pair (s142/s143, 17 Aug) shipped with "Part 2 tomorrow, 9PM" spoken in
# the video. The uploader spaces publishes 8 hours apart from whenever the run
# happened and has no idea what the script promised, so Part 2 actually landed at
# 2:30 AM IST - and for the 28.5% of this audience in the US, that was 5PM the SAME
# day. Wrong hour, wrong day, unfixable once it is in the audio.
#
# Use: "Part 2 is next - follow so you don't miss it."
PART_ONE_CTA = "Part 2 is next — follow so you don't miss it."

CTA_LINES = {
    "shocking":      "Did you see that coming? 🔔 Follow for more stories like this.",
    "controversial": "Whose side are you on? Settle it in the comments. 🔔 Follow for more.",
    "relatable":     "Has this happened to you? 🔔 Follow for more stories.",
    "funny":         "Tag someone who needs to hear this. 🔔 Follow for more.",
    "emotional":     "What would you have done? 🔔 Follow for more stories.",
}
DEFAULT_CTA = "Follow for more stories like this."

# Credit belongs in the description, on every video. It is what makes the
# first-person framing honest rather than a fabricated personal claim.
DISCLAIMER = (
    "Story shared publicly on Reddit, retold here and read aloud. Names and "
    "identifying details are removed. Shared for discussion, not judgement."
)

BGM_DIR = "bgm"           # 21 story tracks; bgm_money belongs to the money channel
REDDIT_CARD = True        # the post-card opener belongs to this channel


# A script must actually be a STORY. A blocklist alone is not enough: the first
# version of this guard happily accepted "Your rice is gummy because you skipped
# thirty seconds at the sink" simply because it contained none of the banned words.
# Blocklists always have holes; requiring the subject to be present does not.
# Both spellings of everything. A perfectly good retelling was rejected as
# "names no relationship at all" purely because it said "my mum" and this list
# only had "my mom" - the guard was right to be strict and wrong about the
# vocabulary. Any relationship word that has a British and an American form needs
# both, or the guard rejects real work at random.
REQUIRED_TERMS = [
    "my mother", "my father", "my mom", "my mum", "my dad", "my daddy",
    "my husband", "my wife", "my sister", "my brother", "my son",
    "my daughter", "my grandmother", "my grandma", "my granny", "my nan",
    "my grandfather", "my grandad", "my granddad", "my grandpa",
    "my aunt", "my auntie", "my uncle", "my cousin", "my nephew", "my niece",
    "my fiance", "my fiancé", "my fiancée", "my girlfriend", "my boyfriend",
    "my partner", "my ex", "my parents", "my family", "my in-laws",
    "my mother-in-law", "my father-in-law", "my stepmother", "my stepfather",
    "my stepmom", "my stepdad", "my neighbour", "my neighbor",
    "my best friend", "my childhood friend", "my landlord",
]


def check_script(text):
    """Return a reason string if this script does not belong on this channel.

    Two-sided check, because either side alone leaks:
      - must NOT contain another niche's vocabulary or a forbidden claim
      - must CONTAIN this niche's vocabulary

    This is the guard that did not exist when the food channel auto-generated three
    Reddit-style family stories and queued them to publish.
    """
    low = " " + " ".join(text.lower().split()) + " "

    for term in FOREIGN_TERMS:
        if f" {term}" in low:
            return f"contains '{term}' - that belongs to another channel's niche"

    for claim in FORBIDDEN_CLAIMS:
        if claim in low:
            return (f"contains '{claim}' - this channel retells other people's "
                    "stories and must never add cruelty or identify anyone")

    if not any(term in low for term in REQUIRED_TERMS):
        return ("names no relationship at all - this channel is family and "
                "relationship stories, so a script with no person in it is off-niche")

    return None

# ── Who writes the scripts ───────────────────────────────────────────────────
# False = the local model is NOT allowed to write scripts for this channel.
#
# Turned off 12 Aug on the user's instruction, and the numbers back it: mango's
# auto-generated era ran a 249 median against ~1,100 for hand-curated, and in
# testing llama3.1:8b undershot every word target (asked for 95-118 it wrote
# 52-89, and still only reached 66-86 after being told it was short) while
# inventing a different output format on almost every call.
#
# Scripts now come from Claude, written against playbook.md - which is generated
# from this channel's own view and retention data by build_playbook.py. Refill
# with: python build_playbook.py --retention   then ask Claude for a batch.
AUTOGEN_ENABLED = False
