#############################################################################
# modules_test.py
#
# This file contains tests for modules.py.
#
# You will write these tests in Unit 2.
#############################################################################

import unittest
from streamlit.testing.v1 import AppTest
from modules import GeminiChatbot #display_post, display_activity_summary, display_genai_advice, display_recent_workouts

# Write your tests below





class TestGeminiChatbot(unittest.TestCase):
        def setUp(self):
                """Initialize the app simulation before each test."""
                self.at = AppTest.from_file("app.py").run()

      
        def test_chat_interaction(self):
                """Test if typing a message updates session state and gives a response."""
                # Simulate typing 'Hello' into the chat input
                # Note: at.chat_input[0] selects the first chat input found
                self.at.chat_input[0].set_value("Hello").run()

                # Check if the message was added to session_state
                messages = self.at.session_state.messages
                self.assertEqual(len(messages), 2)
                self.assertEqual(messages[0]["role"], "user")
                self.assertEqual(messages[0]["content"], "Hello")
                
                # Check if the mock assistant responded correctly
                self.assertEqual(messages[1]["role"], "assistant")
                self.assertIn("analyze your resume", messages[1]["content"])

class TestCompanySearch(unittest.TestCase):
    def setUp(self):
        """Initialize the app simulation before each test."""
        self.at = AppTest.from_file("app.py").run()

    def test_search_input(self):
        """Test if the company search bar accepts text."""
        # Find the text input by the key we set in modules.py
        search_bar = self.at.text_input(key="search_with_user_icon")
        
        # Simulate typing 'Google'
        search_bar.set_value("Google").run()

        # Check if the search bar's internal value is now 'Google'
        self.assertEqual(search_bar.value, "Google", "The search bar did not update its value")
if __name__ == "__main__":
    unittest.main()

