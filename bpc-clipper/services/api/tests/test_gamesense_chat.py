import unittest

from gamesense_chat import ChatMessage, detect_chat_spikes, hype_terms_for_message, is_hype_message


class GameSenseChatTests(unittest.TestCase):
    def test_detects_hype_language(self):
        self.assertTrue(is_hype_message("NO WAY clip that W W W"))
        terms = hype_terms_for_message("Somebody clip that holy shit W")
        self.assertIn("somebody_clip", terms)
        self.assertIn("clip_that", terms)
        self.assertIn("w", terms)

    def test_detects_burst_of_clipworthy_chat(self):
        messages = [
            ChatMessage(0.0, "normal chat"),
            ChatMessage(10.0, "NO WAY"),
            ChatMessage(10.4, "W"),
            ChatMessage(10.8, "clip that"),
            ChatMessage(11.1, "holy shit"),
            ChatMessage(11.4, "OMG"),
            ChatMessage(11.7, "W W W"),
            ChatMessage(12.0, "that was insane"),
            ChatMessage(12.2, "someone clip"),
            ChatMessage(20.0, "back to normal"),
        ]

        spikes = detect_chat_spikes(messages, min_messages=5)

        self.assertEqual(len(spikes), 1)
        spike = spikes[0]
        self.assertEqual(spike.start_seconds, 10.0)
        self.assertGreaterEqual(spike.intensity, 80)
        self.assertGreaterEqual(spike.hype_message_count, 6)
        self.assertIn("clip_that", spike.top_terms)
        self.assertGreaterEqual(len(spike.sample_messages), 3)
        self.assertGreater(spike.messages_per_second, spike.baseline_messages_per_second)

    def test_steady_low_hype_chat_does_not_create_spike(self):
        messages = [ChatMessage(index * 5.0, f"regular message {index}") for index in range(30)]
        self.assertEqual(detect_chat_spikes(messages), [])


if __name__ == "__main__":
    unittest.main()
