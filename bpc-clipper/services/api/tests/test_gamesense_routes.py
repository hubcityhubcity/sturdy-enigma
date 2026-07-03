import unittest
from types import SimpleNamespace

from gamesense_routes import generate_gamesense_candidates
from models import Project, Source


class FakeQuery:
    def __init__(self, rows):
        self.rows = rows

    def filter(self, *args):
        return self

    def order_by(self, *args):
        return self

    def all(self):
        return self.rows


class FakeDb:
    def __init__(self):
        self.project = SimpleNamespace(id="project-1")
        self.source = SimpleNamespace(id="source-1", project_id="project-1")

    def get(self, model, identifier):
        if model is Project and identifier == self.project.id:
            return self.project
        if model is Source and identifier == self.source.id:
            return self.source
        return None

    def query(self, model):
        return FakeQuery([])


class GameSenseRouteTests(unittest.TestCase):
    def test_empty_source_returns_zero_result_with_next_step_message(self):
        result = generate_gamesense_candidates("project-1", source_id="source-1", db=FakeDb())

        self.assertEqual(result["project_id"], "project-1")
        self.assertEqual(result["source_id"], "source-1")
        self.assertEqual(result["generated_count"], 0)
        self.assertEqual(result["candidates"], [])
        self.assertIn("No GameSense evidence", result["message"])


if __name__ == "__main__":
    unittest.main()
