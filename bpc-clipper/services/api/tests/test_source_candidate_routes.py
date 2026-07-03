import unittest
from types import SimpleNamespace

from fastapi import HTTPException

from source_candidate_routes import list_source_candidates


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
    def __init__(self, project, source, candidates):
        self.project = project
        self.source = source
        self.candidates = candidates

    def get(self, model, identifier):
        if model.__name__ == "Project":
            return self.project if identifier == "project-1" else None
        if model.__name__ == "Source":
            return self.source if identifier == "source-1" else None
        return None

    def query(self, model):
        return FakeQuery(self.candidates)


class SourceCandidateRouteTests(unittest.TestCase):
    def test_returns_only_verified_source_candidates(self):
        candidate = SimpleNamespace(
            id="candidate-1", project_id="project-1", source_id="source-1",
            start_seconds=10.0, end_seconds=20.0, title="Moment", excerpt="Clip text",
            score=91, category="clutch", explanation="Strong evidence", score_breakdown={}, risk_flags=[], status="candidate",
        )
        db = FakeDb(
            project=SimpleNamespace(id="project-1"),
            source=SimpleNamespace(id="source-1", project_id="project-1"),
            candidates=[candidate],
        )

        result = list_source_candidates("project-1", "source-1", db)

        self.assertEqual(result["project_id"], "project-1")
        self.assertEqual(result["source_id"], "source-1")
        self.assertEqual(result["candidates"][0]["candidate_id"], "candidate-1")

    def test_rejects_source_owned_by_another_project(self):
        db = FakeDb(
            project=SimpleNamespace(id="project-1"),
            source=SimpleNamespace(id="source-1", project_id="project-2"),
            candidates=[],
        )

        with self.assertRaises(HTTPException) as raised:
            list_source_candidates("project-1", "source-1", db)

        self.assertEqual(raised.exception.status_code, 404)
        self.assertEqual(raised.exception.detail, "source_not_found")


if __name__ == "__main__":
    unittest.main()
