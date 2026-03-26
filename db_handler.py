from google.cloud import bigquery

from dotenv import load_dotenv
import os

load_dotenv()
PROJECT_ID = "oluwanifemi-elias-hu"
DATABASE_ID = "ISE"


def insert_jobs_to_bigquery(jobs):
    """
    This function takes a list of job dictionaries, separates them into
    job data and skill data, and inserts them into two separate BigQuery tables.
    """

    if not PROJECT_ID or not DATABASE_ID:
        print("ERROR: PROJECT_ID and DATABASE_ID environment variables must be set.")
        return (["Configuration error: PROJECT_ID or DATABASE_ID not set."], 
                ["Configuration error: Project or Database ID not set."])

    JOBS_TABLE = f"{PROJECT_ID}.{DATABASE_ID}.JobInformation"
    SKILLS_TABLE = f"{PROJECT_ID}.{DATABASE_ID}.skillsTable"
    JOB_SKILLS_TABLE = f"{PROJECT_ID}.{DATABASE_ID}.jobSkillsTable"

    client = bigquery.Client(project=PROJECT_ID)

    job_rows = []
    skill_rows = []
    job_skill_rows = []

    seen_skills = set()
    seen_job_skill_pairs = set()

    if not jobs:
        print("No jobs provided to insert.")
        return {
            "job_errors": [],
            "skill_errors": [],
            "job_skill_errors": []
        }

    for job in jobs:
        # Basic validation
        if not job.get("job_id"):
            continue

        job_id = str(job["job_id"])

        job_rows.append({
            "job_ID": job_id,
            "company_name": job["company_name"],
            "title": job["job_title"],
            "description": job["job_description"],
            "location": job["job_location"],
        })

        for skill in job.get("skills", []):
            if not skill:
                continue

            skill_name = skill.strip().lower()
            skill_id = skill_name.replace(' ', "_")

            if skill_id not in seen_skills:
                skill_rows.append({
                    "skill_ID":skill_id,
                    "skill_name": skill_name
                })
                seen_skills.add(skill_id)

            pair = (job_id, skill_id)
            if pair not in seen_job_skill_pairs:
                job_skill_rows.append({
                    "job_skill_ID": f"{job_id}_{skill_id}",
                    "job_ID": job_id,
                    "skill_ID": skill_id
                })
                seen_job_skill_pairs.add(pair)
            

    job_errors = []
    if job_rows:
        job_errors = client.insert_rows_json(JOBS_TABLE, job_rows)

    skill_errors = []
    if skill_rows:
        skill_errors = client.insert_rows_json(SKILLS_TABLE, skill_rows)

    job_skill_errors = []
    if job_skill_rows:
        job_skill_errors = client.insert_rows_json(JOB_SKILLS_TABLE, job_skill_rows)

    return {
        "job_errors": job_errors,
        "skill_errors": skill_errors,
        "job_skill_errors": job_skill_errors
    }

def get_jobs_from_bigquery():

    PROJECT_ID = os.getenv("PROJECT_ID")
    DATABASE_ID = os.getenv("DATABASE_ID")
    
    if not PROJECT_ID or not DATABASE_ID:
        print("WARNING: BigQuery is not configured. Returning empty jobs list.")
        return []

    try:
        client = bigquery.Client(project=PROJECT_ID)
    
        query = f"""
        SELECT 
        j.job_ID, 
        j.company_name, 
        j.title, 
        j.description, 
        j.location, 
        ARRAY_AGG(DISTINCT s.skill_name IGNORE NULLS) AS skills
        FROM `{PROJECT_ID}.{DATABASE_ID}.JobInformation` j
        LEFT JOIN `{PROJECT_ID}.{DATABASE_ID}.jobSkillsTable` js
        ON j.job_ID = js.job_ID
        LEFT JOIN `{PROJECT_ID}.{DATABASE_ID}.skillsTable` s
        ON s.skill_ID = js.skill_ID
        GROUP BY 
        j.job_id, 
        j.company_name, 
        j.title, 
        j.description, 
        j.location
        LIMIT 20
        """
    
        query_job = client.query(query)
        results = query_job.result()
    
        jobs = []
        for row in results:
            jobs.append({
                "id": row.job_ID,
                "company": row.company_name,
                "title": row.title,
                "description": row.description,
                "location": row.location,
                "skills": list(row.skills) if row.skills else []
            })
        return jobs

    except Exception as e:
        print(f"Error fetching jobs from BigQuery: {e}")
        return []