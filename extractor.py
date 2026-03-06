# This file handles extracting missing data from the api fetching.
# In this case the Adzuna API doesn't output skills nor experience data.
# Using the description we try to adquire this missing data.

import re

PROGRAMMING_LANGUAGES = [
    "python", "java", "c", "c++", "c#", "javascript", "typescript",
    "go", "rust", "swift", "kotlin", "ruby", "php", "scala", "matlab"
]

WEB_TECH = [
    "html", "css", "react", "angular", "vue", "node", "node.js", "express",
    "django", "flask", "spring", "spring boot", "asp.net"
]

DATABASES = [
    "sql", "mysql", "postgresql", "mongodb", "sqlite", "oracle",
    "redis", "firebase", "dynamodb"
]

CLOUD_DEVOPS = [
    "aws", "azure", "google cloud", "gcp", "docker", "kubernetes",
    "terraform", "jenkins", "ci/cd", "linux", "unix"
]

TOOLS = [
    "git", "github", "gitlab", "bitbucket", "jira", "confluence", "postman"
]

DATA_AI = [
    "pandas", "numpy", "tensorflow", "pytorch", "scikit-learn",
    "machine learning", "deep learning", "data science"
]

SKILLS_LIST = (
    PROGRAMMING_LANGUAGES + WEB_TECH + DATABASES + CLOUD_DEVOPS + TOOLS + DATA_AI
)

# API doesn't give skills we have to get them manually 
def extract_skills(description: str):
    if not description:
        return []
    found_skills = []
    description = description.lower()

    for skill in SKILLS_LIST:
        if skill in description:
            found_skills.append(skill)
    return list(set(found_skills))

def extract_experience(description: str):
    if not description:
        return None

    description = description.lower()
    pattern = r"(\d+(?:-\d+)?\+?\s+years?\s+of\s+experience|\d+(?:-\d+)?\+?\s+years?\s+experience)"
    match = re.search(pattern, description)

    if not match:
        return None
    return match.group()

