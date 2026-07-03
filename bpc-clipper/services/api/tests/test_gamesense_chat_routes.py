import unittest
from types import SimpleNamespace
from unittest.mock import patch

from gamesense_chat_routes import ChatDetectionRequest, automatic_chat_events, detect_gamesense_chat


class FakeQuery:
    def __init__(self, events):
        self.events = events

    def filter(self, *args):
        return self

    def order_by(self, *args):
        return self

    def all(self):
        return self.events


class FakeDb:
    def __init__(self, source, events):
        self.source = source
        self.events = events
        self.deleted = []
        self.did_flush = False
        self.did_commit = False

    def get(self, model, identifier):
        return self.source if identifier == self.source.id else None

    def query(self, model):
        return FakeQuery(self.events)

    def delete(self, event):
        self.deleted.append(event)

    def flush(self):
        self.did_flush = True

    def add(self, event):
        pass

    def commit(self):
        self.did_commit = True

    def refresh(self, event):
        pass


class GameSenseChatRouteTests(unittest.TestCase):
    def test_keeps_only_automatic_detector_events(self):
        automatic = SimpleNamespace(evidence={"detector": "chat_burst_v1"})
        manual = SimpleNamespace(evidence={"detector": "manual_note_v1"})
        missing = SimpleNamespace(evidence={})
        null_evidence = SimpleNamespace(evidence=None)

        result = automatic_chat_events([automatic, manual, missing, null_evidence])

        self.assertEqual(result, [automatic])

    @patch("gamesense_chat_routes.detect_chat_spikes", return_value=[])
    def test_recalculation_deletes_only_automatic_chat_events(self, _detect_chat_spikes):
        automatic = SimpleNamespace(evidence={"detector": "chat_burst_v1"})
        manual = SimpleNamespace(evidence={"detector": "manual_note_v1"})
        source = SimpleNamespace(id="source-1", project_id="project-1")
        db = FakeDb(source, [automatic, manual])
        payload = ChatDetectionRequest(messages=[{"seconds": 12.0, "text": "W"}], replace_existing=True)

        result = detect_gamesense_chat("source-1", payload, db)

        self.assertEqual(db.deleted, [automatic])
        self.assertNotIn(manual, db.deleted)
        self.assertTrue(db.did_flush)
        self.assertTrue(db.did_commit)
        self.assertEqual(result["created_count"], 0)


if __name__ == "__main__":
    unittest.main()
