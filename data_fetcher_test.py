#############################################################################
# data_fetcher_test.py
#
# This file contains tests for data_fetcher.py.
#
# You will write these tests in Unit 3.
#############################################################################
import unittest
import data_fetcher
import db_handler
from unittest.mock import patch, MagicMock
import extractor


class TestDataFetcher(unittest.TestCase):

    "Start of job data testing."

    # Patch API call, it will call amock object instead of contacting the internet
    @patch("data_fetcher.requests.get") 
    def test_fetch_adzuna_jobs(self, mock_get): # get_mock = fake version of request.get
        fake_response = {
            "count": 1,
            "results": [
                {
                    "id": "123",
                    "title": "Software Engineer",
                    "description": "Python and Git required. 2+ years of experience.",
                    "company": {"display_name": "Google"},
                    "location": {"display_name": "Remote"}
                }]}

        # Tell the json what it should return
        mock_get.return_value.json.return_value = fake_response

        # We must insert this method, otherwise python will complain the function doesn't exist
        mock_get.return_value.raise_for_status.return_value = None

        data = data_fetcher.fetch_adzuna_jobs()

        self.assertIn("results", data)
        self.assertEqual(len(data["results"]), 1)
        self.assertEqual(data["results"][0]["title"], "Software Engineer")
        

    def test_parse_jobs(self):
        fake_api_data = {
            "results": [
                {
                    "id": "123",
                    "title": "Software Engineer Intern",
                    "description": "Python, SQL, and Git required. 0-2 years of experience.",
                    "company": {"display_name": "Google"},
                    "location": {"display_name": "Remote"}
                }]}
        
        jobs = data_fetcher.parse_jobs(fake_api_data)

        self.assertEqual(len(jobs), 1)

        job = jobs[0]

        self.assertEqual(job["job_id"], "123")
        self.assertEqual(job["company_name"], "Google")
        self.assertEqual(job["job_title"], "Software Engineer Intern")
        self.assertEqual(job["job_location"], "Remote")
        self.assertIn("python", job["skills"])
        self.assertIn("sql", job["skills"])
        self.assertIn("git", job["skills"])
        self.assertEqual(job["experience_requirements"], "0-2 years of experience")

    def test_extract_skills(self):
        description = "We need Python, Docker, AWS, and Git experience."

        skills = extractor.extract_skills(description)

        self.assertIn("python", skills)
        self.assertIn("docker", skills)
        self.assertIn("aws", skills)
        self.assertIn("git", skills)
    
    def test_extract_skills_empty(self):
        description = "Great opportunity for motivated engineers."

        skills = extractor.extract_skills(description)

        self.assertEqual(skills, [])

    def test_extract_experience(self):
        description = "Candidates must have 3+ years of experience in backend development."

        experience = extractor.extract_experience(description)

        self.assertEqual(experience, "3+ years of experience")

    def test_extract_experience_none(self):
        description = "Great opportunity for motivated engineers."

        experience = extractor.extract_experience(description)

        self.assertIsNone(experience)


class TestGetJobCountByCompany(unittest.TestCase):
    def _make_mock_result(self, count):
        mock_row = MagicMock()
        mock_row.cnt = count
        mock_result = MagicMock()
        mock_result.__iter__ = MagicMock(return_value=iter([mock_row]))
        return mock_result

    # CHANGE: Patch the function 'get_bq_client' instead of 'bq_client'
    @patch("data_fetcher.get_bq_client")
    def test_returns_correct_count(self, mock_get_client):
        """Should return the count from BigQuery."""
        mock_bq = mock_get_client.return_value
        mock_bq.query.return_value.result.return_value = self._make_mock_result(3)
        
        result = data_fetcher.get_job_count_by_company("Tech Solutions Inc.")
        self.assertEqual(result, 3)

    @patch("data_fetcher.get_bq_client")
    def test_returns_zero_for_unknown_company(self, mock_get_client):
        mock_bq = mock_get_client.return_value
        mock_bq.query.return_value.result.return_value = self._make_mock_result(0)
        result = data_fetcher.get_job_count_by_company("Unknown Corp")
        self.assertEqual(result, 0)

    @patch("data_fetcher.get_bq_client")
    def test_returns_integer_type(self, mock_get_client):
        mock_bq = mock_get_client.return_value
        mock_bq.query.return_value.result.return_value = self._make_mock_result(2)
        result = data_fetcher.get_job_count_by_company("Google")
        self.assertIsInstance(result, int)

    @patch("data_fetcher.get_bq_client")
    def test_returns_zero_on_error(self, mock_get_client):
        mock_get_client.side_effect = Exception("BigQuery error")
        result = data_fetcher.get_job_count_by_company("Google")
        self.assertEqual(result, 0)

