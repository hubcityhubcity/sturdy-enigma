import unittest
from types import SimpleNamespace

from gamesense_chat_routes import automatic_chat_events


class GameSenseChatRouteTests(unittest.TestCase):
    def test_keeps_only_automatic_detector_events(self):
        automatic = SimpleNamespace(evidence={"detector": "chat_burst_v1"})
        manual = SimpleNamespace(evidence={"detector": "manual_note_v1"})
        missing = SimpleNamespace(evidence={})
        null_evidence = SimpleNamespace(evidence=None)

        result = automatic_chat_events([automatic, manual, missing, null_evidence])

        self.assertEqual(result, [automatic])


if __name__ == "__main__":
    unittest.main()
