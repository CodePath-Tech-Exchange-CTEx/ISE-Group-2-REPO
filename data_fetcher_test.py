#############################################################################
# data_fetcher_test.py
#
# This file contains tests for data_fetcher.py.
#
# You will write these tests in Unit 3.
#############################################################################
import unittest
from unittest.mock import patch, MagicMock
import data_fetcher
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

        self.assertIn("results", fake_response)
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

        self.assertEqual(job["id"], "123")
        self.assertEqual(job["company"], "Google")
        self.assertEqual(job["title"], "Software Engineer Intern")
        self.assertEqual(job["location"], "Remote")
        self.assertIn("python", job["skills"])
        self.assertIn("sql", job["skills"])
        self.assertIn("git", job["skills"])
        self.assertEqual(job["experience"], "0-2 years of experience")

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

    


if __name__ == "__main__":
    unittest.main()