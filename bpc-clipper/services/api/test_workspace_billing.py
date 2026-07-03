import unittest
from uuid import uuid4

from fastapi import HTTPException
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from database import Base
import models  # noqa: F401
import workspace_models  # noqa: F401
from models import Project, Source
from workspace_billing import claim_project, create_workspace, enforce_source_quota, usage_snapshot


class WorkspaceBillingTests(unittest.TestCase):
    def setUp(self):
        engine = create_engine("sqlite://")
        Base.metadata.create_all(engine)
        self.db = sessionmaker(bind=engine)()

    def tearDown(self):
        self.db.close()

    def test_source_minutes_are_metered_for_workspace_projects(self):
        workspace, access_key = create_workspace(self.db, "Test Workspace")
        self.assertTrue(access_key.startswith("titan_"))
        project = Project(id=str(uuid4()), name="Test", source_type="upload", rights_confirmed=True, status="created")
        self.db.add(project)
        self.db.flush()
        claim_project(self.db, workspace, project.id)
        self.db.add(Source(id=str(uuid4()), project_id=project.id, source_type="upload", title="sample", duration_seconds=60.0, validation_status="valid", rights_confirmed=True))
        self.db.commit()

        usage = usage_snapshot(self.db, workspace)
        self.assertEqual(usage["source_minutes_used"], 1.0)
        self.assertEqual(usage["exports_used"], 0)

    def test_free_workspace_rejects_overage_before_source_is_saved(self):
        workspace, _ = create_workspace(self.db, "Limit Test")
        project = Project(id=str(uuid4()), name="Test", source_type="upload", rights_confirmed=True, status="created")
        self.db.add(project)
        self.db.flush()
        claim_project(self.db, workspace, project.id)
        self.db.add(Source(id=str(uuid4()), project_id=project.id, source_type="upload", title="near-limit", duration_seconds=29 * 60, validation_status="valid", rights_confirmed=True))
        self.db.commit()

        with self.assertRaises(HTTPException) as raised:
            enforce_source_quota(self.db, workspace, 2 * 60)
        self.assertEqual(raised.exception.status_code, 402)


if __name__ == "__main__":
    unittest.main()