class TestSearchJobs(unittest.TestCase):

    @patch("data_fetcher.get_bq_client")
    def test_returns_list(self, mock_get_client):
        mock_bq = mock_get_client.return_value
        mock_bq.query.return_value.result.return_value = iter([])
        result = data_fetcher.search_jobs("engineer")
        self.assertIsInstance(result, list)

    @patch("data_fetcher.get_bq_client")
    def test_returns_matching_jobs(self, mock_get_client):
        mock_bq = mock_get_client.return_value
        fake_jobs = [{"company_name": "Tech Solutions Inc.", "skills": ["Python"]}]
        mock_bq.query.return_value.result.return_value = iter(fake_jobs)
        result = data_fetcher.search_jobs("Python")
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]["company_name"], "Tech Solutions Inc.")


class TestBigQueryInsert(unittest.TestCase):

    @patch("data_fetcher.insert_jobs_to_bigquery")
    @patch("data_fetcher.parse_jobs")
    @patch("data_fetcher.fetch_adzuna_jobs")
    def test_fetch_and_save_success(self, mock_fetch, mock_parse, mock_insert):
        mock_fetch.return_value = {"results": []}
        mock_parse.return_value = [
            {
                "job_id": "123",
                "company_name": "Google",
                "job_title": "Software Engineer Intern",
                "job_description": "Python required.",
                "job_location": "Remote",
                "experience_requirements": "0-2 years of experience",
                "skills": ["python"]
            }
        ]

        mock_insert.return_value = {
            "job_errors": [],
            "skill_errors": [],
            "job_skill_errors": []
        }

        result = data_fetcher.fetch_and_save_jobs()

        self.assertTrue(result)
        mock_fetch.assert_called_once()
        mock_parse.assert_called_once()
        mock_insert.assert_called_once()

    @patch("db_handler.PROJECT_ID", "John_Doe")
    @patch("db_handler.DATABASE_ID", "jobs")
    @patch("db_handler.bigquery.Client")
    def test_insert_jobs_to_bigquery_success(self, mock_client_class):
        mock_client = MagicMock()
        mock_client.insert_rows_json.return_value = []
        mock_client_class.return_value = mock_client

        jobs = [
            {
                "job_id": "123",
                "company_name": "Google",
                "job_title": "Software Engineer Intern",
                "job_description": "Python and Git required.",
                "job_location": "Remote",
                "experience_requirements": "0-2 years of experience",
                "skills": ["python", "git"],
                "job_link": "https://google.com/careers"
            }
        ]

        errors = db_handler.insert_jobs_to_bigquery(jobs)

        self.assertEqual(errors["job_errors"], [])
        self.assertEqual(errors["skill_errors"], [])
        self.assertEqual(errors["job_skill_errors"], [])
        self.assertEqual(mock_client.insert_rows_json.call_count, 3)

        mock_client_class.assert_called_once_with(project="John_Doe")

        mock_client.insert_rows_json.assert_any_call(
            "John_Doe.jobs.JobInformation",
            [{
                "job_ID": "123",
                "company_name": "Google",
                "title": "Software Engineer Intern",
                "description": "Python and Git required.",
                "location": "Remote",
                "job_link": "https://google.com/careers"
            }]
        )

        mock_client.insert_rows_json.assert_any_call(
            "John_Doe.jobs.skillsTable",
            [
                {"skill_ID": "python", "skill_name": "python"},
                {"skill_ID": "git", "skill_name": "git"}
            ]
        )

        mock_client.insert_rows_json.assert_any_call(
            "John_Doe.jobs.jobSkillsTable",
            [
                {"job_skill_ID": "123_python", "job_ID": "123", "skill_ID": "python"},
                {"job_skill_ID": "123_git", "job_ID": "123", "skill_ID": "git"}
            ]
        )

    @patch("db_handler.PROJECT_ID", "John_Doe")
    @patch("db_handler.DATABASE_ID", "jobs")
    @patch("db_handler.bigquery.Client")
    def test_get_jobs_from_bigquery(self, mock_client_class):
        fake_row_1 = MagicMock()
        fake_row_1.job_ID = "123"
        fake_row_1.company_name = "Google"
        fake_row_1.title = "Software Engineer Intern"
        fake_row_1.description = "Python and Git required."
        fake_row_1.location = "Remote"
        fake_row_1.skills = ["python", "git"]

        fake_row_2 = MagicMock()
        fake_row_2.job_ID = "456"
        fake_row_2.company_name = "Meta"
        fake_row_2.title = "Backend Engineer Intern"
        fake_row_2.description = "Java and SQL required."
        fake_row_2.location = "California"
        fake_row_2.skills = ["java", "sql"]

        fake_rows = [fake_row_1, fake_row_2]

        mock_client = MagicMock()
        mock_client.query.return_value.result.return_value = fake_rows
        mock_client_class.return_value = mock_client

        jobs = db_handler.get_jobs_from_bigquery()

        self.assertEqual(len(jobs), 2)

        self.assertEqual(jobs[0]["id"], "123")
        self.assertEqual(jobs[0]["company"], "Google")
        self.assertEqual(jobs[0]["title"], "Software Engineer Intern")
        self.assertEqual(jobs[0]["description"], "Python and Git required.")
        self.assertEqual(jobs[0]["location"], "Remote")
        self.assertEqual(jobs[0]["skills"], ["python", "git"])

        self.assertEqual(jobs[1]["id"], "456")
        self.assertEqual(jobs[1]["company"], "Meta")
        self.assertEqual(jobs[1]["title"], "Backend Engineer Intern")
        self.assertEqual(jobs[1]["description"], "Java and SQL required.")
        self.assertEqual(jobs[1]["location"], "California")
        self.assertEqual(jobs[1]["skills"], ["java", "sql"])

        mock_client_class.assert_called_once_with(project="John_Doe")
        mock_client.query.assert_called_once()



    "End of job data testing."

