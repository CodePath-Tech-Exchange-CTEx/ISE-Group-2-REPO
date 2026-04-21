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
from db_handler import insert_jobs_to_bigquery, get_jobs_from_bigquery
from dotenv import load_dotenv
import os
import json


load_dotenv()

bq_client = bigquery.Client()

PROJECT_ID = "oluwanifemi-elias-hu"
DATABASE_ID = "ISE" 


def get_bq_client():
    """
    Initializes the BigQuery client only when needed.
    This prevents 'DefaultCredentialsError' during the import phase in testing environments.
    """
    return bigquery.Client()

# users = {
#     'user1': {
#         'full_name': 'Remi',
#         'username': 'remi_the_rems',
#         'date_of_birth': '1990-01-01',
#         'profile_image': 'https://upload.wikimedia.org/wikipedia/commons/c/c8/Puma_shoes.jpg',
#         'friends': ['user2', 'user3', 'user4'],
#     },
#     'user2': {
#         'full_name': 'Blake',
#         'username': 'blake',
#         'date_of_birth': '1990-01-01',
#         'profile_image': 'https://upload.wikimedia.org/wikipedia/commons/c/c8/Puma_shoes.jpg',
#         'friends': ['user1'],
#     },
#     'user3': {
#         'full_name': 'Jordan',
#         'username': 'jordanjordanjordan',
#         'date_of_birth': '1990-01-01',
#         'profile_image': 'https://upload.wikimedia.org/wikipedia/commons/c/c8/Puma_shoes.jpg',
#         'friends': ['user1', 'user4'],
#     },
#     'user4': {
#         'full_name': 'Gemmy',
#         'username': 'gems',
#         'date_of_birth': '1990-01-01',
#         'profile_image': 'https://upload.wikimedia.org/wikipedia/commons/c/c8/Puma_shoes.jpg',
#         'friends': ['user1', 'user3'],
#     },
# }


# def get_user_posts(user_id):
#     """Returns a list of a user's posts.

#     This function currently returns random data. You will re-write it in Unit 3.
#     """
#     content = random.choice([
#         'Had a great workout today!',
#         'The AI really motivated me to push myself further, I ran 10 miles!',
#     ])
#     return [{
#         'user_id': user_id,
#         'post_id': 'post1',
#         'timestamp': '2024-01-01 00:00:00',
#         'content': content,
#         'image': 'image_url',
#     }]



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
            "job_link": job.get("redirect_url"),
            "experience_requirements": extract_experience(description),
            "skills": extract_skills(description),
        })

    return jobs

def get_job_count_by_company(company_name: str) -> int:
    """Count the number of open job listings for a given company_name."""
    
    query = f"""
        SELECT COUNT(*) AS cnt
        FROM `{PROJECT_ID}.{DATABASE_ID}.JobInformation`
        WHERE LOWER(company_name) = LOWER(@company_name)
    """
    job_config = bigquery.QueryJobConfig(
        query_parameters=[
            bigquery.ScalarQueryParameter("company_name", "STRING", company_name)
        ]
    )
    try:
        # Call the helper function instead of a global variable
        client = get_bq_client()
        result = client.query(query, job_config=job_config).result()
        for row in result:
            return row.cnt
        return 0
    except Exception as e:
        print(f"get_job_count_by_company error: {e}") 
        return 0


