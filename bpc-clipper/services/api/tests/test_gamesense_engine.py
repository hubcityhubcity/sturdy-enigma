import unittest

from gamesense_engine import GameSignal, build_gamesense_moments


class GameSenseEngineTests(unittest.TestCase):
    def test_clutch_reaction_and_chat_fuse_into_one_strong_moment(self):
        signals = [
            GameSignal("clutch", "gameplay", 100.0, 103.0, intensity=97, confidence=0.96),
            GameSignal("scream", "audio", 103.1, 104.2, intensity=92, confidence=0.93),
            GameSignal("reaction", "facecam", 103.2, 105.0, intensity=88, confidence=0.9),
            GameSignal("chat_spike", "chat", 104.0, 106.0, intensity=91, confidence=0.95),
        ]

        moments = build_gamesense_moments(signals)

        self.assertEqual(len(moments), 1)
        best = moments[0]
        self.assertEqual(best.category, "clutch")
        self.assertGreaterEqual(best.score, 90)
        self.assertEqual(best.start_seconds, 92.0)
        self.assertGreaterEqual(best.end_seconds, 112.0)
        self.assertIn("gameplay", best.explanation)
        self.assertIn("audio", best.explanation)
        self.assertIn("chat", best.explanation)

    def test_audio_and_visual_signals_become_one_reaction_candidate(self):
        signals = [
            GameSignal("audio_spike", "audio", 50.0, 51.5, intensity=93, confidence=0.95),
            GameSignal("scene_change", "visual", 51.0, 51.35, intensity=75, confidence=0.8),
            GameSignal("scene_change", "visual", 52.0, 52.35, intensity=73, confidence=0.8),
        ]

        moments = build_gamesense_moments(signals)

        self.assertEqual(len(moments), 1)
        self.assertEqual(moments[0].category, "reaction_moment")
        self.assertIn("audio spike", moments[0].explanation)
        self.assertIn("scene change", moments[0].explanation)

    def test_far_apart_highlights_are_preserved(self):
        signals = [
            GameSignal("clutch", "gameplay", 30.0, 32.0, intensity=95, confidence=1.0),
            GameSignal("scream", "audio", 32.0, 33.0, intensity=90, confidence=1.0),
            GameSignal("victory", "gameplay", 120.0, 123.0, intensity=96, confidence=1.0),
            GameSignal("chat_spike", "chat", 123.0, 125.0, intensity=92, confidence=1.0),
        ]

        moments = build_gamesense_moments(signals)

        self.assertEqual(len(moments), 2)
        self.assertEqual({moment.category for moment in moments}, {"clutch", "victory"})

    def test_single_low_signal_does_not_create_a_clip(self):
        moments = build_gamesense_moments([
            GameSignal("round_end", "gameplay", 20.0, 21.0, intensity=25, confidence=0.5),
        ])
        self.assertEqual(moments, [])

    def test_rage_gets_setup_and_reaction_room(self):
        moments = build_gamesense_moments([
            GameSignal("rage", "audio", 60.0, 63.0, intensity=95, confidence=1.0),
            GameSignal("reaction", "facecam", 61.0, 64.0, intensity=90, confidence=1.0),
        ])

        self.assertGreaterEqual(len(moments), 1)
        best = moments[0]
        self.assertEqual(best.category, "rage_moment")
        self.assertEqual(best.start_seconds, 52.0)
        self.assertGreaterEqual(best.end_seconds, 70.0)


if __name__ == "__main__":
    unittest.main()
