import unittest

from caption_segments import build_caption_segments, build_caption_segments_from_words


class CaptionSegmentTests(unittest.TestCase):
    def test_word_timed_segments_are_clip_relative(self):
        words = [
            {"text": "This", "start_seconds": 10.0, "end_seconds": 10.2},
            {"text": "is", "start_seconds": 10.2, "end_seconds": 10.35},
            {"text": "a", "start_seconds": 10.35, "end_seconds": 10.45},
            {"text": "real", "start_seconds": 10.45, "end_seconds": 10.7},
            {"text": "caption", "start_seconds": 10.7, "end_seconds": 11.0},
            {"text": "test", "start_seconds": 11.0, "end_seconds": 11.25},
        ]

        segments = build_caption_segments_from_words(
            words,
            clip_start_seconds=10.0,
            clip_duration_seconds=5.0,
        )

        self.assertEqual(len(segments), 1)
        self.assertEqual(segments[0].text, "This is a real caption test")
        self.assertEqual(segments[0].start_seconds, 0.0)
        self.assertEqual(segments[0].end_seconds, 1.25)

    def test_words_outside_clip_window_are_trimmed(self):
        words = [
            {"text": "before", "start_seconds": 8.0, "end_seconds": 9.8},
            {"text": "start", "start_seconds": 9.8, "end_seconds": 10.2},
            {"text": "inside", "start_seconds": 10.2, "end_seconds": 10.5},
            {"text": "end", "start_seconds": 11.8, "end_seconds": 12.3},
            {"text": "after", "start_seconds": 12.3, "end_seconds": 12.6},
        ]

        segments = build_caption_segments_from_words(
            words,
            clip_start_seconds=10.0,
            clip_duration_seconds=2.0,
        )

        self.assertEqual(len(segments), 1)
        self.assertEqual(segments[0].text, "start inside end")
        self.assertEqual(segments[0].start_seconds, 0.0)
        self.assertEqual(segments[0].end_seconds, 2.0)

    def test_word_grouping_obeys_max_words(self):
        words = [
            {"text": word, "start_seconds": index * 0.2, "end_seconds": index * 0.2 + 0.15}
            for index, word in enumerate(["one", "two", "three", "four", "five", "six", "seven"])
        ]

        segments = build_caption_segments_from_words(
            words,
            clip_start_seconds=0.0,
            clip_duration_seconds=3.0,
            max_words=3,
        )

        self.assertEqual([segment.text for segment in segments], ["one two three", "four five six", "seven"])
        self.assertEqual([segment.index for segment in segments], [1, 2, 3])

    def test_empty_word_list_preserves_fallback_decision(self):
        self.assertEqual(
            build_caption_segments_from_words([], clip_start_seconds=0.0, clip_duration_seconds=5.0),
            [],
        )

        fallback = build_caption_segments("Fallback caption text", duration_seconds=4.0)
        self.assertGreater(len(fallback), 0)
        self.assertEqual(fallback[0].start_seconds, 0.0)


if __name__ == "__main__":
    unittest.main()
