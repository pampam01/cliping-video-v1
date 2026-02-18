import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from dotenv import load_dotenv
load_dotenv()

import unittest
from moviepy.editor import ColorClip
from services.video_processor import VideoProcessor

import unittest
from unittest.mock import MagicMock, patch
from moviepy.editor import ColorClip
from services.video_processor import VideoProcessor

class TestHookEffects(unittest.TestCase):
    def setUp(self):
        # Patch __init__ to avoid loading heavy models
        with patch.object(VideoProcessor, '__init__', return_value=None):
            self.processor = VideoProcessor()
            # Manually set up any required attributes if needed (none for this method)

    def test_apply_visual_effects(self):
        # Create a dummy 3-second red clip
        clip = ColorClip(size=(1080, 1920), color=(255, 0, 0), duration=3)
        
        # Apply effects
        # We need to mock vfx import inside the method if it wasn't imported at top level
        # But it is imported at top level in video_processor.py
        
        processed_clip = self.processor.apply_visual_effects(clip)
        
        # Check if duration is preserved
        self.assertEqual(processed_clip.duration, 3)
        
        # Check if size is preserved (since we crop back)
        self.assertEqual(processed_clip.size, (1080, 1920))
        
        print("\n✅ Visual effects applied successfully without errors.")

if __name__ == '__main__':
    unittest.main()