class TestGetChatContext(unittest.TestCase):
    @patch("data_fetcher.get_bq_client")
    def test_get_chat_context_success(self, mock_get_client):
        mock_bq = mock_get_client.return_value
        mock_row = {"user_prompt": "Hello", "ai_response": "Hi there!"}
        mock_bq.query.return_value.result.return_value = [mock_row]

        result = data_fetcher.get_chat_context("user123", "job456")
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]["user_prompt"], "Hello")

class TestSaveChatSession(unittest.TestCase):
    @patch("data_fetcher.get_bq_client")
    def test_save_chat_session_success(self, mock_get_client):
        mock_bq = mock_get_client.return_value
        mock_bq.insert_rows_json.return_value = []
        
        result = data_fetcher.save_chat_session("u1", "r1", "j1", "prompt", "resp")
        self.assertTrue(result)

class TestGetResumeWithSkills(unittest.TestCase):
    @patch("data_fetcher.get_bq_client")
    def test_get_resume_with_skills_success(self, mock_get_client):
        mock_bq = mock_get_client.return_value
        fake_row = {"name": "Jane Doe", "skills": ["Python"]}
        mock_bq.query.return_value.result.return_value = [fake_row]

        result = data_fetcher.get_resume_with_skills("res_001")
        self.assertEqual(result["name"], "Jane Doe")

