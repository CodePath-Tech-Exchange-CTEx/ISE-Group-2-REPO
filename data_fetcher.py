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
from extractor import *
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
        job_errors, skill_errors = insert_jobs_to_bigquery(jobs)

        if not job_errors and not skill_errors:
            print("Successfully fetched and saved all job data.")
            return True
        else:
            print("Completed with errors.")

            if job_errors:
                print(f"Job insertion errors: {job_errors}")

            if skill_errors:
                print(f"Skill insertion errors: {skill_errors}")
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


def get_jobs():
    return get_jobs_from_bigquery()


if __name__ == "__main__":
    # This allows the script to be run directly to populate the database 
    fetch_and_save_jobs()
