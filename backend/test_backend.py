import unittest
import threading
from unittest.mock import patch

from spatial import get_spatial_cue
from dedup import should_speak, _spoken
from context_engine import build_speech

class TestBackend(unittest.TestCase):

    def setUp(self):
        _spoken.clear()

    def test_spatial(self):
        w, h = 1000, 1000
        
        # Center bbox, 40% height -> directly ahead, 1 meter
        bbox_center = (400, 300, 600, 700) # cx=500 -> directly ahead, height=400 -> ratio=0.40 (>0.30)
        res1 = get_spatial_cue(bbox_center, (w, h))
        self.assertEqual(res1['direction'], "directly ahead")
        self.assertEqual(res1['distance_label'], "approximately 1 meter")

        # Left-third bbox -> "to your left" (cx = 200 < 333)
        bbox_left = (100, 300, 300, 700)
        res2 = get_spatial_cue(bbox_left, (w, h))
        self.assertEqual(res2['direction'], "to your left")

        # Right-third bbox -> "to your right" (cx = 800 > 666)
        bbox_right = (700, 300, 900, 700)
        res3 = get_spatial_cue(bbox_right, (w, h))
        self.assertEqual(res3['direction'], "to your right")

        # Tiny sign ratio 0.05 -> far ahead
        bbox_tiny = (450, 450, 550, 500) # height=50 -> ratio=0.05
        res4 = get_spatial_cue(bbox_tiny, (w, h))
        self.assertEqual(res4['distance_label'], "far ahead")

    @patch('dedup.time.time')
    def test_dedup(self, mock_time):
        mock_time.return_value = 100.0
        
        self.assertTrue(should_speak("STOP"))
        self.assertFalse(should_speak("STOP"))
        self.assertTrue(should_speak("EXIT"))
        
        # Advance 6 seconds
        mock_time.return_value = 106.0
        self.assertTrue(should_speak("STOP"))

    def test_context_engine(self):
        # NO ENTRY -> is_danger=True
        speech1, is_danger1 = build_speech("NO ENTRY", {})
        self.assertTrue(is_danger1)
        self.assertIn("No entry", speech1)
        
        # pharmacy -> is_danger=False
        speech2, is_danger2 = build_speech("pharmacy", {})
        self.assertFalse(is_danger2)
        
        # Hindi
        speech3, is_danger3 = build_speech("प्रवेश निषेध", {})
        self.assertTrue(is_danger3)
        self.assertIn("No entry", speech3)
        
        # Fallback raw text parsing regex + safety check
        speech4, is_danger4 = build_speech("UNKNOWN XYZ", {})
        self.assertTrue(speech4.startswith("Sign reads:"))

    def test_thread_safety(self):
        results = []
        threads = []
        
        def run():
            results.append(should_speak("THREAD_STOP"))
            
        for _ in range(10):
            t = threading.Thread(target=run)
            threads.append(t)
            t.start()
            
        for t in threads:
            t.join()
            
        trues = [r for r in results if r is True]
        self.assertEqual(len(trues), 1)

if __name__ == '__main__':
    unittest.main()
