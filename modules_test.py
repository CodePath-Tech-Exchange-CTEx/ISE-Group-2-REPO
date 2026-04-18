#############################################################################
# modules_test.py
#
# This file contains tests for modules.py.
#
# You will write these tests in Unit 2.
#############################################################################
import io
import unittest
from streamlit.testing.v1 import AppTest
from unittest.mock import patch, MagicMock
import sys
import streamlit as st

# MOCK BIGQUERY AND VERTEX BEFORE IMPORTING MODULES
# This prevents the "DefaultCredentialsError" during the import phase
with patch('google.cloud.bigquery.Client'), \
     patch('vertexai.init'), \
     patch('vertexai.generative_models.GenerativeModel'):

    from modules import GeminiChatbot, Render_Job, CompanySearch, ProfilePage, ResumeUploader, KeywordMatcher, NavBar #display_post, display_activity_summary, display_genai_advice, display_recent_workouts
import modules

class TestGeminiChatbot(unittest.TestCase):
    def setUp(self):
        """Initialize the app simulation before each test."""
        self.at = AppTest.from_file("app.py").run()
        
        # Mocking the session state context required for the Chatbot
        self.at.session_state.current_resume_id = "res123"
        self.at.session_state.current_job_id = "job456"
        self.at.session_state.current_job_desc = "Software Engineer role"
        self.at.session_state.user_resume = "Extracted resume content: Python, Java, SQL."
        self.at.run()

    @patch("modules.get_gemini_model") 
    @patch("modules.get_resume_with_skills")
    @patch("modules.save_chat_session")
    def test_chatbot_full_flow(self, mock_save_chat, mock_get_resume, mock_get_model):
        """Test the full loop: Data Fetch -> AI Generation -> Data Save."""
        
        # 1. Setup Mock for BigQuery Resume Fetch
        mock_get_resume.return_value = {
            "name": "John Doe",
            "skills": ["Python", "SQL"]
        }

        # 2. Setup Mock for the Model Instance
        mock_model_inst = MagicMock()
        mock_get_model.return_value = mock_model_inst
        
        mock_response = MagicMock()
        mock_response.text = "Your Python skills match the job description perfectly."
        mock_model_inst.generate_content.return_value = mock_response

        # 3. Simulate user input in the chat_input
        if self.at.chat_input:
            # Setting value and running the script
            self.at.chat_input[0].set_value("Does my resume match?").run()

            # 4. ASSERTIONS
            # Verify BigQuery was called to get context
            mock_get_resume.assert_called_with("res123")
            
            # Check if the AI response was added to session state
            messages = self.at.session_state.messages
            self.assertEqual(messages[-1]["role"], "assistant")
            self.assertIn("Python skills", messages[-1]["content"])

            # Verify interaction was saved to BigQuery
            self.assertTrue(mock_save_chat.called)
            kwargs = mock_save_chat.call_args.kwargs
            self.assertEqual(kwargs['user_prompt'], "Does my resume match?") 

class TestApplyWindow(unittest.TestCase):

    @patch("modules.st.link_button")
    @patch("modules.st.write")
    @patch("modules.st.markdown")
    def test_render_apply_window_contents(self, mock_markdown, mock_write, mock_link_button):
        job = {
            "title": "Software Engineer Intern",
            "company": "DoubleVerify",
            "link": "https://example.com/apply/123"
        }

        modules.render_apply_window_contents(job)

        mock_markdown.assert_called_once_with("### Software Engineer Intern")
        mock_write.assert_called_once_with(
            "Apply for **DoubleVerify** via the official link below:"
        )
        mock_link_button.assert_called_once_with(
            "Go to Application Site",
            "https://example.com/apply/123",
            type="primary",
            use_container_width=True
        )

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


        @patch("modules.components.html")
        def test_favorite_button_in_html(self, mock_html):
            """Test that the bookmark button is rendered in each job card."""
            jobs = [{
            "id": "google-1",
            "company": "Google",
            "title": "Software Engineer Intern Summer 2026",
            "description": "Work on scalable systems.",
            "skills": ["Python", "Git"],
            "experience": "Projects accepted",
            "location": "Florida",
            }]
            modules.Render_Job(DummyContainer(), jobs)

            html = mock_html.call_args[0][0]

            # Check bookmark button and JS are present
            self.assertIn("bookmark-btn", html)
            self.assertIn("💾", html)
            self.assertIn("toggleBookmark", html)
            self.assertIn("bm-google-1", html)       



@unittest.skip("Blocked by Streamlit AppTest limitation in CI")
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


