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

if __name__ == "__main__":
    unittest.main()