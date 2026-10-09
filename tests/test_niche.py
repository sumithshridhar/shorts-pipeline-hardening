"""Tests for pipeline/niche.py: the channel config and the check_script() guard."""

import re
import unittest

import _paths  # noqa: F401  (puts ../pipeline on sys.path)
import niche


class ChannelConfigTests(unittest.TestCase):
    def test_id_prefix_is_a_single_lowercase_letter(self):
        self.assertRegex(niche.ID_PREFIX, r"^[a-z]$")

    def test_match_lists_are_lowercase(self):
        # check_script() lowercases the script and then tests `term in text`, so a term
        # with a capital letter could never match.
        for name in ("FOREIGN_TERMS", "FORBIDDEN_CLAIMS", "REQUIRED_TERMS"):
            for term in getattr(niche, name):
                self.assertEqual(term, term.lower(), f"{name}: {term!r} is not lowercase")

    def test_every_mood_has_hashtags_tags_and_a_cta(self):
        self.assertEqual(set(niche.MOOD_HASHTAGS), set(niche.MOOD_TAGS))
        self.assertEqual(set(niche.MOOD_HASHTAGS), set(niche.CTA_LINES))

    def test_hashtags_start_with_a_hash(self):
        for tag in niche.HASHTAGS + [t for tags in niche.MOOD_HASHTAGS.values() for t in tags]:
            self.assertTrue(tag.startswith("#"), tag)

    def test_part_one_cta_names_no_clock_time_or_weekday(self):
        # The comment in niche.py explains why: the uploader spaces posts by hours, so a
        # promised "tomorrow 9PM" was wrong the moment it was spoken.
        pattern = re.compile(
            r"(?i)\b(monday|tuesday|wednesday|thursday|friday|saturday|sunday)\b"
            r"|\b(today|tonight|tomorrow)\b|\b\d{1,2}(:\d{2})?\s?(am|pm)\b"
        )
        lines = [niche.PART_ONE_CTA, niche.DEFAULT_CTA, *niche.CTA_LINES.values()]
        for line in lines:
            self.assertIsNone(pattern.search(line), line)

    def test_publishing_requires_a_credited_source(self):
        self.assertTrue(niche.SOURCE_REQUIRED)
        self.assertTrue(niche.SOURCE_CREDIT.strip())
        self.assertIn("Reddit", niche.DISCLAIMER)


class CheckScriptTests(unittest.TestCase):
    GOOD = "My mother called me from the hospital last night. She said the box in the attic was never hers."

    def test_a_real_looking_story_passes(self):
        self.assertIsNone(niche.check_script(self.GOOD))

    def test_matching_ignores_case_and_extra_whitespace(self):
        self.assertIsNone(niche.check_script("MY   MOTHER\n\nfound   the box."))

    def test_british_and_american_spellings_both_count_as_a_relationship(self):
        self.assertIsNone(niche.check_script("My mum found a letter behind the clock."))
        self.assertIsNone(niche.check_script("My mom found a letter behind the clock."))
        self.assertIsNone(niche.check_script("My fiancé found a letter behind the clock."))

    def test_every_required_term_is_accepted_on_its_own(self):
        for term in niche.REQUIRED_TERMS:
            with self.subTest(term=term):
                self.assertIsNone(niche.check_script(f"{term} told me something I never forgot."))

    def test_a_script_with_no_person_in_it_is_rejected(self):
        reason = niche.check_script("Your rice is gummy because you skipped thirty seconds at the sink.")
        self.assertIn("names no relationship", reason)

    def test_every_foreign_term_is_rejected_and_named_in_the_reason(self):
        for term in niche.FOREIGN_TERMS:
            with self.subTest(term=term):
                reason = niche.check_script(f"My mother always said {term} was the secret.")
                self.assertIsNotNone(reason)
                self.assertIn(term, reason)
                self.assertIn("another channel", reason)

    def test_every_forbidden_claim_is_rejected_and_named_in_the_reason(self):
        for claim in niche.FORBIDDEN_CLAIMS:
            with self.subTest(claim=claim):
                reason = niche.check_script(f"My brother said that {claim} was the only answer.")
                self.assertIsNotNone(reason)
                self.assertIn(claim, reason)

    def test_the_blocklist_is_checked_even_when_a_relationship_is_present(self):
        self.assertIsNotNone(niche.check_script("My mother kept her recipe in a drawer."))

    def test_returns_none_not_an_empty_string_when_the_script_is_fine(self):
        self.assertIs(niche.check_script(self.GOOD), None)


class KnownLimitations(unittest.TestCase):
    """Things the review found. They fail today; remove the decorator once fixed.

    The guard uses plain substring matching, so it is sloppy at word edges.
    """

    @unittest.expectedFailure
    def test_skill_should_not_trigger_the_forbidden_word_kill(self):
        self.assertIsNone(niche.check_script("My mother taught me one skill that saved the family."))

    @unittest.expectedFailure
    def test_paradox_should_not_trigger_the_forbidden_word_dox(self):
        self.assertIsNone(niche.check_script("My brother loves a good paradox."))

    @unittest.expectedFailure
    def test_in_my_experience_is_not_a_relationship(self):
        # "my ex" is in REQUIRED_TERMS and is found inside "my experience". "my son" is
        # found inside "my song", and "my mom" inside "my moment", the same way.
        reason = niche.check_script("In my experience, rice is gummy because you skipped rinsing it.")
        self.assertIsNotNone(reason)

    @unittest.expectedFailure
    def test_a_foreign_term_in_quotes_should_still_be_caught(self):
        # FOREIGN_TERMS only match after a space, so "recipe" right after a quote
        # (or a bracket) slips through.
        reason = niche.check_script('My mother said "recipe cards" were all she had left.')
        self.assertIsNotNone(reason)


if __name__ == "__main__":
    unittest.main()