class TestDataFilter(unittest.TestCase):

    # --- Tests for filter_jobs_by_location ---
    @patch("data_fetcher.bq_client")
    def test_filter_jobs_by_location_success(self, mock_bq):
        """Should return a list of job dictionaries for a valid location."""
        fake_jobs = [{'job_ID': 'J004', 'title': 'DevOps Engineer', 'location': 'Austin, TX'}]
        
        # FIX: Hand it a result object, not just an iterator
        mock_bq.query.return_value.result.return_value = fake_jobs
        
        result = data_fetcher.filter_jobs_by_location('Austin, TX')
        
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]['location'], 'Austin, TX')

    # --- Tests for filter_jobs_by_skill_name ---
    @patch("data_fetcher.bq_client")
    def test_filter_jobs_by_skill_name_params(self, mock_bq):
        """Verify the skill_name is correctly passed as a parameter."""
        mock_bq.query.return_value = iter([])
        data_fetcher.filter_jobs_by_skill_name("Python")
        
        self.assertTrue(mock_bq.query.called)
        _, kwargs = mock_bq.query.call_args
        params = kwargs["job_config"].query_parameters
        # Check if "Python" was the value passed to the @skill_name parameter
        self.assertEqual(params[0].value, "Python")

    # --- Tests for get_resume_skills ---
    @patch("data_fetcher.bq_client")
    def test_get_resume_skills_returns_list(self, mock_bq):
        """Should return exactly the skills linked to the resume_ID."""
        fake_skills = [
            {'resume_ID': '1', 'skill_name': 'Kubernetes'},
            {'resume_ID': '1', 'skill_name': 'Python'}
        ]
        
        # FIX: Use the result chain here as well
        mock_bq.query.return_value.result.return_value = fake_skills
        
        result = data_fetcher.get_resume_skills('1')
        
        self.assertIsInstance(result, list)
        self.assertEqual(len(result), 2)
        self.assertEqual(result[1]['skill_name'], 'Python')

    @patch("data_fetcher.bq_client")
    def test_get_job_skills_returns_list(self, mock_bq):
        """Should return exactly the skills linked to the job_ID."""
        # 1. Create your fake database response
        fake_job_skills = [
            {'job_ID': 'J004', 'skill_name': 'Cloud Computing'},
            {'job_ID': 'J004', 'skill_name': 'Terraform'}
        ]
        
        # 2. Setup the mock chain: query() -> result() -> returns fake_job_skills
        mock_bq.query.return_value.result.return_value = fake_job_skills
        
        # 3. Call the actual function
        result = data_fetcher.get_job_skills('J004')
        
        # 4. Assertions (Verifying the output is correct)
        self.assertIsInstance(result, list, "The function must return a list.")
        self.assertEqual(len(result), 2, "The function should have found 2 skills.")
        self.assertEqual(result[0]['skill_name'], 'Cloud Computing')
        self.assertEqual(result[1]['job_ID'], 'J004')

    # --- Tests for get_project_with_skills ---
    @patch("data_fetcher.bq_client")
    def test_get_project_with_skills_structure(self, mock_bq):
        """Should return project titles and their associated skill names."""
        fake_projects = [{
            'project_title': 'Project B', 
            'skill_name': 'RESTful APIs', 
            'resume_ID': '102'
        }]

        mock_query_job = MagicMock()
        mock_query_job.result.return_value = fake_projects
        mock_bq.query.return_value = mock_query_job
        
        result = data_fetcher.get_project_with_skills('102')
        
        self.assertEqual(result[0]['project_title'], 'Project B')
        # mock_bq.query.return_value = iter(fake_projects)
        
        # result = data_fetcher.get_project_with_skills('102')
        
        # self.assertEqual(result[0]['project_title'], 'Project B')
        # self.assertIn('skill_name', result[0])

    # --- General Error Handling Test ---
    @patch("data_fetcher.bq_client")
    def test_all_functions_return_empty_on_error(self, mock_bq):
        """Verify catch-all error handling across data fetching functions."""
        mock_bq.query.side_effect = Exception("BigQuery connection timeout")

        self.assertEqual(data_fetcher.filter_jobs_by_location('fakelocation'), [])
        self.assertEqual(data_fetcher.filter_jobs_by_job_type('faketype'), [])
        self.assertEqual(data_fetcher.filter_jobs_by_skill_name('fakeskill'), [])
        self.assertEqual(data_fetcher.get_resume_skills('-1'), [])
        self.assertEqual(data_fetcher.get_job_skills('-1'), [])
        self.assertEqual(data_fetcher.get_project_with_skills('-1'), [])

    @patch("data_fetcher.bq_client")
    def test_all_functions_return_list_type(self, mock_bq):
        # 1. Mock a standard successful return
        mock_bq.query.return_value.result.return_value = [{'sample': 'data'}]
        
        # Test each function for list type on success
        self.assertIsInstance(data_fetcher.filter_jobs_by_location("fakelocation"), list, "Location filter must return a list.")
        self.assertIsInstance(data_fetcher.filter_jobs_by_job_type("faketype"), list, "Location filter must return a list.")
        self.assertIsInstance(data_fetcher.filter_jobs_by_skill_name("fakeskill"), list, "Location filter must return a list.")
        self.assertIsInstance(data_fetcher.get_resume_skills("102"), list, "Resume skills must return a list.")
        self.assertIsInstance(data_fetcher.get_job_skills("J002"), list, "Job skills must return a list.")
        self.assertIsInstance(data_fetcher.get_project_with_skills("102"), list, "Project skills must return a list.")

    # --- Tests for get_match_score ---
    @patch("data_fetcher.get_job_skills")
    @patch("data_fetcher.get_resume_skills")
    def test_get_match_score_calculation(self, mock_resume, mock_job):
        """Should correctly calculate percentage and identify common skills."""
        
        # 1. Setup: Resume has Python and SQL. Job wants Python and Java.
        mock_resume.return_value = [{'skill_name': 'Python'}, {'skill_name': 'SQL'}]
        mock_job.return_value = [{'skill_name': 'Python'}, {'skill_name': 'Java'}]
        
        # 2. Execute: (1 common skill / 2 total job skills) * 100 = 50.0%
        score, common = data_fetcher.get_match_score('res123', 'job456')
        
        # 3. Assert
        self.assertEqual(score, 50.0)
        self.assertEqual(common, {'Python'})

    @patch("data_fetcher.get_job_skills")
    @patch("data_fetcher.get_resume_skills")
    def test_get_match_score_perfect_match(self, mock_resume, mock_job):
        """Should return 100% when all job skills are present on the resume."""
        mock_resume.return_value = [{'skill_name': 'Python'}, {'skill_name': 'SQL'}, {'skill_name': 'Git'}]
        mock_job.return_value = [{'skill_name': 'Python'}, {'skill_name': 'SQL'}]
        
        score, _ = data_fetcher.get_match_score('res123', 'job456')
        
        self.assertEqual(score, 100.0)

    @patch("data_fetcher.get_job_skills")
    @patch("data_fetcher.get_resume_skills")
    def test_get_match_score_empty_job_skills(self, mock_resume, mock_job):
        """Should return 0.0 and avoid division by zero error if job has no skills."""
        mock_resume.return_value = [{'skill_name': 'Python'}]
        mock_job.return_value = [] # Empty job skills
        
        score, common = data_fetcher.get_match_score('res123', 'job456')
        
        self.assertEqual(score, 0.0)
        self.assertEqual(common, set())

    @patch("data_fetcher.bq_client")
    @patch("data_fetcher.sync_skill_to_db")
    @patch("data_fetcher.get_next_id")
    @patch("data_fetcher.ai_extract_resume_data")
    def test_save_resume_pipeline_success(self, mock_ai, mock_id, mock_sync, mock_bq):
        """Verify the full pipeline: AI extraction -> ID generation -> DB insertion."""
        
        # 1. Mock AI Response
        mock_ai.return_value = {
            "name": "Jane Doe",
            "location": "Miami, FL",
            "university": "FIU",
            "skills": ["Python", "SQL"]
        }
        
        # 2. Mock ID Generation
        # Side effect returns a new ID each time it's called
        mock_id.side_effect = ["RES105", "USR105", "RSK001", "RSK002"]
        
        # 3. Mock Skill Sync
        # Pretend Python is SK001 and SQL is SK002
        mock_sync.side_effect = ["SK001", "SK002"]
        
        # 4. Mock BigQuery Query Object
        # We need to mock the .result() call so it doesn't crash
        mock_bq.query.return_value.result.return_value = []

        # EXECUTE
        result_id = data_fetcher.save_resume_pipeline("Dummy PDF Text", "user123")

        # ASSERTIONS
        # Check if it returned the correct resume ID
        self.assertEqual(result_id, "RES105")
        
        # Verify the AI was called with our text
        mock_ai.assert_called_once_with("Dummy PDF Text")
        
        # Verify BigQuery was called for: 1 Resume Insert + 2 Skill Link Inserts = 3 total
        self.assertEqual(mock_bq.query.call_count, 3)
        
        # Verify the first call was the Resume Table insert
        first_call_args = mock_bq.query.call_args_list[0]
        self.assertIn("resumesTable", first_call_args[0][0])

