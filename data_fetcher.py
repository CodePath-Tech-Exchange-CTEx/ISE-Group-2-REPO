#############################################################################
# data_fetcher.py
#
# This file contains functions to fetch data needed for the app.
#
# You will re-write these functions in Unit 3, and are welcome to alter the
# data returned in the meantime. We will replace this file with other data when
# testing earlier units.
#############################################################################
import datetime
import uuid
import random
import requests
from extractor import *
from google.cloud import bigquery

bq_client = bigquery.Client()
from db_handler import insert_jobs_to_bigquery, get_jobs_from_bigquery

from dotenv import load_dotenv
import os

load_dotenv()

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

def fetch_and_save_jobs():
    """
    Orchestrates fetching jobs from Adzuna API, parsing them, and saving to BigQuery.
    This function is intended to be run as a standalone script or a scheduled job.
    """
    try:
        api_data = fetch_adzuna_jobs()
        
        jobs = parse_jobs(api_data)
        
        if not jobs:
            return False

        errors = insert_jobs_to_bigquery(jobs)

        if not errors["job_errors"] and not errors["skill_errors"] and not errors["job_skill_errors"]:
            print("Successfully fetched and saved all job data.")
            return True
        else:
            print("Completed with errors.")

            if errors["job_errors"]:
                print(f"Job insertion errors: {errors['job_errors']}")

            if errors["skill_errors"]:
                print(f"Skill insertion errors: {errors['skill_errors']}")

            if errors["job_skill_errors"]:
                print(f"Job-skill insertion errors: {errors['job_skill_errors']}")

            return False

    except Exception as e:
        print(f"An error occurred during the fetch-and-save process: {e}")
        return False

def parse_jobs(api_data):
    jobs = []

    for job in api_data.get("results", []):
        description = job.get("description") or ""
        
        jobs.append({
            "job_id": str(job.get("id")),
            "company_name": (job.get("company") or {}).get("display_name"),
            "job_title": job.get("title"),
            "job_description": description,
            "job_location": (job.get("location") or {}).get("display_name"),
            "experience_requirements": extract_experience(description),
            "skills": extract_skills(description),
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


def get_jobs():
    return get_jobs_from_bigquery()

def get_chat_context(user_id: str, job_id: str) -> list[dict]:
    """
    Fetches all previous user_prompt and ai_response entries 
    for a given user_ID and job_ID to provide memory to the chatbot.
    """
    query = """
        SELECT user_prompt, ai_response
        FROM `kenneth-ye-fiu.ISE.chatbotTABLE`
        WHERE user_ID = @user_id AND job_ID = @job_id
        ORDER BY session_ID ASC
    """
    job_config = bigquery.QueryJobConfig(
        query_parameters=[
            bigquery.ScalarQueryParameter("user_id", "STRING", user_id),
            bigquery.ScalarQueryParameter("job_id", "STRING", job_id),
        ]
    )
    try:
        result = bq_client.query(query, job_config=job_config).result()
        return [dict(row) for row in result]
    except Exception as e:
        print(f"get_chat_context error: {e}")
        return []

def save_chat_session(user_id: str, resume_id: str, job_id: str, user_prompt: str, ai_response: str):
    """
    Inserts a new chat record into BigQuery. 
    Fulfills the 'get_genai_data' requirement to update the DB using AI output.
    """

    #define the target tbale in project.dataset.table format
    table_id = "kenneth-ye-fiu.ISE.chatbotTABLE"
    
    # Generating a unique ID for the session record
    session_id = str(uuid.uuid4())

    rows_to_insert = [
        {
            "session_ID": session_id,
            "user_prompt": user_prompt,
            "ai_response": ai_response,
            "user_ID": user_id,
            "resume_ID": resume_id,
            "job_ID": job_id
        }
    ]

    try:
        # Use the JSON streaming API to push the data into BigQuery
        errors = bq_client.insert_rows_json(table_id, rows_to_insert)
        if errors == []: #if errors bigQuery returns a list of error objects
            return True
        else:
            print(f"Errors inserting chat session: {errors}")
            return False
    except Exception as e:
        print(f"save_chat_session error: {e}")
        return False

def get_resume_with_skills(resume_id: str) -> dict:
    """
    Fetches the resume details and associated skills for comparison logic.
    Uses a JOIN between Resumes, resumeSkill, and Skills tables.
    """

    #array_agg takes multiple skill rows and turns them into a single list
    
    query = """
        SELECT 
            r.name, r.location, r.university,
            ARRAY_AGG(s.skill_name IGNORE NULLS) AS skills
        FROM `kenneth-ye-fiu.ISE.Resumes` r
        LEFT JOIN `kenneth-ye-fiu.ISE.resumeSkill` rs ON r.resume_ID = rs.resume_ID
        LEFT JOIN `kenneth-ye-fiu.ISE.Skills` s ON rs.skill_ID = s.skill_ID
        WHERE r.resume_ID = @resume_id
        GROUP BY r.name, r.location, r.university
    """
    job_config = bigquery.QueryJobConfig(
        query_parameters=[
            bigquery.ScalarQueryParameter("resume_id", "STRING", resume_id)
        ]
    )
    try:
        result = bq_client.query(query, job_config=job_config).result()
        for row in result:
            return dict(row)
        return {}
    except Exception as e:
        print(f"get_resume_with_skills error: {e}")
        return {}



if __name__ == "__main__":
    # This allows the script to be run directly to populate the database 
    fetch_and_save_jobs()
