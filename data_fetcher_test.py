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
        """Helper: returns a fake BigQuery result with a cnt field."""
        mock_row = MagicMock()
        mock_row.cnt = count
        mock_result = MagicMock()
        mock_result.__iter__ = MagicMock(return_value=iter([mock_row]))
        return mock_result

    @patch("data_fetcher.bq_client")
    def test_returns_correct_count(self, mock_bq):
        """Should return the count from BigQuery."""
        mock_bq.query.return_value.result.return_value = self._make_mock_result(3)
        result = data_fetcher.get_job_count_by_company("Tech Solutions Inc.")
        self.assertEqual(result, 3)

    @patch("data_fetcher.bq_client")
    def test_returns_zero_for_unknown_company(self, mock_bq):
        """Should return 0 when company has no listings."""
        mock_bq.query.return_value.result.return_value = self._make_mock_result(0)
        result = data_fetcher.get_job_count_by_company("Unknown Corp")
        self.assertEqual(result, 0)

    @patch("data_fetcher.bq_client")
    def test_returns_integer_type(self, mock_bq):
        """Return type must be int."""
        mock_bq.query.return_value.result.return_value = self._make_mock_result(2)
        result = data_fetcher.get_job_count_by_company("Google")
        self.assertIsInstance(result, int)

    @patch("data_fetcher.bq_client")
    def test_returns_zero_on_error(self, mock_bq):
        """Should return 0 gracefully if BigQuery raises an exception."""
        mock_bq.query.side_effect = Exception("BigQuery error")
        result = data_fetcher.get_job_count_by_company("Google")
        self.assertEqual(result, 0)

    @patch("data_fetcher.bq_client")
    def test_query_uses_company_name_parameter(self, mock_bq):
        """Should pass company_name as a query parameter."""
        mock_bq.query.return_value.result.return_value = self._make_mock_result(1)
        data_fetcher.get_job_count_by_company("Tech Solutions Inc.")
        self.assertTrue(mock_bq.query.called)
        _, kwargs = mock_bq.query.call_args
        params = kwargs["job_config"].query_parameters
        param_values = [p.value for p in params]
        self.assertIn("Tech Solutions Inc.", param_values)


class TestSearchJobs(unittest.TestCase):

    @patch("data_fetcher.bq_client")
    def test_returns_list(self, mock_bq):
        """Should always return a list."""
        mock_bq.query.return_value.result.return_value = iter([])
        result = data_fetcher.search_jobs("engineer")
        self.assertIsInstance(result, list)

    @patch("data_fetcher.bq_client")
    def test_returns_empty_list_on_no_match(self, mock_bq):
        """Should return [] when no jobs match the keyword."""
        mock_bq.query.return_value.result.return_value = iter([])
        result = data_fetcher.search_jobs("blockchain quantum")
        self.assertEqual(result, [])

    @patch("data_fetcher.bq_client")
    def test_returns_empty_list_on_error(self, mock_bq):
        """Should return [] gracefully if BigQuery raises an exception."""
        mock_bq.query.side_effect = Exception("BigQuery error")
        result = data_fetcher.search_jobs("engineer")
        self.assertEqual(result, [])

    @patch("data_fetcher.bq_client")
    def test_query_uses_keyword_parameter(self, mock_bq):
        """Should pass keyword as a query parameter."""
        mock_bq.query.return_value.result.return_value = iter([])
        data_fetcher.search_jobs("Python")
        self.assertTrue(mock_bq.query.called)
        _, kwargs = mock_bq.query.call_args
        params = kwargs["job_config"].query_parameters
        param_values = [p.value for p in params]
        self.assertIn("Python", param_values)

    @patch("data_fetcher.bq_client")
    def test_returns_matching_jobs(self, mock_bq):
        """Should return jobs that match the keyword."""
        fake_jobs = [
            {
                "job_ID": "j1",
                "company_name": "Tech Solutions Inc.",
                "title": "Backend Software Engineer",
                "description": "Work with Python and SQL.",
                "location": "Remote",
                "job_type": "Full-time",
                "salary_min": 80000,
                "salary_max": 120000,
                "date_posted": "2024-01-01",
                "date_expire": "2024-06-01",
                "skills": ["Python", "SQL"]
            }
        ]
        mock_bq.query.return_value.result.return_value = iter(fake_jobs)
        result = data_fetcher.search_jobs("Python")
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]["company_name"], "Tech Solutions Inc.")
        self.assertIn("Python", result[0]["skills"])


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

    @patch("db_handler.os.getenv")
    @patch("db_handler.bigquery.Client")
    def test_insert_jobs_to_bigquery_success(self, mock_client_class, mock_getenv):
        def fake_getenv(key):
            values = {
                "PROJECT_ID": "John_Doe",
                "DATABASE_ID": "jobs"
            }
            return values.get(key)

        mock_getenv.side_effect = fake_getenv

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
                "skills": ["python", "git"]
            }
        ]

        errors = db_handler.insert_jobs_to_bigquery(jobs)

        self.assertEqual(errors["job_errors"], [])
        self.assertEqual(errors["skill_errors"], [])
        self.assertEqual(errors["job_skill_errors"], [])
        self.assertEqual(mock_client.insert_rows_json.call_count, 3)

    @patch("db_handler.os.getenv")
    @patch("db_handler.bigquery.Client")
    def test_get_jobs_from_bigquery(self, mock_client_class, mock_getenv):
        def fake_getenv(key):
            values = {
                "PROJECT_ID": "John_Doe",
                "DATABASE_ID": "jobs"
            }
            return values.get(key)

        mock_getenv.side_effect = fake_getenv

        row1 = MagicMock()
        row1.job_ID = "123"
        row1.company_name = "Google"
        row1.title = "Software Engineer Intern"
        row1.description = "Python and Git required."
        row1.location = "Remote"
        row1.skills = ["python", "git"]

        row2 = MagicMock()
        row2.job_ID = "456"
        row2.company_name = "Meta"
        row2.title = "Backend Engineer Intern"
        row2.description = "Java and SQL required."
        row2.location = "California"
        row2.skills = ["java", "sql"]

        fake_rows = [row1, row2]

        mock_client = MagicMock()
        mock_query_job = MagicMock()
        mock_query_job.result.return_value = fake_rows
        mock_client.query.return_value = mock_query_job
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