class TestApplicationBigQuery(unittest.TestCase):

    @patch("db_handler.bigquery.Client")
    def test_insert_application(self, mock_client_class):
        mock_client = MagicMock()
        mock_client.query.return_value.result.return_value = None
        mock_client_class.return_value = mock_client

        result = db_handler.insert_application_to_bigquery(
            "id1", "Test Job", "2025-01-01"
        )

        self.assertEqual(result["application_id"], "id1")
        self.assertEqual(result["job_title"], "Test Job")
        self.assertEqual(result["status"], "Applied")
        mock_client.query.assert_called_once()


    @patch("db_handler.bigquery.Client")
    def test_update_application(self, mock_client_class):
        mock_client = MagicMock()

        mock_query_job = MagicMock()
        mock_query_job.result.return_value = None
        mock_query_job.errors = None

        mock_client.query.return_value = mock_query_job
        mock_client_class.return_value = mock_client

        errors = db_handler.update_application_status_in_bigquery(
            "id1", "Interview"
        )

        self.assertIsNone(errors)
        mock_client.query.assert_called_once()


    @patch("db_handler.bigquery.Client")
    def test_delete_application(self, mock_client_class):
        mock_client = MagicMock()

        mock_query_job = MagicMock()
        mock_query_job.result.return_value = None
        mock_query_job.errors = None

        mock_client.query.return_value = mock_query_job
        mock_client_class.return_value = mock_client

        errors = db_handler.delete_application_from_bigquery("id1")

        self.assertIsNone(errors)
        mock_client.query.assert_called_once()


    @patch("db_handler.bigquery.Client")
    def test_fetch_applications(self, mock_client_class):
        mock_client = MagicMock()

        fake_row = MagicMock()
        fake_row.application_id = "id1"
        fake_row.job_title = "Test Job"
        fake_row.status = "Applied"
        fake_row.applied_at = "2025-01-01"

        mock_client.query.return_value.result.return_value = [fake_row]
        mock_client_class.return_value = mock_client

        result = db_handler.fetch_applications_from_bigquery()

        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]["title"], "Test Job")
        self.assertEqual(result[0]["status"], "Applied")

