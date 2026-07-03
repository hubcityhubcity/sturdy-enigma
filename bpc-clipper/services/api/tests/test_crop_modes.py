import unittest

from render_scaffold import crop_filter_for_mode, resolve_crop_mode


class CropModeTests(unittest.TestCase):
    def test_crop_mode_aliases(self):
        self.assertEqual(resolve_crop_mode("speaker_focus"), "center_focus")
        self.assertEqual(resolve_crop_mode("left"), "left_focus")
        self.assertEqual(resolve_crop_mode("right_focus"), "right_focus")
        self.assertEqual(resolve_crop_mode("unknown_mode"), "center_focus")

    def test_horizontal_framing_presets(self):
        self.assertEqual(crop_filter_for_mode("left_focus"), "crop=1080:1920:0:(ih-oh)/2")
        self.assertEqual(crop_filter_for_mode("right_focus"), "crop=1080:1920:iw-ow:(ih-oh)/2")
        self.assertEqual(crop_filter_for_mode("speaker_focus"), "crop=1080:1920:(iw-ow)/2:(ih-oh)/2")

    def test_vertical_framing_presets(self):
        self.assertEqual(crop_filter_for_mode("top_focus"), "crop=1080:1920:(iw-ow)/2:0")
        self.assertEqual(crop_filter_for_mode("bottom_focus"), "crop=1080:1920:(iw-ow)/2:ih-oh")


if __name__ == "__main__":
    unittest.main()
