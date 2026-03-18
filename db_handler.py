import sqlite3
from datetime import datetime

def init_db():
    """
    Initializes the database and creates the chatbotTable according to the ER diagram.
    """
    conn = sqlite3.connect('internmatch.db') 
    cursor = conn.cursor()

    # Enable foreign key support in SQLite
    cursor.execute("PRAGMA foreign_keys = ON;")

    # Updated to match the "chatbotTable" in the image
    # Note: PK (session_ID) should be auto-incrementing for ease of use
    cursor.execute('''CREATE TABLE IF NOT EXISTS chatbotTable (
                        session_ID INTEGER PRIMARY KEY AUTOINCREMENT, 
                        user_prompt TEXT, 
                        ai_response TEXT, 
                        user_ID TEXT, 
                        resume_ID TEXT, 
                        job_ID TEXT,
                        timestamp TEXT,
                        FOREIGN KEY (user_ID) REFERENCES Users(user_ID),
                        FOREIGN KEY (resume_ID) REFERENCES Resumes(resume_ID),
                        FOREIGN KEY (job_ID) REFERENCES JobInformation(job_ID)
                    )''')
    
    conn.commit()
    conn.close()
    print("Database initialized with chatbotTable.")

def save_chat_log(user_id, resume_id, job_id, prompt, response):
    """
    Persists a chat interaction using the foreign keys from the diagram.
    
    Args:
        user_id (str): FK to Users table
        resume_id (str): FK to Resumes table
        job_id (str): FK to JobInformation table
        prompt (str): The user's input
        response (str): The AI's output
    """
    try:
        conn = sqlite3.connect('internmatch.db')
        c = conn.cursor()

        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        # Column names updated to: user_prompt, ai_response, user_ID, resume_ID, job_ID
        query = """INSERT INTO chatbotTable 
                   (user_prompt, ai_response, user_ID, resume_ID, job_ID, timestamp) 
                   VALUES (?, ?, ?, ?, ?, ?)"""
        
        c.execute(query, (prompt, response, user_id, resume_id, job_id, timestamp))
        
        conn.commit()
        conn.close()
        print("SQL SUCCESS: Data committed to chatbotTable.")
    except Exception as e:
        print(f"SQL ERROR: {e}")

def get_chat_history(user_id):
    """
    Retrieves history for a specific user.
    """
    conn = sqlite3.connect('internmatch.db')
    c = conn.cursor()
    # Updated query to use user_prompt and ai_response
    c.execute("""SELECT user_prompt, ai_response, timestamp 
                 FROM chatbotTable 
                 WHERE user_ID = ? 
                 ORDER BY timestamp DESC""", (user_id,))
    rows = c.fetchall()
    conn.close()
    return rows

def save_to_jobs_db():
    pass