class TestUserSavedJobs(unittest.TestCase):

    # --- Tests for delete_saved_job ---
    @patch("data_fetcher.bq_client")
    def test_delete_saved_job_success(self, mock_bq):
        # Mock a successful query execution with no errors
        mock_bq.query.return_value.result.return_value = None
        
        result = data_fetcher.delete_saved_job("user1", "job123")
        
        self.assertTrue(result)
        mock_bq.query.assert_called_once()

    @patch("data_fetcher.bq_client")
    def test_delete_saved_job_exception(self, mock_bq):
        # Force the query to throw an error
        mock_bq.query.side_effect = Exception("BigQuery connection dropped")
        
        result = data_fetcher.delete_saved_job("user1", "job123")
        
        self.assertFalse(result)

    # --- Tests for add_saved_job ---
    @patch("data_fetcher.get_next_id")
    @patch("data_fetcher.bq_client")
    def test_add_saved_job_success(self, mock_bq, mock_next_id):
        # We need to mock TWO database calls: the check query, and the insert query.
        
        # 1. The check query returns an empty list (meaning no duplicate exists)
        mock_check_result = MagicMock()
        mock_check_result.result.return_value = []
        
        # 2. The insert query executes successfully
        mock_insert_result = MagicMock()
        mock_insert_result.result.return_value = None
        
        # Apply the two mocked responses in order
        mock_bq.query.side_effect = [mock_check_result, mock_insert_result]
        
        # Mock the helper function to return the correct 'fav001' format
        mock_next_id.return_value = "fav001"
        
        result = data_fetcher.add_saved_job("user1", "job123")
        
        self.assertTrue(result)
        self.assertEqual(mock_bq.query.call_count, 2) # Verified it checked and inserted
        mock_next_id.assert_called_once()

    @patch("data_fetcher.bq_client")
    def test_add_saved_job_duplicate_found(self, mock_bq):
        # Mock the check query to return a pre-existing record
        mock_check_result = MagicMock()
        mock_check_result.result.return_value = [{"FavoriteId": "fav001"}]
        
        mock_bq.query.return_value = mock_check_result
        
        result = data_fetcher.add_saved_job("user1", "job123")
        
        # Should return False and stop before inserting
        self.assertFalse(result)
        self.assertEqual(mock_bq.query.call_count, 1)

    # --- Tests for get_user_saved_jobs ---
    @patch("data_fetcher.get_jobs")
    @patch("data_fetcher.bigquery.Client")
    def test_get_user_saved_jobs_success(self, mock_client_class, mock_get_jobs):
        # Mock the internal client initialized inside the function
        mock_client = MagicMock()
        mock_client_class.return_value = mock_client
        
        # Mock BigQuery returning one saved JobId
        mock_row = MagicMock()
        mock_row.JobId = "job_555"
        mock_client.query.return_value.result.return_value = [mock_row]
        
        # Mock the get_jobs() function to return our target job and a decoy job
        mock_get_jobs.return_value = [
            {
                "id": "job_555",
                "company": "Tech Innovations",
                "title": "Robotics Engineer",
                "date_expire": "2026-12-31"
            },
            {
                "id": "job_999", # This one should get filtered out
                "company": "Other Corp",
                "title": "Analyst",
                "date_expire": "2026-10-10"
            }
        ]
        
        result = data_fetcher.get_user_saved_jobs("user1")
        
        # Assertions
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]["id"], "job_555")
        self.assertEqual(result[0]["company"], "Tech Innovations")
        # Verify that 'date_expire' was successfully mapped to 'deadline'
        self.assertEqual(result[0]["deadline"], "2026-12-31")

class TestGetNextId(unittest.TestCase):
    @patch("data_fetcher.bq_client")
    def test_get_next_id_existing_records(self, mock_bq):
        # Mock the MAX() query finding an existing ID like 'fav042'
        mock_row = MagicMock()
        mock_row.max_id = "fav042"
        mock_bq.query.return_value.result.return_value = iter([mock_row])
        
        # It should strip 'fav', see 42, add 1, and pad it back to 3 digits
        result = data_fetcher.get_next_id("fake_table", "id_col", prefix="fav", padding=3)
        self.assertEqual(result, "fav043")

    @patch("data_fetcher.bq_client")
    def test_get_next_id_empty_table(self, mock_bq):
        # Mock an empty table (returns None or empty)
        mock_bq.query.return_value.result.return_value = iter([])
        
        result = data_fetcher.get_next_id("fake_table", "id_col", prefix="fav", padding=3)
        self.assertEqual(result, "fav001")

if __name__ == "__main__":
    unittest.main()