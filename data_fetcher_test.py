#############################################################################
# data_fetcher_test.py
#
# This file contains tests for data_fetcher.py.
#
# You will write these tests in Unit 3.
#############################################################################
import unittest
from unittest.mock import patch
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


    "End of job data testing."
    


if __name__ == "__main__":
    unittest.main()