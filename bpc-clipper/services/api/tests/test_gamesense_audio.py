import unittest

from gamesense_audio import AudioLevel, detect_audio_spikes_from_levels, parse_astats_metadata


class GameSenseAudioTests(unittest.TestCase):
    def test_parses_astats_metadata_with_pts(self):
        output = """
frame:0    pts:0       pts_time:0
lavfi.astats.Overall.RMS_level=-42.5
frame:1    pts:24000   pts_time:0.5
lavfi.astats.Overall.RMS_level=-18.2
"""
        levels = parse_astats_metadata(output)
        self.assertEqual(len(levels), 2)
        self.assertEqual(levels[0].seconds, 0.0)
        self.assertEqual(levels[1].seconds, 0.5)
        self.assertEqual(levels[1].rms_db, -18.2)

    def test_detects_and_merges_short_loud_reaction(self):
        levels = [
            AudioLevel(0.0, -45.0),
            AudioLevel(0.5, -44.0),
            AudioLevel(1.0, -43.0),
            AudioLevel(1.5, -16.0),
            AudioLevel(2.0, -14.0),
            AudioLevel(2.5, -17.0),
            AudioLevel(3.0, -44.0),
        ]
        spikes = detect_audio_spikes_from_levels(levels)
        self.assertEqual(len(spikes), 1)
        spike = spikes[0]
        self.assertEqual(spike.start_seconds, 1.5)
        self.assertEqual(spike.end_seconds, 3.0)
        self.assertGreaterEqual(spike.intensity, 80)
        self.assertEqual(spike.peak_db, -14.0)
        self.assertLess(spike.baseline_db, -40.0)

    def test_steady_audio_does_not_create_false_spikes(self):
        levels = [AudioLevel(index * 0.5, -28.0 + (index % 2) * 0.5) for index in range(12)]
        self.assertEqual(detect_audio_spikes_from_levels(levels), [])


if __name__ == "__main__":
    unittest.main()
