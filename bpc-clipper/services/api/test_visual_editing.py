import unittest

from visual_editing import (
    FaceBox,
    FaceObservation,
    assign_face_tracks,
    build_crop_keyframes,
    build_shots,
    build_visual_edit_plan,
    choose_primary_tracks,
)


class VisualEditingTests(unittest.TestCase):
    def test_tracking_preserves_ids_for_the_same_moving_face(self):
        observations = [
            FaceObservation(0.0, FaceBox(0.18, 0.2, 0.18, 0.18)),
            FaceObservation(0.3, FaceBox(0.20, 0.2, 0.18, 0.18)),
            FaceObservation(0.6, FaceBox(0.22, 0.2, 0.18, 0.18)),
        ]
        tracked = assign_face_tracks(observations)
        self.assertEqual({item.track_id for item in tracked}, {"face_1"})

    def test_tracking_creates_a_new_id_for_a_distinct_face(self):
        observations = [
            FaceObservation(0.0, FaceBox(0.10, 0.2, 0.15, 0.15)),
            FaceObservation(0.2, FaceBox(0.70, 0.2, 0.15, 0.15)),
        ]
        tracked = assign_face_tracks(observations)
        self.assertEqual([item.track_id for item in tracked], ["face_1", "face_2"])

    def test_nearby_cut_candidates_do_not_create_chattery_shots(self):
        shots = build_shots(12.0, [(2.0, 0.60), (2.3, 0.95), (7.0, 0.80)], minimum_shot_seconds=1.0)
        self.assertEqual(len(shots), 3)
        self.assertAlmostEqual(shots[0].end_seconds, 2.3)
        self.assertAlmostEqual(shots[1].end_seconds, 7.0)

    def test_primary_focus_resists_a_weaker_challenger(self):
        shots = build_shots(8.0, [(4.0, 0.9)])
        observations = [
            FaceObservation(0.5, FaceBox(0.20, 0.2, 0.24, 0.24, 0.95), "face_1"),
            FaceObservation(0.5, FaceBox(0.62, 0.2, 0.20, 0.20, 0.95), "face_2"),
            FaceObservation(4.5, FaceBox(0.23, 0.2, 0.22, 0.22, 0.95), "face_1"),
            FaceObservation(4.5, FaceBox(0.62, 0.2, 0.23, 0.23, 0.95), "face_2"),
        ]
        primary = choose_primary_tracks(observations, shots)
        self.assertEqual(primary[0], "face_1")
        self.assertEqual(primary[1], "face_1")

    def test_crop_keyframes_limit_reframing_speed(self):
        shots = build_shots(2.0, [])
        observations = [
            FaceObservation(0.1, FaceBox(0.05, 0.2, 0.20, 0.20), "face_1"),
            FaceObservation(1.9, FaceBox(0.80, 0.2, 0.20, 0.20), "face_1"),
        ]
        primary = {0: "face_1"}
        keyframes = build_crop_keyframes(observations, shots, primary, max_pan_per_second=0.10)
        self.assertEqual(len(keyframes), 2)
        self.assertLessEqual(abs(keyframes[-1].center_x - keyframes[0].center_x), 0.20 + 1e-9)

    def test_plan_warns_when_no_faces_exist(self):
        plan = build_visual_edit_plan(5.0, [], [(2.0, 0.8)])
        self.assertTrue(plan.warnings)
        self.assertEqual(len(plan.keyframes), 4)


if __name__ == "__main__":
    unittest.main()
