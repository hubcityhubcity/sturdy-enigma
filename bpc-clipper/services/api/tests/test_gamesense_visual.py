import unittest

from gamesense_visual import parse_showinfo_scene_times, scene_changes_from_times


class GameSenseVisualTests(unittest.TestCase):
    def test_parses_selected_frame_timestamps(self):
        log = """
[Parsed_showinfo_1 @ 0x0] n:   0 pts:  15360 pts_time:0.640000
[Parsed_showinfo_1 @ 0x0] n:   1 pts:  45600 pts_time:1.900000
[Parsed_showinfo_1 @ 0x0] n:   2 pts:  45600 pts_time:1.900000
"""
        self.assertEqual(parse_showinfo_scene_times(log), [0.64, 1.9])

    def test_creates_normalized_scene_change_events(self):
        changes = scene_changes_from_times([3.2, 18.75], threshold=0.3)
        self.assertEqual(len(changes), 2)
        self.assertEqual(changes[0].start_seconds, 3.2)
        self.assertEqual(changes[0].end_seconds, 3.55)
        self.assertGreaterEqual(changes[0].intensity, 60)
        self.assertGreaterEqual(changes[0].confidence, 0.5)
        self.assertEqual(changes[0].threshold, 0.3)

    def test_no_times_means_no_visual_events(self):
        self.assertEqual(scene_changes_from_times([], threshold=0.3), [])


if __name__ == "__main__":
    unittest.main()
