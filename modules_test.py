#############################################################################
# modules_test.py
#
# This file contains tests for modules.py.
#
# You will write these tests in Unit 2.
#############################################################################

import unittest
from streamlit.testing.v1 import AppTest
from unittest.mock import patch, MagicMock
import sys
import streamlit as st
import os

# Write your tests below
os.environ["GEMINI_API_KEY"]="mock_key"
from modules import GeminiChatbot, Render_Job, CompanySearch, ProfilePage, ResumeUploader, KeywordMatcher, NavBar #display_post, display_activity_summary, display_genai_advice, display_recent_workouts
import modules
import sqlite3

class TestGeminiChatbot(unittest.TestCase):
    def setUp(self):
        """Initialize the app simulation before each test."""
        self.at = AppTest.from_file("app.py").run()

    @patch("modules.client.models.generate_content")
    @patch("modules.save_chat_log")
    def test_chatbot_full_flow(self, mock_save_log, mock_gemini):
        """Test that typing a message triggers Gemini and saves to the DB."""
        
        # 1. Setup Mock Response from Gemini
        mock_response = MagicMock()
        mock_response.text = "I am a mock AI response for your resume."
        mock_gemini.return_value = mock_response

        # 2. Simulate user input in the chatbot
        # We find the chat input and set a value
        if self.at.chat_input:
            self.at.chat_input[0].set_value("How is my resume?").run()

            # 3. Assertions: Did the session state update?
            messages = self.at.session_state.messages
            self.assertTrue(len(messages) >= 2)
            self.assertEqual(messages[-2]["content"], "How is my resume?")
            self.assertEqual(messages[-1]["content"], "I am a mock AI response for your resume.")

            # 4. Assertion: Was the Database function called?
            self.assertTrue(mock_save_log.called)
            # Verify it was called with the right prompt
            args, kwargs = mock_save_log.call_args
            self.assertEqual(kwargs['prompt'], "How is my resume?")

    def test_resume_context_handling(self):
        """Test if the chatbot uses the resume context from session state."""
        # Manually inject a resume into session state
        self.at.session_state.user_resume = "Experience: Python Developer at Google"
        self.at.run()
        
        self.assertEqual(self.at.session_state.user_resume, "Experience: Python Developer at Google")

    @patch("modules.client.models.generate_content")
    def test_ai_error_handling(self, mock_gemini):
        """Test if the app displays an error message when the AI fails (404/500)."""
        # Simulate an API Failure
        mock_gemini.side_effect = Exception("API Error")
        
        if self.at.chat_input:
            self.at.chat_input[0].set_value("Hi").run()
            
            # Look for the error message in the UI
            self.assertTrue(self.at.error)


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

                mock_html.assert_called_once()
                
                # Grab the HTML passed to components.html
                html = mock_html.call_args[0][0]

                # Basic checks
                self.assertIn("Google", html)
                self.assertIn("Software Engineer Intern Summer 2026", html)
                self.assertIn("Work on scalable systems.", html)
                self.assertIn("Python", html)
                self.assertIn("Git", html)
                self.assertIn("Florida", html)

########## code change ##########
class TestNavigation(unittest.TestCase):
    def setUp(self):
        """Initialize the app simulation."""
        self.at = AppTest.from_file("app.py").run()

    def test_navbar_home_button(self):
        """Test if clicking the Home button in NavBar sets page to home."""
        # Find the home button in the navbar
        home_btn = self.at.button(key="nav_home_btn")
        home_btn.click().run()
        
        # Check if session state updated
        self.assertEqual(self.at.session_state.page, "home")

    def test_profile_button_navigation(self):
        """Test if the user icon button switches page to profile."""
        # Find the profile button in the CompanySearch module
        profile_btn = self.at.button(key="user_profile_btn")
        profile_btn.click().run()
        
        # Check if session state updated
        self.assertEqual(self.at.session_state.page, "profile")



class TestProfilePage(unittest.TestCase):
    def setUp(self):
        """Initialize and navigate to profile page."""
        self.at = AppTest.from_file("app.py").run()
        # Force the app into profile mode
        self.at.session_state.page = "profile"
        self.at.run()

    def test_profile_display_elements(self):
        """Test if profile page shows user details."""
        # Check for the Title and User Name (checking subheader values)
        self.assertTrue(any("User Profile" in s.value for s in self.at.title))
        self.assertTrue(any("John Doe" in s.value for s in self.at.subheader))


    def test_resume_text_persistence(self):
        """Test if typing in the text area saves to session state."""
        # Switch to text mode first
        self.at.button(key="btn_text").click().run()
        
        # Find text area and input dummy resume
        text_area = self.at.text_area(key="resume_text_area")
        text_area.set_value("Experience with Python and Streamlit").run()
        
        # Verify it saved to session state
        self.assertEqual(self.at.session_state.user_resume, "Experience with Python and Streamlit")
class TestResumeAndMatcherLogic(unittest.TestCase):
    def setUp(self):
        """Initialize the app simulation."""
        self.at = AppTest.from_file("app.py").run()
    def test_uploader_clears_session_state(self):
        """Test if the cleanup logic removes current_resume when uploader is empty."""
        # Manually inject data to simulate an existing upload
        self.at.session_state['current_resume'] = "Mock Resume"
        
        # Run the app; because the uploader is empty, the 'else' block should trigger
        self.at.run()

        # Verify that the logic correctly deleted the key from session state
        self.assertNotIn('current_resume', self.at.session_state, 
                "Logic failed to delete 'current_resume' when uploader was empty.")

    def test_matcher_disabled_state_ui(self):
        """Test if the Matcher shows the warning when no resume exists."""
        # Ensure the state is empty to trigger the 'disabled' UI branch
        if 'current_resume' in self.at.session_state:
                del self.at.session_state['current_resume']
        self.at.run()

        # Verify the specific button is disabled
        self.assertTrue(self.at.button(key="disabled_match_btn").disabled)
        
        # Verify that the warning caption is visible to the user
        warning_exists = any("Please upload a resume" in cap.value for cap in self.at.caption)
        self.assertTrue(warning_exists)

class TestNavBar(unittest.TestCase):
    def setUp(self):
        self.at = AppTest.from_file("app.py").run()

    def test_home_button(self):
        # Get button
        home_btn = self.at.button(key="nav_home_btn")
        
        # Click and rerun
        home_btn.click().run()
        
        # Check if session state updated
        self.assertEqual(self.at.session_state.page, "home")
    
    def test_profile_button(self):
        # Get button
        profile_btn = self.at.button(key="nav_profile_btn")
        
        # Click and rerun
        profile_btn.click().run()
        
        # Check if session state updated
        self.assertEqual(self.at.session_state.page, "profile")

class TestSearchIntegration(unittest.TestCase):
    def setUp(self):
        """Initialize the app simulation."""
        self.at = AppTest.from_file("app.py").run()

    def test_search_filtering_logic(self):
        """Test if the search bar correctly filters job results."""
        
        # 1. Select search input and type 'Google'
        search_bar = self.at.text_input(key="search_with_user_icon")
        search_bar.set_value("Google").run()

        # 2. Check the info feedback
        self.assertIn("Google", self.at.info[0].value)

        # 3. Find the iframe component
        iframes = self.at.get("iframe")
        self.assertTrue(len(iframes) > 0, "No iframe components found")
        
        # 4. Use 'srcdoc' Accessing the proto object to get the internal HTML content
        rendered_content = iframes[0].proto.srcdoc
        
        # 5. Final Assertion
        self.assertIn("Google", rendered_content)


if __name__ == "__main__":
    unittest.main()