def search_jobs(keyword: str) -> list[dict]:
    query = f"""
        SELECT 
            j.job_ID, j.company_name, j.title, j.description,
            j.location, j.job_type, j.salary_min, j.salary_max,
            j.date_posted, j.date_expire,
            ARRAY_AGG(s.skill_name IGNORE NULLS) AS skills
        FROM `{PROJECT_ID}.{DATABASE_ID}.JobInformation` j
        LEFT JOIN `{PROJECT_ID}.{DATABASE_ID}.jobSkillsTable` js ON j.job_ID = js.job_ID
        LEFT JOIN `{PROJECT_ID}.{DATABASE_ID}.skillsTable` s ON js.skill_ID = s.skill_ID
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
        client = get_bq_client()
        result = client.query(query, job_config=job_config).result()
        return [dict(row) for row in result]
    except Exception as e:
        print(f"search_jobs error: {e}")
        return []


def get_jobs():
    return get_jobs_from_bigquery()
     
def get_chat_context(user_id: str, job_id: str) -> list[dict]:
    """
    Retrieves the history of a specific conversation to give the AI 'memory'.
    Filters by user and job so the bot doesn't mix up different applications.
    """
    # SQL Query: Grabs the prompts and responses in chronological order
    query = f"""
        SELECT user_prompt, ai_response
        FROM `{PROJECT_ID}.{DATABASE_ID}.chatbotTABLE`
        WHERE user_ID = @user_id AND job_ID = @job_id
        ORDER BY session_ID ASC
    """
    
    # Parametrization: This prevents 'SQL Injection' by safely passing variables
    job_config = bigquery.QueryJobConfig(
        query_parameters=[
            bigquery.ScalarQueryParameter("user_id", "STRING", user_id),
            bigquery.ScalarQueryParameter("job_id", "STRING", job_id),
        ]
    )
    
    try:
        # Lazy initialization: Client is only created when the function runs
        client = get_bq_client()
        result = client.query(query, job_config=job_config).result()
        
        # Converts BigQuery Row objects into standard Python dictionaries for the app
        return [dict(row) for row in result]
    except Exception as e:
        print(f"get_chat_context error: {e}")
        return []

def save_chat_session(user_id: str, resume_id: str, job_id: str, user_prompt: str, ai_response: str):
    """
    Logs a new chat interaction into the database. 
    This is critical for tracking user engagement and AI accuracy.
    """
    table_id = f"{PROJECT_ID}.{DATABASE_ID}.chatbotTABLE"
    
    # Generate a unique ID for this specific message pair
    session_id = str(uuid.uuid4())

    # Format the data into a list of JSON objects as required by BigQuery streaming
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
        client = get_bq_client()
        # insert_rows_json is a 'Streaming Insert' - it's much faster than a standard SQL INSERT
        errors = client.insert_rows_json(table_id, rows_to_insert)
        
        if errors == []:
            return True # Success
        else:
            # BigQuery returns a list of error objects if something went wrong (e.g., schema mismatch)
            print(f"Errors inserting chat session: {errors}")
            return False
    except Exception as e:
        print(f"save_chat_session error: {e}")
        return False

def get_resume_with_skills(resume_id: str) -> dict:
    """
    Joins multiple tables to get a complete picture of a candidate.
    Combines the 'Resumes' metadata with their list of skills.
    """
    # SQL Query: Uses LEFT JOINs to ensure we get the resume even if skills are missing
    # ARRAY_AGG(s.skill_name) turns multiple skill rows into a single Python list
    query = f"""
        SELECT 
            r.name, r.location, r.university,
            ARRAY_AGG(s.skill_name IGNORE NULLS) AS skills
        FROM `{PROJECT_ID}.{DATABASE_ID}.Resumes` r
        LEFT JOIN `{PROJECT_ID}.{DATABASE_ID}.resumeSkill` rs ON r.resume_ID = rs.resume_ID
        LEFT JOIN `{PROJECT_ID}.{DATABASE_ID}.Skills` s ON rs.skill_ID = s.skill_ID
        WHERE r.resume_ID = @resume_id
        GROUP BY r.name, r.location, r.university
    """
    
    job_config = bigquery.QueryJobConfig(
        query_parameters=[
            bigquery.ScalarQueryParameter("resume_id", "STRING", resume_id)])
    try:

        client = get_bq_client()
        result = client.query(query, job_config=job_config).result()
        
        # result is an iterator; we only expect one resume per ID
        for row in result:
            return dict(row)
        return {} # Return empty dict if ID doesn't exist
    except Exception as e:
        print(f"get_resume_with_skills error: {e}")
        return {}

def get_user_profile(user_id: str) -> list:

    # # Use Kenneth dataset until femi's gets set up
    # PROJECT_ID = "kenneth-ye-fiu"
    # DATABASE_ID = "ISE"

    # Check for database validity
    if not PROJECT_ID or not DATABASE_ID:
        print("Error running query, DATABASE_ID not valid or not configured, or PROJECT_ID is incorrect")
        return None

    client = bigquery.Client(project=PROJECT_ID)

    query = f"""
        SELECT
        u.email,
        u.first_name,
        u.last_name,
        u.date_created,
        u.is_verified
        FROM `{PROJECT_ID}.{DATABASE_ID}.User` u
        WHERE
        u.user_ID = '{user_id}'
        """

    query_job = client.query(query)
    results = query_job.result()

    user = {}
    row = next(results, None)
    if row:
        user = {
            "email": row.email,
            "first_name": row.first_name,
            "last_name": row.last_name,
            "date_created": row.date_created,
            "is_verified": row.is_verified
        }
    return user

def get_user_resume(user_id: str) -> dict:

    # # Use Kenneth dataset until femi's gets set up
    # PROJECT_ID = "kenneth-ye-fiu"
    # DATABASE_ID = "ISE"

    # Check for database validity
    if not PROJECT_ID or not DATABASE_ID:
        print("Error running query, DATABASE_ID not valid or not configured, or PROJECT_ID is incorrect")
        return None

    client = bigquery.Client(project=PROJECT_ID)

    query = f"""
        SELECT
        r.resume_ID,
        r.user_ID,
        STRING_AGG(CONCAT(u.first_name, ' ', u.last_name)) AS Name,
        STRING_AGG(r.name) AS FILENAME,
        r.location,
        r.university
        FROM
        `{PROJECT_ID}.{DATABASE_ID}.resumesTable` AS r
        JOIN
        `{PROJECT_ID}.{DATABASE_ID}.User` AS u
        ON r.user_ID = u.user_ID
        WHERE
        r.user_ID = '{user_id}'
        GROUP BY
        r.resume_ID,
        r.name,
        r.user_ID,
        r.location,
        r.university
        ORDER BY
        r.user_ID
        """
    
    resume = {}

    query_job = client.query(query)
    results = query_job.result()

    for row in results:
        resume[f"{row.resume_ID}"] = {"Name": row.Name, "user_ID": row.user_ID, "FILENAME": row.FILENAME, "location": row.location, "university": row.university}
    return resume


def filter_jobs_by_job_type(job_type):
    query = f"""
        SELECT *
        FROM `{PROJECT_ID}.{DATABASE_ID}.JobInformation`
        WHERE
        job_type = @job_type  
    """
    job_config = bigquery.QueryJobConfig(
        query_parameters=[
            bigquery.ScalarQueryParameter("job_type", "STRING", job_type)
        ]
    )
    try:
        query_job = bq_client.query(query, job_config=job_config)
        return [dict(row) for row in query_job.result()]

    except Exception as e:
        print(f"filter_jobs_by_job_type error: {e}")
        return []

        
def filter_jobs_by_location(location):
    query = f"""
        SELECT *
        FROM `{PROJECT_ID}.{DATABASE_ID}.JobInformation`
        WHERE
        location = @location  
    """
    job_config = bigquery.QueryJobConfig(
        query_parameters=[
            bigquery.ScalarQueryParameter("location", "STRING", location)
        ]
    )
    try:
        query_job = bq_client.query(query, job_config=job_config)
        return [dict(row) for row in query_job.result()]

    except Exception as e:
        print(f"filter_jobs_by_location error: {e}")
        return []


def filter_jobs_by_skill_name(skill_name):
    query = f"""
        SELECT t1.*
        FROM `{PROJECT_ID}.{DATABASE_ID}.JobInformation` AS t1
        INNER JOIN `{PROJECT_ID}.{DATABASE_ID}.jobSkillsTable` AS t2
        ON t1.job_ID = t2.job_ID
        INNER JOIN `{PROJECT_ID}.{DATABASE_ID}.skillsTable` AS t3
        ON t2.skill_ID = t3.skill_ID
        WHERE t3.skill_name = @skill_name
    """
    job_config = bigquery.QueryJobConfig(
        query_parameters=[
            bigquery.ScalarQueryParameter("skill_name", "STRING", skill_name)
        ]
    )
    try:
        query_job = bq_client.query(query, job_config=job_config)
        return [dict(row) for row in query_job.result()]

    except Exception as e:
        print(f"filter_jobs_by_skill_name error: {e}")
        return []

def get_resume_skills(resume_id):
    query = f"""
        SELECT t1.resume_ID, t3.skill_name
        FROM `{PROJECT_ID}.{DATABASE_ID}.resumesTable` AS t1
        INNER JOIN `{PROJECT_ID}.{DATABASE_ID}.resumeSkill` AS t2
            ON t1.resume_ID = t2.resume_ID
        INNER JOIN `{PROJECT_ID}.{DATABASE_ID}.skillsTable` AS t3
            ON t2.skill_ID = t3.skill_ID
        WHERE t1.resume_ID = @resume_id
    """

    job_config = bigquery.QueryJobConfig(
        query_parameters=[
            bigquery.ScalarQueryParameter("resume_id", "STRING", resume_id) 
        ]
    )
    try:
        query_job = bq_client.query(query, job_config=job_config)
        return [dict(row) for row in query_job.result()]
    except Exception as e:
        print(f"get_resume_skills error: {e}")
        return []

def get_job_skills(job_id):
    query = f"""
        SELECT t1.job_ID, t3.skill_name
        FROM `{PROJECT_ID}.{DATABASE_ID}.JobInformation` AS t1
        INNER JOIN `{PROJECT_ID}.{DATABASE_ID}.jobSkillsTable` AS t2
            ON t1.job_ID = t2.job_ID
        INNER JOIN `{PROJECT_ID}.{DATABASE_ID}.skillsTable` AS t3
            ON t2.skill_ID = t3.skill_ID
        WHERE t1.job_ID = @job_id
    """
    job_config = bigquery.QueryJobConfig(
        query_parameters=[
            bigquery.ScalarQueryParameter("job_id", "STRING", job_id) 
        ]
    )
    
    try:
        query_job = bq_client.query(query, job_config=job_config)
        return [dict(row) for row in query_job.result()]
    except Exception as e:
        print(f"get_resume_skills error: {e}")
        return []

    

def get_project_with_skills(resume_id):
    query = f"""
        SELECT DISTINCT 
            t1.project_title, 
            t1.project_start_date, 
            t3.skill_name
        FROM `{PROJECT_ID}.{DATABASE_ID}.project_info` AS t1
        INNER JOIN `{PROJECT_ID}.{DATABASE_ID}.projectSkillsTable` AS t2 
            ON t1.project_ID = t2.project_ID
        INNER JOIN `{PROJECT_ID}.{DATABASE_ID}.skillsTable` AS t3
            ON t2.skill_ID = t3.skill_ID
        WHERE t1.resume_ID = @resume_id
        ORDER BY t1.project_start_date DESC;
    """
    
    job_config = bigquery.QueryJobConfig(
        query_parameters=[
            bigquery.ScalarQueryParameter("resume_id", "STRING", str(resume_id))
        ]
    )

    try:
        query_job = bq_client.query(query, job_config=job_config)
        return [dict(row) for row in query_job.result()]
        
    except Exception as e:
        print(f"Error fetching project skills: {e}")
        return []


def get_match_score(resume_id, job_id):
    onlyResumeSkills = set([item['skill_name'] for item in get_resume_skills(resume_id)])
    onlyJobSkills = set([item['skill_name'] for item in get_job_skills(job_id)])

    commonSkills = onlyResumeSkills.intersection(onlyJobSkills)

    if not onlyJobSkills: 
        return 0.0, commonSkills # Return 0 if there are no job skills to match against
        
    matchScore = (len(commonSkills) / len(onlyJobSkills)) * 100
    return matchScore, commonSkills

# processing new resumes
def get_next_id(table_id, id_column, prefix="", padding=3):
    """ Fetches the max ID from a table and increments it. """
    query = f"SELECT MAX({id_column}) as max_id FROM `{table_id}`"
    try:
        results = bq_client.query(query).result()
        row = next(results, None)
        
        if row and row.max_id:
            # Extract only the digits (e.g., 'RSK012' -> 12)
            match = re.search(r'\d+', str(row.max_id))
            num = int(match.group()) + 1 if match else 1
        else:
            num = 1
            
        # If padding is 0, just returns the string number (e.g., '105')
        if padding == 0:
            return str(num)
        return f"{prefix}{str(num).zfill(padding)}"
    except Exception as e:
        print(f"ID Generation Error: {e}")
        return "1"

import json
from vertexai.generative_models import GenerativeModel, GenerationConfig

def ai_extract_resume_data(pdf_text):
    model = GenerativeModel("gemini-2.5-flash-lite")
    
    prompt = f"""
    Extract the following information from this resume text:
    1. Full Name
    2. Location (City, State)
    3. University Name
    4. A list of technical skills (e.g., Python, SQL)
    
    Return the result EXACTLY in this JSON format:
    {{
        "name": "string",
        "location": "string",
        "university": "string",
        "skills": ["skill1", "skill2"]
    }}
    
    Resume Text:
    {pdf_text}
    """
    
    response = model.generate_content(
        prompt,
        generation_config=GenerationConfig(response_mime_type="application/json", max_output_tokens=1000, temperature=0.1)
    )
    return json.loads(response.text)

def sync_skill_to_db(skill_name):
    """ Checks if a skill exists (case-insensitive) and returns its ID. """
    check_query = f"""
        SELECT skill_ID FROM `{PROJECT_ID}.{DATABASE_ID}.skillsTable` 
        WHERE LOWER(skill_name) = LOWER(@name)
    """
    params = [bigquery.ScalarQueryParameter("name", "STRING", skill_name)]
    results = bq_client.query(check_query, job_config=bigquery.QueryJobConfig(query_parameters=params)).result()
    
    existing = next(results, None)
    if existing:
        return existing.skill_ID
    
    # Otherwise, create the new skill
    new_id = get_next_id(f"{PROJECT_ID}.{DATABASE_ID}.skillsTable", "skill_ID", prefix="SK", padding=3)
    insert_query = f"""
        INSERT INTO `{PROJECT_ID}.{DATABASE_ID}.skillsTable` (skill_ID, skill_name)
        VALUES (@id, @name)
    """
    insert_params = [
        bigquery.ScalarQueryParameter("id", "STRING", new_id),
        bigquery.ScalarQueryParameter("name", "STRING", skill_name),
    ]
    bq_client.query(insert_query, job_config=bigquery.QueryJobConfig(query_parameters=insert_params)).result()
    return new_id

def save_resume_pipeline(raw_text):
    # Parse
    extracted = ai_extract_resume_data(raw_text)
    
    # 2. Get New IDs for User and Resume
    new_res_id = get_next_id(f"{PROJECT_ID}.{DATABASE_ID}.resumesTable", "resume_ID", padding=0)
    new_user_id = get_next_id(f"{PROJECT_ID}.{DATABASE_ID}.resumesTable", "user_ID", padding=0)
    
    # 3. Insert into resumesTable
    resume_sql = f"""
    INSERT INTO `{PROJECT_ID}.{DATABASE_ID}.resumesTable` 
    (resume_ID, user_ID, name, location, university)
    VALUES (@rid, @uid, @name, @loc, @univ)
    """
    res_params = [
        bigquery.ScalarQueryParameter("rid", "STRING", new_res_id),
        bigquery.ScalarQueryParameter("uid", "STRING", new_user_id),
        bigquery.ScalarQueryParameter("name", "STRING", extracted['name']),
        bigquery.ScalarQueryParameter("loc", "STRING", extracted['location']),
        bigquery.ScalarQueryParameter("univ", "STRING", extracted['university']),
    ]
    bq_client.query(resume_sql, job_config=bigquery.QueryJobConfig(query_parameters=res_params)).result()

    # 4. Link every skill found by the AI
    for s_name in extracted['skills']:
        skill_id = sync_skill_to_db(s_name)
        
        # Create unique link ID (RSK...)
        rsk_id = get_next_id(f"{PROJECT_ID}.{DATABASE_ID}.resumeSkill", "resume_Skill_ID", prefix="RSK", padding=3)
        
        link_sql = f"""
        INSERT INTO `{PROJECT_ID}.{DATABASE_ID}.resumeSkill` 
        (resume_Skill_ID, resume_ID, skill_ID)
        VALUES (@rskid, @rid, @sid)
        """
        link_params = [
            bigquery.ScalarQueryParameter("rskid", "STRING", rsk_id),
            bigquery.ScalarQueryParameter("rid", "STRING", new_res_id),
            bigquery.ScalarQueryParameter("sid", "STRING", skill_id),
        ]
        bq_client.query(link_sql, job_config=bigquery.QueryJobConfig(query_parameters=link_params)).result()

    return new_res_id # Return this so your app can show the newly created resume

def delete_saved_job(user_id, job_id):
    """
    Removes a saved job from the database.
    Returns True if successful, False otherwise.
    """
    try:
       # Your specific table reference
        table_ref = f"{PROJECT_ID}.{DATABASE_ID}.Favorites"

        # The parameter-safe DELETE query
        query = f"""
            DELETE FROM `{table_ref}`
            WHERE UserId = @user_id 
              AND JobId = @job_id
        """

        # Configure the parameters to safely pass the IDs
        job_config = bigquery.QueryJobConfig(
            query_parameters=[
                bigquery.ScalarQueryParameter("user_id", "STRING", str(user_id)),
                bigquery.ScalarQueryParameter("job_id", "STRING", str(job_id)),
            ]
        )

        # Execute the query
        bq_client.query(query, job_config=job_config).result()

        
        print(f"DEBUG: Successfully deleted job {job_id} for user {user_id} from DB.")
        return True 
        
    except Exception as e:
        print(f"Database Error: {e}")
        return False

def add_saved_job(user_id, job_id):
    """
    Inserts a new saved job record into the BigQuery 'favorites' table 
    using the get_next_id helper function.
    Returns True if successful, False if it fails.
    """
    try:
        table_ref = f"{PROJECT_ID}.{DATABASE_ID}.Favorites"

        check_query = f"""
            SELECT FavoriteId 
            FROM `{table_ref}` 
            WHERE UserId = @user_id AND JobId = @job_id
            LIMIT 1
        """
        check_config = bigquery.QueryJobConfig(
            query_parameters=[
                bigquery.ScalarQueryParameter("user_id", "STRING", str(user_id)),
                bigquery.ScalarQueryParameter("job_id", "STRING", str(job_id)),
            ]
        )
        
        # Run the check
        existing_records = list(bq_client.query(check_query, job_config=check_config).result())
        
        # If the list is not empty, they already saved it! Stop the function.
        if len(existing_records) > 0:
            print(f"DEBUG: UserId {user_id} already saved JobId {job_id}. Skipping insert.")
            return False

        # 1. Fetch the next ID cleanly using your helper function
        favorite_id = get_next_id(table_ref, "FavoriteId", prefix="fav", padding=3)

        # 2. Write the parameterized SQL query
        insert_query = f"""
            INSERT INTO `{table_ref}` (FavoriteId, JobId, UserId)
            VALUES (@favorite_id, @job_id, @user_id)
        """

        # 3. Configure the parameters
        insert_config = bigquery.QueryJobConfig(
            query_parameters=[
                bigquery.ScalarQueryParameter("favorite_id", "STRING", favorite_id),
                bigquery.ScalarQueryParameter("job_id", "STRING", str(job_id)),
                bigquery.ScalarQueryParameter("user_id", "STRING", str(user_id)),
            ]
        )

        # 4. Execute the query
        query_job = bq_client.query(insert_query, job_config=insert_config)
        query_job.result()  
        
        print(f"DEBUG: Successfully added JobId {job_id} for UserId {user_id} with ID {favorite_id}.")
        return True

    except Exception as e:
        print(f"BigQuery Insert Error: {e}")
        return False

def get_user_saved_jobs(user_id):
    """
    Fetches the saved jobs for a specific user from BigQuery and 
    merges them with the full job details.
    """
    try:
        # 1. Initialize client and table reference
        client = bigquery.Client(project = PROJECT_ID)
        table_ref = f"{PROJECT_ID}.{DATABASE_ID}.Favorites" # Update dataset name

        # 2. Query BigQuery for this user's saved JobIds
        query = f"""
            SELECT JobId 
            FROM `{table_ref}`
            WHERE UserId = @user_id
        """
        
        job_config = bigquery.QueryJobConfig(
            query_parameters=[
                bigquery.ScalarQueryParameter("user_id", "STRING", str(user_id)),
            ]
        )

        results = client.query(query, job_config=job_config).result()
        
        # Extract just the IDs into a simple Python list
        saved_job_ids = [str(row.JobId) for row in results]

        # If they have no saved jobs, exit early
        if not saved_job_ids:
            return []

        # 3. Get all jobs and filter for the saved ones
        all_jobs = get_jobs() 
        final_saved_jobs = []

        for job in all_jobs:
            if str(job.get("id")) in saved_job_ids:
                # Map the data to exactly match what your UI expects
                final_saved_jobs.append({
                    "id": job.get("id"),
                    "company": job.get("company", "Unknown Company"),
                    "position": job.get("title", "Unknown Position"), 
                    "deadline": job.get("date_expire", "TBD") # Ensure your get_jobs returns a deadline
                })

        return final_saved_jobs

    except Exception as e:
        print(f"Error fetching saved jobs from BigQuery: {e}")
        return []

if __name__ == "__main__":
    fetch_and_save_jobs()
    
   
  
