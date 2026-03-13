# File that handles all data base query
import sqlite3
from datetime import datetime


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

def save_to_jobs_db():
    pass

