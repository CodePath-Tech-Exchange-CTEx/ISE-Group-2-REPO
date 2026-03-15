# File that handles all data base query
import sqlite3
from datetime import datetime
from google.cloud import bigquery

from dotenv import load_dotenv
import os

load_dotenv()


def init_db():
    """
    Initializes the local SQLite database and creates the chat_history table 
    if it does not already exist.
    """
    # Establish connection (creates the file if it doesn't exist)
    conn = sqlite3.connect('internmatch.db') 
    cursor = conn.cursor()

    # Define schema for storing user interactions and LLM context
    cursor.execute('''CREATE TABLE IF NOT EXISTS chat_history (
                        user_id TEXT, 
                        resume_text TEXT, 
                        job_description TEXT, 
                        prompt TEXT, 
                        response TEXT, 
                        timestamp TEXT
                    )''')
    
    conn.commit()
    conn.close()
            
def save_chat_log(user_id, resume, job_desc, prompt, response):
    """
    Persists a single chat interaction to the database with a current timestamp.
    
    Args:
        user_id (str): Unique identifier for the user.
        resume (str): The raw text of the uploaded resume.
        job_desc (str): The target job description.
        prompt (str): The exact prompt sent to the LLM.
        response (str): The AI-generated output.
    """
    try:
        conn = sqlite3.connect('internmatch.db')
        c = conn.cursor()

        # Generate ISO 8601 formatted timestamp for chronological sorting
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        # Use parameterized queries to prevent SQL injection
        c.execute("INSERT INTO chat_history VALUES (?, ?, ?, ?, ?, ?)",
                (user_id, resume, job_desc, prompt, response, timestamp))
        
        conn.commit()
        conn.close()
        print("SQL SUCCESS: Data committed to internmatch.db")
    except Exception as e:
        print(f"SQL ERROR: {e}")


def get_chat_history(user_id):
    # This fulfills  requirement to "read" the saved prompts and history
    conn = sqlite3.connect('internmatch.db')
    c = conn.cursor()
    c.execute("SELECT prompt, response, timestamp FROM chat_history WHERE user_id = ? ORDER BY timestamp DESC", (user_id,))
    rows = c.fetchall()
    conn.close()
    return rows

def insert_jobs_to_bigquery(jobs):
    """
    This function takes a list of job dictionaries, separates them into
    job data and skill data, and inserts them into two separate BigQuery tables.
    """

    PROJECT_ID = os.getenv("PROJECT_ID")
    DATABASE_ID = os.getenv("DATABASE_ID")

    if not PROJECT_ID or not DATABASE_ID:
        print("ERROR: PROJECT_ID and DATABASE_ID environment variables must be set.")
        return (["Configuration error: PROJECT_ID or DATABASE_ID not set."], 
                ["Configuration error: Project or Database ID not set."])

    JOBS_TABLE = f"{PROJECT_ID}.{DATABASE_ID}.jobs"
    SKILLS_TABLE = f"{PROJECT_ID}.{DATABASE_ID}.jobs_skills"

    client = bigquery.Client(project=PROJECT_ID)

    job_rows = []
    skill_rows = []

    if not jobs:
        print("No jobs provided to insert.")
        return ([], [])

    for job in jobs:
        # Basic validation
        if not job.get("job_id"):
            print(f"Skipping job with no ID: {job.get('job_title')}")
            continue

        job_rows.append({
            "job_id": job["job_id"],
            "company_name": job["company_name"],
            "job_title": job["job_title"],
            "job_description": job["job_description"],
            "job_location": job["job_location"],
            "experience_requirements": job["experience_requirements"],
        })

        for skill in job.get("skills", []):
            skill_rows.append({
                "job_id": job["job_id"],
                "skill": skill 
            })

    job_error_handler = []
    if job_rows:
        job_error_handler = client.insert_rows_json(JOBS_TABLE, job_rows)
    
    skill_error_handler = []
    if skill_rows:
        skill_error_handler = client.insert_rows_json(SKILLS_TABLE, skill_rows)

    return job_error_handler, skill_error_handler

def get_jobs_from_bigquery():

    PROJECT_ID = os.getenv("PROJECT_ID")
    DATABASE_ID = os.getenv("DATABASE_ID")

    client = bigquery.Client(project=PROJECT_ID)

    query = f"""
    SELECT j.job_id, j.company_name, j.job_title, j.job_description, j.job_location, j.experience_requirements,
    ARRAY_AGG(DISTINCT s.skill IGNORE NULLS) AS skills
    FROM `{PROJECT_ID}.{DATABASE_ID}.jobs` j
    LEFT JOIN `{PROJECT_ID}.{DATABASE_ID}.jobs_skills` s
    ON j.job_id = s.job_id
    GROUP BY j.job_id, j.company_name, j.job_title, j.job_description, j.job_location, j.experience_requirements
    LIMIT {20}
    """

    query_job = client.query(query)
    results = query_job.result()

    jobs = []
    for row in results:
        jobs.append({
            "id": row.job_id,
            "company": row.company_name,
            "title": row.job_title,
            "description": row.job_description,
            "location": row.job_location,
            "experience": row.experience_requirements,
            "skills": list(row.skills) if row.skills else []
        })
    return jobs
