#############################################################################
# modules_test.py
#
# This file contains tests for modules.py.
#
# You will write these tests in Unit 2.
#############################################################################

import unittest
from streamlit.testing.v1 import AppTest
from modules import GeminiChatbot, Render_Job, CompanySearch #display_post, display_activity_summary, display_genai_advice, display_recent_workouts
from unittest.mock import patch
import modules

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
#fake container that behaves like a real Streamlit container, but does nothing.
class DummyContainer:
    def __enter__(self): return self
    def __exit__(self, exc_type, exc, tb): return False
    
class TestJobRender(unittest.TestCase):
        def test_render_skills(self):
                html = modules.render_skills(["Python"])
                self.assertIn("Python", html)
                self.assertIn('class="chip"', html)

        #This replaces the Streamlit rendering call with a mock function during this test.
        @patch("modules.components.html") 
        def test_render_job_outputs_html(self, mock_html):
                jobs = [{
                        "id": "google-1",
                        "company": "Google",
                        "title": "Software Engineer Intern Summer 2026",
                        "description": "Work on scalable systems.",
                        "skills": ["Python", "Git"],
                        "experience": "Projects accepted",
                        "location": "Florida",
                        }]
                #Calls a mock_html
                modules.Render_Job(DummyContainer(), jobs)

                # Grab the HTML passed to components.html
                html = mock_html.call_args[0][0]

                # Basic checks
                self.assertIn("Google", html)
                self.assertIn("Software Engineer Intern Summer 2026", html)
                self.assertIn("Work on scalable systems.", html)
                self.assertIn("Python", html)
                self.assertIn("Git", html)
                self.assertIn("Florida", html)



if __name__ == "__main__":
    unittest.main()

