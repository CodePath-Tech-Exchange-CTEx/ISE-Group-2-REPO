#############################################################################
# data_fetcher.py
#
# This file contains functions to fetch data needed for the app.
#
# You will re-write these functions in Unit 3, and are welcome to alter the
# data returned in the meantime. We will replace this file with other data when
# testing earlier units.
#############################################################################

import random
import requests
import os
from extractor import *
from google.cloud import bigquery

bq_client = bigquery.Client()

users = {
    'user1': {
        'full_name': 'Remi',
        'username': 'remi_the_rems',
        'date_of_birth': '1990-01-01',
        'profile_image': 'https://upload.wikimedia.org/wikipedia/commons/c/c8/Puma_shoes.jpg',
        'friends': ['user2', 'user3', 'user4'],
    },
    'user2': {
        'full_name': 'Blake',
        'username': 'blake',
        'date_of_birth': '1990-01-01',
        'profile_image': 'https://upload.wikimedia.org/wikipedia/commons/c/c8/Puma_shoes.jpg',
        'friends': ['user1'],
    },
    'user3': {
        'full_name': 'Jordan',
        'username': 'jordanjordanjordan',
        'date_of_birth': '1990-01-01',
        'profile_image': 'https://upload.wikimedia.org/wikipedia/commons/c/c8/Puma_shoes.jpg',
        'friends': ['user1', 'user4'],
    },
    'user4': {
        'full_name': 'Gemmy',
        'username': 'gems',
        'date_of_birth': '1990-01-01',
        'profile_image': 'https://upload.wikimedia.org/wikipedia/commons/c/c8/Puma_shoes.jpg',
        'friends': ['user1', 'user3'],
    },
}


def get_user_profile(user_id):
    """Returns information about the given user.

    This function currently returns random data. You will re-write it in Unit 3.
    """
    if user_id not in users:
        raise ValueError(f'User {user_id} not found.')
    return users[user_id]


def get_user_posts(user_id):
    """Returns a list of a user's posts.

    This function currently returns random data. You will re-write it in Unit 3.
    """
    content = random.choice([
        'Had a great workout today!',
        'The AI really motivated me to push myself further, I ran 10 miles!',
    ])
    return [{
        'user_id': user_id,
        'post_id': 'post1',
        'timestamp': '2024-01-01 00:00:00',
        'content': content,
        'image': 'image_url',
    }]


def get_genai_advice(user_id):
    """Returns the most recent advice from the genai model.

    This function currently returns random data. You will re-write it in Unit 3.
    """
    advice = random.choice([
        'Your heart rate indicates you can push yourself further. You got this!',
        "You're doing great! Keep up the good work.",
        'You worked hard yesterday, take it easy today.',
        'You have burned 100 calories so far today!',
    ])
    image = random.choice([
        'https://plus.unsplash.com/premium_photo-1669048780129-051d670fa2d1?q=80&w=3870&auto=format&fit=crop&ixlib=rb-4.0.3&ixid=M3wxMjA3fDB8MHxwaG90by1wYWdlfHx8fGVufDB8fHx8fA%3D%3D',
        None,
    ])
    return {
        'advice_id': 'advice1',
        'timestamp': '2024-01-01 00:00:00',
        'content': advice,
        'image': image,
    }



def fetch_adzuna_jobs():

    APP_ID = os.getenv("ADZUNA_APP_ID")
    API_KEY = os.getenv("ADZUNA_API_KEY")

    url = "https://api.adzuna.com/v1/api/jobs/us/search/1"

    params = {
        "app_id": APP_ID,
        "app_key": API_KEY,
        "results_per_page": 20,
        "what": "Software Engineer" # When user logs in we ask preference and change
    }

    # Timeout prevents the request from hanging forever
    response = requests.get(url, params=params, timeout=30)  

    # Raises error if API request failed
    response.raise_for_status()   

    data = response.json()
    
    return data

def parse_jobs(api_data):
    jobs = []

    for job in api_data.get("results", []):
        description = job.get("description")

        jobs.append({
            "id": str(job.get("id")),
            "company": (job.get("company") or {}).get("display_name"),
            "title": job.get("title"),
            "description": description,
            "skills": extract_skills(description),
            "experience": extract_experience(description),
            "location": (job.get("location") or {}).get("display_name"),
        })

    return jobs

def get_job_count_by_company(company_name: str) -> int:
    """Count the number of open job listings for a given company_name."""
    query = """
        SELECT COUNT(*) AS cnt
        FROM `kenneth-ye-fiu.ISE.JobInformation`
        WHERE LOWER(company_name) = LOWER(@company_name)
    """
    job_config = bigquery.QueryJobConfig(
        query_parameters=[
            bigquery.ScalarQueryParameter("company_name", "STRING", company_name)
        ]
    )
    try:
        result = bq_client.query(query, job_config=job_config).result()
        for row in result:
            return row.cnt
        return 0
    except Exception as e:
        print(f"get_job_count_by_company error: {e}")
        return 0


def search_jobs(keyword: str) -> list[dict]:
    query = """
        SELECT 
            j.job_ID, j.company_name, j.title, j.description,
            j.location, j.job_type, j.salary_min, j.salary_max,
            j.date_posted, j.date_expire,
            ARRAY_AGG(s.skill_name IGNORE NULLS) AS skills
        FROM `kenneth-ye-fiu.ISE.JobInformation` j
        LEFT JOIN `kenneth-ye-fiu.ISE.jobSkillsTable` js ON j.job_ID = js.job_ID
        LEFT JOIN `kenneth-ye-fiu.ISE.skillsTable` s ON js.skill_ID = s.skill_ID
        WHERE LOWER(j.title)       LIKE LOWER(CONCAT('%', @keyword, '%'))
           OR LOWER(j.description) LIKE LOWER(CONCAT('%', @keyword, '%'))
        GROUP BY j.job_ID, j.company_name, j.title, j.description,
                 j.location, j.job_type, j.salary_min, j.salary_max,
                 j.date_posted, j.date_expire
    """
    job_config = bigquery.QueryJobConfig(
        query_parameters=[
            bigquery.ScalarQueryParameter("keyword", "STRING", keyword)
        ]
    )
    try:
        result = bq_client.query(query, job_config=job_config).result()
        return [dict(row) for row in result]
    except Exception as e:
        print(f"search_jobs error: {e}")
        return []


Mock_Jobs = [
    {"id": "google-1",
        "company": "Google",
        "title": "Software Engineer Intern Summer 2026",
        "description": "Work on scalable systems.",
        "skills": ["Python", "Data Structures", "Git","Swift", "Postgres", "Flask"],
        "experience": "Projects / coursework accepted",
        "location" : "Florida"
    },
    {
        "id": "meta-1",
        "company": "Meta",
        "title": "Backend Intern 2026",
        "description": "Build APIs and services.",
        "skills": ["Java", "APIs", "Databases"],
        "experience": "Some backend project experience",
        "location" : "White House"
    },
    {
        "id": "apple-1",
        "company": "Apple",
        "title": "iOS Intern 2026",
        "description": "Help develop iOS features.",
        "skills": ["Swift", "Postgres", "Flask"],
        "experience": "Mobile apps or class projects",
        "location" : "New York"
    }
    ]

def get_jobs():
    return Mock_Jobs