@unittest.skip("Blocked by Streamlit AppTest limitation in CI")
class TestProfilePage(unittest.TestCase):
    def setUp(self):
        """Initialize and navigate to profile page."""
        self.at = AppTest.from_file("app.py").run()
        # Force the app into profile mode
        self.at.session_state.page = "profile"

    @patch("modules.get_user_profile")
    def test_profile_displays_verified_user(self, mock_get_user_profile):
        """Test if profile page correctly shows a verified user's details."""
        # 1. Setup Mock Data for a verified user
        mock_user_data = {
            "first_name": "Jane",
            "last_name": "Doe",
            "email": "jane.doe@example.com",
            "date_created": "2024-01-15",
            "is_verified": True
        }
        mock_get_user_profile.return_value = mock_user_data

        # 2. Run the app test now that the patch is active
        self.at.run()

        # 3. Assertions
        self.assertEqual(self.at.title[0].value, "User Profile")
        self.assertEqual(self.at.subheader[0].value, "Jane Doe")
        # The user icon markdown is at index 1, email is at index 2
        self.assertIn("jane.doe<span>@</span>example.com", self.at.markdown[2].value)

        # Collect all `st.write` contents to check for presence
        write_outputs = "".join([w.value for w in self.at.write])
        self.assertIn("**Date created:** 2024-01-15", write_outputs)
        self.assertIn("**Verified:** ✅", write_outputs)

    @patch("modules.get_user_profile")
    def test_profile_displays_unverified_user(self, mock_get_user_profile):
        """Test if profile page correctly shows an unverified user's status."""
        # 1. Setup Mock Data for an unverified user
        mock_user_data = {
            "first_name": "John",
            "last_name": "Smith",
            "email": "j.smith@example.com",
            "date_created": "2024-02-20",
            "is_verified": False
        }
        mock_get_user_profile.return_value = mock_user_data

        # 2. Run the app test
        self.at.run()

        # 3. Assertions
        write_outputs = "".join([w.value for w in self.at.write])
        self.assertIn("**Verified:** ❌", write_outputs)

    @patch("modules.get_user_profile")
    def test_resume_text_persistence(self, mock_get_user_profile):
        """Test if typing in the text area saves to session state."""
        # Mock the profile data call to prevent errors during this unrelated test
        mock_get_user_profile.return_value = {"first_name": "Test", "last_name": "User", "email": "a@b.c", "date_created": "d", "is_verified": True}
        self.at.run()
        # Switch to text mode first
        self.at.button(key="btn_text").click().run()
        
        # Find text area and input dummy resume
        text_area = self.at.text_area(key="resume_text_area")
        text_area.set_value("Experience with Python and Streamlit").run()
        
        # Verify it saved to session state
        self.assertEqual(self.at.session_state.user_resume, "Experience with Python and Streamlit")

    @patch("modules.get_user_resume")
    @patch("modules.get_user_profile")
    def test_resume_dropdown_displays_resumes(self, mock_get_user_profile, mock_get_user_resume):
        """Test if the resume dropdown shows the correct resumes for a user."""
        # 1. Mock user profile to prevent other errors in the ProfilePage component
        mock_get_user_profile.return_value = {
            "first_name": "Test", "last_name": "User", "email": "a@b.c",
            "date_created": "2024-01-01", "is_verified": True
        }

        # 2. Mock resume data that the dropdown should display
        mock_resumes = {
            "RES-001": {"FILENAME": "Software_Engineer_Resume.pdf"},
            "RES-002": {"FILENAME": "Data_Analyst_Resume.docx"}
        }
        mock_get_user_resume.return_value = mock_resumes

        # 3. Run the app to render the profile page with the mocked data
        self.at.run()

        # 4. Assertions
        mock_get_user_resume.assert_called_with(1)
        self.assertTrue(any(t.value == "Resumes" for t in self.at.title), "'Resumes' title not found")

        # Find the selectbox for resumes by its label
        resume_selectbox = None
        for sb in self.at.selectbox:
            if sb.label == "All submitted resumes":
                resume_selectbox = sb
                break
        
        self.assertIsNotNone(resume_selectbox, "Resume selectbox with label 'All submitted resumes' not found.")
        self.assertEqual(resume_selectbox.options, list(mock_resumes.keys()))


