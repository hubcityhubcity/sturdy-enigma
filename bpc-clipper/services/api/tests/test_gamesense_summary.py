import unittest
from dataclasses import dataclass

from gamesense_summary import summarize_gamesense_events


@dataclass
class Event:
    event_type: str
    modality: str
    start_seconds: float
    end_seconds: float
    intensity: int
    confidence: float
    evidence: dict | None = None


class GameSenseSummaryTests(unittest.TestCase):
    def test_counts_modalities_and_orders_strongest_events(self):
        summary = summarize_gamesense_events([
            Event("scene_change", "visual", 12.0, 12.3, 72, 0.80),
            Event("audio_spike", "audio", 10.0, 11.0, 95, 0.92),
            Event("chat_spike", "chat", 10.5, 12.0, 88, 0.94),
        ])

        self.assertEqual(summary["total_events"], 3)
        self.assertEqual(summary["modality_counts"]["audio"], 1)
        self.assertEqual(summary["modality_counts"]["visual"], 1)
        self.assertEqual(summary["modality_counts"]["chat"], 1)
        self.assertEqual(summary["modality_counts"]["facecam"], 0)
        self.assertEqual(summary["event_type_counts"]["audio_spike"], 1)
        self.assertEqual(summary["strongest_events"][0]["event_type"], "audio_spike")
        self.assertEqual(summary["strongest_by_modality"]["chat"]["event_type"], "chat_spike")

    def test_chat_is_kept_when_overall_top_five_excludes_it(self):
        events = [
            Event(f"audio_{index}", "audio", index, index + 0.5, 100 - index, 0.9)
            for index in range(5)
        ]
        events.append(Event("chat_spike", "chat", 30.0, 31.0, 70, 0.8, {"top_terms": ["w"]}))

        summary = summarize_gamesense_events(events)

        self.assertNotIn("chat_spike", [event["event_type"] for event in summary["strongest_events"]])
        self.assertEqual(summary["strongest_by_modality"]["chat"]["event_type"], "chat_spike")
        self.assertEqual(summary["strongest_by_modality"]["chat"]["evidence"]["top_terms"], ["w"])

    def test_empty_summary_keeps_standard_modalities(self):
        summary = summarize_gamesense_events([])
        self.assertEqual(summary["total_events"], 0)
        self.assertEqual(summary["strongest_events"], [])
        self.assertEqual(summary["strongest_by_modality"], {})
        self.assertEqual(summary["modality_counts"]["audio"], 0)
        self.assertEqual(summary["modality_counts"]["gameplay"], 0)


if __name__ == "__main__":
    unittest.main()
