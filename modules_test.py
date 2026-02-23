#############################################################################
# modules_test.py
#
# This file contains tests for modules.py.
#
# You will write these tests in Unit 2.
#############################################################################

import unittest
from streamlit.testing.v1 import AppTest
from modules import UserProfile, GeminiChatbot #display_post, display_activity_summary, display_genai_advice, display_recent_workouts

# Write your tests below



class UserProfile(unittest.TestCase):
    """Tests the UserProfile function."""

    def test_foo(self):
        """Tests foo."""
        pass


class TestGeminiChatbot(unittest.TestCase):
    """Tests the GeminiChatbot function."""

    def test_foo(self):
        """Tests foo."""
        pass


if __name__ == "__main__":
    unittest.main()