@unittest.skip("Blocked by Streamlit AppTest limitation in CI")
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
        """Test if the Analyze button is disabled when no resume exists."""
        # Ensure state is empty
        if 'current_resume' in self.at.session_state:
            del self.at.session_state['current_resume']
        self.at.run()

        # Target the SINGLE button key
        analyze_btn = self.at.button(key="analyze_match_btn")
        
        # Assert it is disabled
        self.assertTrue(analyze_btn.disabled)
        self.assertTrue(any("Please upload a resume" in cap.value for cap in self.at.caption))

    def test_matcher_enabled_state_ui(self):
        """Test if the Analyze button is enabled when a resume is added."""

        self.at.session_state['current_resume'] = "Mock Resume"
        
        self.at.run()

        analyze_btn = self.at.button(key="analyze_match_btn")
        
        if 'current_resume' in self.at.session_state:
            self.assertFalse(analyze_btn.disabled)

    # test to see if there is an ouptut when a resume is added and the Analyze match score button is clicked.
    def test_analyze_output(self):
        self.at.session_state['current_resume'] = "Mock Resume"
        self.at.run()
        analyze_btn = self.at.button(key="analyze_match_btn")

        analyze_btn.click().run()
        matches_info = any("Matches found:" in i.value for i in self.at.info)
        self.assertTrue(matches_info)
    

    # test to see if when the resume is deleted after it has been analyzed once that the analyze matchscore button become disabled again
    def test_analyze_reset_after_resume_removed(self):
        self.at.session_state['current_resume'] = "Mock Resume"
        self.at.run()
        if 'current_resume' in self.at.session_state:
            del self.at.session_state['current_resume']
        self.at.run()

        analyze_btn = self.at.button(key="analyze_match_btn")
        self.assertTrue(analyze_btn.disabled)
        self.assertTrue(any("Please upload a resume" in cap.value for cap in self.at.caption))
        

@unittest.skip("Blocked by Streamlit AppTest limitation in CI")
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

@unittest.skip("Blocked by Streamlit AppTest limitation in CI")
class TestSearchIntegration(unittest.TestCase):
    def setUp(self):
        """Initialize the app simulation."""
        self.at = AppTest.from_file("app.py").run()


    @patch("data_fetcher.get_jobs")  
    def test_search_filtering_logic(self, mock_get_jobs):  
        """Test if the search bar correctly filters job results."""

        
        mock_get_jobs.return_value = [
            {"id": "g1", "company": "Google", "title": "Software Engineer",
             "description": "Python required", "skills": ["Python"], 
             "experience": "0-2 years", "location": "Remote"}
        ]


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

@unittest.skip("Blocked by Streamlit AppTest limitation in CI")
class TestApplicationTracker(unittest.TestCase):
    def setUp(self):
        """Initialize and navigate to tracker page."""
        self.at = AppTest.from_file("app.py").run()
        # Ensure session state is clean
        self.at.session_state.job_tracker = []
        self.at.session_state.page = "tracker"
        self.at.run()

    def test_add_job_flow(self):
        """Test adding a job with a title and date."""
        # 1. Fill out the form inside the expander
        self.at.text_input(key="add_job_form_Job Title").set_value("Frontend Engineer at Meta")
        
        # Streamlit testing handles dates as datetime.date objects
        import datetime
        test_date = datetime.date(2026, 4, 16)
        self.at.date_input(key="add_job_form_Date Applied").set_value(test_date)
        
        # 2. Submit the form
        self.at.button(key="add_job_form_Add to List").click().run()

        # 3. Assertions
        # Check if added to session state
        tracker_data = self.at.session_state.job_tracker
        self.assertEqual(len(tracker_data), 1)
        self.assertEqual(tracker_data[0]['title'], "Frontend Engineer at Meta")
        self.assertEqual(tracker_data[0]['date'], "2026-04-16")
        
        # Check if displayed on screen (using markdown or success message)
        self.assertTrue(any("Frontend Engineer at Meta" in m.value for m in self.at.markdown))

    def test_status_update(self):
        """Test if changing the status selectbox updates session state."""
        # 1. Manually inject a job into session state
        self.at.session_state.job_tracker = [{
            "id": 0,
            "title": "Backend Dev at Apple",
            "date": "2026-01-01",
            "status": "Applied"
        }]
        self.at.run()

        # 2. Find status selectbox and change value to 'Interview'
        status_box = self.at.selectbox(key="status_0")
        status_box.select("Interview").run()

        # 3. Assert state updated
        self.assertEqual(self.at.session_state.job_tracker[0]['status'], "Interview")

    def test_delete_job(self):
        """Test if clicking the trash icon removes the job."""
        # 1. Inject two jobs
        self.at.session_state.job_tracker = [
            {"id": 0, "title": "Job A", "date": "2026-01-01", "status": "Applied"},
            {"id": 1, "title": "Job B", "date": "2026-01-01", "status": "Applied"}
        ]
        self.at.run()

        # 2. Click delete on the first one
        self.at.button(key="delete_0").click().run()

        # 3. Assert only one job remains
        self.assertEqual(len(self.at.session_state.job_tracker), 1)
        self.assertEqual(self.at.session_state.job_tracker[0]['title'], "Job B")






if __name__ == "__main__":
    unittest.main()