# ... (existing code) ...

class TestGetChatContext(unittest.TestCase):
    @patch("data_fetcher.bq_client")
    def test_get_chat_context_success(self, mock_bq):
        """Should return a list of dictionaries with chat history."""
        # Create a fake row that mimics BigQuery behavior
        mock_row = {"user_prompt": "Hello", "ai_response": "Hi there!"}
        
        # Configure the mock to return our fake row
        mock_query_job = MagicMock()
        mock_query_job.result.return_value = [mock_row]
        mock_bq.query.return_value = mock_query_job

        result = data_fetcher.get_chat_context("user123", "job456")

        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]["user_prompt"], "Hello")
        self.assertEqual(result[0]["ai_response"], "Hi there!")

    @patch("data_fetcher.bq_client")
    def test_get_chat_context_empty(self, mock_bq):
        """Should return an empty list if no history exists."""
        mock_bq.query.return_value.result.return_value = []
        result = data_fetcher.get_chat_context("new_user", "job1")
        self.assertEqual(result, [])


class TestSaveChatSession(unittest.TestCase):
    @patch("data_fetcher.bq_client")
    def test_save_chat_session_success(self, mock_bq):
        """Should return True if BigQuery insert has no errors."""
        # BigQuery returns an empty list [] if there are no errors
        mock_bq.insert_rows_json.return_value = []
        
        result = data_fetcher.save_chat_session(
            "u1", "r1", "j1", "How is my resume?", "It looks great!"
        )
        self.assertTrue(result)
        # Ensure it was called once
        self.assertEqual(mock_bq.insert_rows_json.call_count, 1)

    @patch("data_fetcher.bq_client")
    def test_save_chat_session_failure(self, mock_bq):
        """Should return False if BigQuery returns errors."""
        # Mocking an error response from BigQuery
        mock_bq.insert_rows_json.return_value = [{"errors": "Table not found"}]
        
        result = data_fetcher.save_chat_session("u1", "r1", "j1", "prompt", "response")
        self.assertFalse(result)


class TestGetResumeWithSkills(unittest.TestCase):
    @patch("data_fetcher.bq_client")
    def test_get_resume_with_skills_success(self, mock_bq):
        """Should return a dictionary with resume details and skill list."""
        # Define fake data coming from BigQuery
        fake_row = {
            "name": "Jane Doe",
            "location": "Miami",
            "university": "FIU",
            "skills": ["Python", "SQL", "Cloud"]
        }
        
        mock_query_job = MagicMock()
        mock_query_job.result.return_value = [fake_row]
        mock_bq.query.return_value = mock_query_job

        result = data_fetcher.get_resume_with_skills("res_001")

        self.assertEqual(result["name"], "Jane Doe")
        self.assertEqual(len(result["skills"]), 3)
        self.assertIn("Python", result["skills"])

    @patch("data_fetcher.bq_client")
    def test_get_resume_not_found(self, mock_bq):
        """Should return an empty dictionary if resume ID doesn't exist."""
        mock_bq.query.return_value.result.return_value = []
        result = data_fetcher.get_resume_with_skills("fake_id")
        self.assertEqual(result, {})



if __name__ == "__main__":
    unittest.main()