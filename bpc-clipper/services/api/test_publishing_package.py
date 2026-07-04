import unittest
from types import SimpleNamespace

from publishing_package import build_publishing_package


class PublishingPackageTests(unittest.TestCase):
    def test_package_contains_publishable_assets(self):
        export = SimpleNamespace(id="export-1")
        edit = SimpleNamespace(id="edit-1", hook_text="The truth is I had to learn discipline before I could change my life.", start_seconds=10.0, end_seconds=42.0)
        candidate = SimpleNamespace(id="candidate-1", excerpt="fallback", category="emotional_moment")

        package = build_publishing_package(export, edit, candidate)

        self.assertEqual(package["export_id"], "export-1")
        self.assertEqual(package["candidate_id"], "candidate-1")
        self.assertTrue(package["title_options"])
        self.assertTrue(package["caption_options"])
        self.assertTrue(package["hashtags"])
        self.assertGreater(package["duration_seconds"], 0)
        self.assertTrue(package["publishing_checklist"])


if __name__ == "__main__":
    unittest.main()
