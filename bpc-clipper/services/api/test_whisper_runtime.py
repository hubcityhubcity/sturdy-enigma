import os
import sys
import unittest
from types import SimpleNamespace
from unittest.mock import Mock, patch

from transcription_adapter import WhisperTranscriptionProvider


class WhisperRuntimeTests(unittest.TestCase):
    def test_provider_loads_model_from_configured_cache(self):
        fake_model = object()
        fake_whisper = SimpleNamespace(load_model=Mock(return_value=fake_model))
        provider = WhisperTranscriptionProvider("base")

        with patch.dict(sys.modules, {"whisper": fake_whisper}):
            with patch.dict(os.environ, {"WHISPER_DOWNLOAD_ROOT": "/tmp/titan-models"}, clear=False):
                loaded = provider._load_model()

        self.assertIs(loaded, fake_model)
        fake_whisper.load_model.assert_called_once_with("base", download_root="/tmp/titan-models")


if __name__ == "__main__":
    unittest.main()
