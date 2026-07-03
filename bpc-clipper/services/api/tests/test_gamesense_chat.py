import unittest

from gamesense_chat import ChatMessage, detect_chat_spikes, is_hype_message


class GameSenseChatTests(unittest.TestCase):
    def test_detects_dense_hype_burst(self):
        messages = [
            ChatMessage(0.0, "normal"),
            ChatMessage(10.0, "hello"),
            ChatMessage(20.0, "watch this"),
            ChatMessage(30.0, "W"),
            ChatMessage(30.4, "OMG"),
            ChatMessage(30.8, "CLIP THAT"),
            ChatMessage(31.2, "NO WAY"),
            ChatMessage(31.6, "W W W"),
            ChatMessage(32.0, "GOAT"),
            ChatMessage(32.4, "INSANE"),
        ]

        spikes = detect_chat_spikes(messages)

        self.assertEqual(len(spikes), 1)
        spike = spikes[0]
        self.assertEqual(spike.start_seconds, 30.0)
        self.assertGreaterEqual(spike.message_count, 7)
        self.assertGreaterEqual(spike.hype_message_count, 6)
        self.assertGreaterEqual(spike.intensity, 80)
        self.assertGreater(spike.messages_per_second, spike.baseline_messages_per_second)

    def test_steady_chat_does_not_become_a_spike(self):
        messages = [ChatMessage(index * 2.0, "normal chat") for index in range(30)]
        self.assertEqual(detect_chat_spikes(messages), [])

    def test_hype_terms_cover_common_gaming_reactions(self):
        self.assertTrue(is_hype_message("W"))
        self.assertTrue(is_hype_message("clip that right now"))
        self.assertTrue(is_hype_message("NO WAY OMG"))
        self.assertFalse(is_hype_message("I think that was a smart rotation"))


if __name__ == "__main__":
    unittest.main()
