import unittest
from types import SimpleNamespace

from gamesense_engine import GameSignal, build_gamesense_moments
from scoring_engine import risk_flags_for_breakdown, score_segment


class TitanBrainRankingTests(unittest.TestCase):
    def segment(self, text: str, duration: float = 30.0):
        return SimpleNamespace(text=text, start_seconds=0.0, end_seconds=duration)

    def test_standalone_complete_clip_beats_mid_thought_open_loop(self):
        complete = score_segment(self.segment("The truth is I was broke, but then I realized the lesson was to build skills before chasing money."))
        dependent = score_segment(self.segment("And that is why they were wrong about it?"))

        self.assertGreater(complete.context.score, dependent.context.score)
        self.assertGreater(complete.payoff.score, dependent.payoff.score)
        self.assertGreater(complete.overall.score, dependent.overall.score)

    def test_risk_flags_explain_context_and_payoff_problems(self):
        breakdown = score_segment(self.segment("But they did it because of that?", duration=8.0)).as_dict()
        flags = risk_flags_for_breakdown(breakdown)

        self.assertIn("context_required", flags)
        self.assertIn("weak_payoff", flags)

    def test_multimodal_moment_beats_single_weak_detector_signal(self):
        single = build_gamesense_moments([
            GameSignal("audio_spike", "audio", 50.0, 51.0, intensity=95, confidence=0.95),
        ])
        multimodal = build_gamesense_moments([
            GameSignal("elimination", "gameplay", 50.0, 51.0, intensity=86, confidence=0.95),
            GameSignal("audio_spike", "audio", 50.2, 51.2, intensity=90, confidence=0.95),
            GameSignal("chat_spike", "chat", 50.4, 51.4, intensity=82, confidence=0.90),
        ])

        self.assertTrue(single)
        self.assertTrue(multimodal)
        self.assertGreater(multimodal[0].score, single[0].score)

    def test_duplicate_detector_hits_collapse_to_one_moment(self):
        moments = build_gamesense_moments([
            GameSignal("audio_spike", "audio", 20.0, 20.8, intensity=90, confidence=0.95),
            GameSignal("audio_spike", "audio", 20.3, 21.1, intensity=88, confidence=0.95),
            GameSignal("reaction", "facecam", 20.4, 21.2, intensity=86, confidence=0.90),
        ])

        self.assertEqual(len(moments), 1)


if __name__ == "__main__":
    unittest.main()
