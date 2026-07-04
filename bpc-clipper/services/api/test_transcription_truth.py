import os
import unittest
from unittest.mock import patch

from transcription_adapter import MockTranscriptionProvider, TranscriptionConfigurationError, get_transcription_provider


class TranscriptionTruthTests(unittest.TestCase):
    def test_missing_provider_does_not_fall_back_to_demo_transcript(self):
        with patch.dict(os.environ, {}, clear=True):
            with self.assertRaises(TranscriptionConfigurationError):
                get_transcription_provider()

    def test_mock_provider_is_available_only_when_explicitly_selected(self):
        provider = get_transcription_provider("mock")
        self.assertIsInstance(provider, MockTranscriptionProvider)
        self.assertEqual(provider.name, "mock_demo")

    def test_unknown_provider_is_rejected(self):
        with self.assertRaises(TranscriptionConfigurationError):
            get_transcription_provider("not-a-provider")


if __name__ == "__main__":
    unittest.main()
