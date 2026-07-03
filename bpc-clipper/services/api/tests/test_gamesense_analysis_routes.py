import unittest
from unittest.mock import Mock

from gamesense_analysis_routes import delete_automatic_events


class GameSenseAnalysisRouteTests(unittest.TestCase):
    def test_delete_automatic_events_removes_existing_detector_events(self):
        first = Mock()
        second = Mock()
        query = Mock()
        query.filter.return_value = query
        query.all.return_value = [first, second]
        db = Mock()
        db.query.return_value = query

        delete_automatic_events(db, "source-123")

        self.assertEqual(db.delete.call_count, 2)
        db.flush.assert_called_once()


if __name__ == "__main__":
    unittest.main()
