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
    def test_user_profile_renders(self):
        """Tests that UserProfile displays the correct subheader."""
        # 1. Setup: We initialize a simulated Streamlit app
        at = AppTest.from_string("""
import streamlit as st
from modules import UserProfile
container = st.container()
UserProfile(container)
        """).run()

        # 2. Execution & Assertion: 
        # We check if the subheader "User Profile" exists in the rendered output.
        # This confirms our function actually 'wrote' to the container.
        self.assertTrue(len(at.subheader) > 0)
        self.assertEqual(at.subheader[0].value, "Profile")

   


class TestGeminiChatbot(unittest.TestCase):
    def test_gemini_chatbot_interaction(self):
        """Tests the Chatbot UI and its mock response logic."""
        # 1. Setup: Simulate the chatbot inside the app
        at = AppTest.from_string("""
import streamlit as st
from modules import GeminiChatbot
container = st.container()
GeminiChatbot(container)
        """).run()

        # 2. Action: Simulate a user typing "Hello" into the chat input
        # In software testing, this is 'Input Simulation'.
        at.chat_input[0].set_value("Hello").run()

        # 3. Assertions:
        # Check if the user message was added to the chat
        self.assertIn("Hello", at.markdown[0].value)
        
        # Check if the mock assistant response appeared
        # This confirms our session_state logic and response logic are working.
        expected_response = "I'll be ready to analyze your resume once the API is linked!"
        self.assertIn(expected_response, at.markdown[1].value)


if __name__ == "__main__":
    unittest.main()
