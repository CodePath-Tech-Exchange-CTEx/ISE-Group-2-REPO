#############################################################################
# modules.py
#
# This file contains modules that may be used throughout the app.
#
# You will write these in Unit 2. Do not change the names or inputs of any
# function other than the example.
#############################################################################

from internals import create_component
import streamlit as st
import streamlit.components.v1 as components
import vertexai
from vertexai.generative_models import GenerativeModel
from data_fetcher import get_resume_with_skills, save_chat_session, get_chat_context, get_user_profile, get_user_resume, get_match_score, save_resume_pipeline, delete_saved_job, add_saved_job, get_user_saved_jobs
from db_handler import insert_application_to_bigquery, update_application_status_in_bigquery, delete_application_from_bigquery, fetch_applications_from_bigquery
import pdfplumber
import datetime
import uuid

PROJECT_ID = "oluwanifemi-elias-hu"   #TODO: Check if team can utilize the api with it being under my project
LOCATION = "us-central1"

# do not use global initialization, move them into a helper
def get_gemini_model():
    """
    Initializes the Vertex AI environment using the project-specific 
    credentials and returns a GenerativeModel instance. 
    Using a helper ensures we don't hit initialization errors on app reload.
    """
    vertexai.init(project=PROJECT_ID, location=LOCATION)
    # Using Gemini 1.5 Pro for its high reasoning capabilities and large context window,
    # which is ideal for comparing long resumes against detailed job descriptions.
    return GenerativeModel("gemini-2.5-pro")


# This one has been written for you as an example. You may change it as wanted.
def display_my_custom_component(value):
    """Displays a 'my custom component' which showcases an example of how custom
    components work.

    value: the name you'd like to be called by within the app
    """
    # Define any templated data from your HTML file. The contents of
    # 'value' will be inserted to the templated HTML file wherever '{{NAME}}'
    # occurs. You can add as many variables as you want.
    data = {
        'NAME': value,
    }
    # Register and display the component by providing the data and name
    # of the HTML file. HTML must be placed inside the "custom_components" folder.
    html_file_name = "my_custom_component"
    create_component(data, html_file_name)


########## code change ##########
def NavBar():
    st.markdown("""
    <style>

    /*Button styling*/
    .st-key-nav_container .st-key-nav_home_btn button,
    .st-key-nav_container .st-key-nav_profile_btn button,
    .st-key-nav_container .st-key-nav_settings_btn button 
    .st-key-nav_container .st-key-nav_tracker_btn button {
        background: inherit !important;
        font-size: 24px !important;
        color: gray !important;
        display: flex;
        text-align: center;
    }

    /*Button text styling*/
    .st-key-nav_container .st-key-nav_home_btn button p,
    .st-key-nav_container .st-key-nav_profile_btn button p,
    .st-key-nav_container .st-key-nav_settings_btn button p,
    .st-key-nav_container .st-key-nav_tracker_btn button p{
        font-size: 30px !important;
        color: gray !important;
    }

    /*NavBar */
    .st-key-nav_container {
        display: flex;
        padding-top: 12px;
        padding-bottom: 12px;
        align-items: center;
        justify-content: center;
        position: fixed;
        bottom: 0;
        left: 0;
        right: 0;
        width: 100%;
        background: #ffffff;
        box-shadow: 0px -3px 25px 2px rgba(0, 0, 0, 0.3);
    }

    .st-key-nav_container .stVerticalBlock {
        display: flex;
        justify-content: space-around;
    }

    </style>
    """, unsafe_allow_html=True)
    

    container = st.container(key="nav_container")

    with container:
        col2, col3, col4 = st.columns([1, 1, 1], vertical_alignment="center", gap="small")

        # with col1:
        #     st.button("⚙️", key="nav_settings_btn")

        with col2:
            if st.button("🏠", key="nav_home_btn"):
                st.session_state.page = "home"
                st.rerun()
        with col3: 
            if st.button("👤", key="nav_profile_btn"):
                st.session_state.page = "profile"
                st.rerun()
        with col4: 
            if st.button("📋", key="nav_tracker_btn"): # Using a chart icon for the tracker
                st.session_state.page = "tracker"
                st.rerun()


def GeminiChatbot(container):
    ############
    # Main AI logic. It combines BigQuery metadata, extracted Resume text, and 
    # the current job description to provide tailored advice
    ################
    st.markdown(
        """
        <style>
        /* Expander as a "pop-up" drawer */
        div[data-testid="stExpander"] {
            border: 2px solid black !important;
            border-radius: 30px; 
            width: 60%;
            background-color: white !important;
        }

        /* Force chat text to be black for readability */
        [data-testid="stChatMessage"] div, 
        [data-testid="stChatMessage"] p, 
        [data-testid="stChatMessage"] li {
            color: black !important;
        }

        /* Assistant bubble styling */
        [data-testid="stChatMessage"][data-testid="assistant"] {
            background-color: #f0f2f6 !important;
            border: 1px solid #ddd;
        }
        
        /* User bubble styling */
        [data-testid="stChatMessage"][data-testid="user"] {
            background-color: #e1f5fe !important;
            border: 1px solid #b3e5fc;
        }

        .stChatInput {
            border: 1px solid black !important;
            border-radius: 30px;
        }
        </style>
        """,
        unsafe_allow_html=True
    )

    with container:
        st.markdown('<div id="chatbot-section-wrapper">', unsafe_allow_html=True)
        
        with st.expander("🔎 Ask AI Assistant", expanded=False):
            
            # 1. IDENTIFY CONTEXT
            # Pull IDs from session state (defaults provided if keys don't exist yet)
            user_id = st.session_state.get('user_id', 'user1')
            resume_id = st.session_state.get('current_resume_id', 'res01')
            job_id = st.session_state.get('current_job_id', 'job01')

            # Initialize local UI chat history so messages persist during the session
            if "messages" not in st.session_state:
                st.session_state.messages = []

            # Render existing messages from the current session
            for message in st.session_state.messages:
                with st.chat_message(message["role"]):
                    st.markdown(message["content"])

            # 2. HANDLE NEW USER INPUT
            if prompt := st.chat_input("Ask how to improve your resume..."):
                # Display user message immediately
                with st.chat_message("user"):
                    st.markdown(prompt)
                st.session_state.messages.append({"role": "user", "content": prompt})

                try:
                    # 3. FETCH BIGQUERY DATA FOR AI CONTEXT
                    # Call the function from data_fetcher.py to get real DB data
                    resume_data = get_resume_with_skills(resume_id)
                    
                    # Convert the list of skills from BigQuery into a readable string
                    skills_list = ", ".join(resume_data.get('skills', [])) if resume_data.get('skills') else "No skills listed."
                    
                    # Get unstructured text extracted from the file (PDF)
                    full_resume_text = st.session_state.get('user_resume', 'No full resume text uploaded.')
                    
                    # Get the job description from Adzuna carousel
                    job_desc = st.session_state.get('current_job_desc', 'General career advice context.')
                    
                    with st.chat_message("assistant"):
                        with st.spinner("Analyzing with Vertex AI..."):

                            # Call function instead of using global method only access when needed
                            model = get_gemini_model()
                            
                            # 4. PROMPT ENGINEERING (Semantic Comparison)
                            # We feed all three parts: Profile Metadata, Full Resume, and Job Description.
                            # The structured 'CANDIDATE PROFILE' helps Gemini identify core strengths,
                            # while the 'FULL RESUME TEXT' allows it to see details like work dates and projects.
                            full_prompt = (
                                f"You are a professional career advisor and a friendly helpful hand in suggesting ways to improve skills, experiences, projects, etc.\n\n"
                                f"CANDIDATE PROFILE:\n- Name: {resume_data.get('name', 'Applicant')}\n- Skills: {skills_list}\n\n"
                                f"FULL RESUME TEXT:\n{full_resume_text}\n\n"
                                f"TARGET JOB DESCRIPTION:\n{job_desc}\n\n"
                                f"USER QUESTION: {prompt}\n\n"
                                f"INSTRUCTIONS: If the user asks for help with their resume Compare the resume against the job description. "
                                f"Answer the users questions, Identify gaps between resume and job description, highlight matching skills, and give specific suggestions depending on what the user asks for."
                            )

                            # 5. VERTEX AI GENERATION
                            # We use 'model' defined at the top of modules.py via vertexai.init.
                            # The response is generated based on the grounded data provided in the prompt.
                            response = model.generate_content(full_prompt)
                            ai_response = response.text
                            
                            # Display AI response in the UI
                            st.markdown(ai_response)
                    
                    # 6. SAVE INTERACTION BACK TO BIGQUERY
                    # This closes the loop: Data -> AI -> Data Storage.
                    # We log the user's specific prompt and the AI's tailored response for future context retrieval.
                    save_chat_session(
                        user_id=user_id,
                        resume_id=resume_id,
                        job_id=job_id,
                        user_prompt=prompt,
                        ai_response=ai_response
                    )

                    # Update local session state so the message stays on screen after rerun
                    st.session_state.messages.append({"role": "assistant", "content": ai_response})
                
                except Exception as e:
                    # Catch authentication or API quota errors and display them safely to the user
                    st.error(f"AI error occurred: {e}")
                    print(f"DEBUG ERROR: {str(e)}")

        st.markdown('</div>', unsafe_allow_html=True)



#MODULE 4 User Button + Search Bar:
def CompanySearch(container):
    
    # Keeping the border style for the search bar
    st.markdown("""
        <style>
            .stTextInput > div > div {
                border: 2px solid black !important;
                border-radius: 30px !important;
            }
            /* Styling the user button to be circular */
            .user-btn {
                display: flex;
                align-items: center;
                justify-content: center;
                height: 45px;
                width: 45px;
                border: 2px solid black;
                border-radius: 50%;
                font-size: 20px;
                cursor: pointer;
                background-color: white;
            }
        </style>
    """, unsafe_allow_html=True)

    with container:
        # Create two columns: 1 for the icon, 1 for the search 
        col_icon, col_search = st.columns([1, 10])
        
        with col_icon:
            ########## code change ##########
            # Replace the static div with a real button
            if st.button("👤", key="user_profile_btn"):
                st.session_state.page = "profile"
                st.rerun()
            #################################
            
        with col_search:
            # Search bar stays here
            company_name = st.text_input(
                "Search", 
                placeholder="🔎 | Search company...", 
                label_visibility="collapsed",
                key="search_with_user_icon"
            )

        # This part makes "Enter" feel real:
        if company_name:
            st.info(f"Searching for:  {company_name}")
    return company_name


def ProfilePage(container):
    # CSS for centered elements and labels
    st.markdown("""
        <style>
            .resume-section {
                padding: 20px;
                margin-top: 10px;
                text-align: center;
            }

            .upload-label {
                color: black;
                font-weight: bold;
                margin-bottom: 5px;
                display: block;
                text-align: center;
            }

            .st-key-profile_container span{
                color: black;
            
            }


        </style>
    """, unsafe_allow_html=True)

    user_info = get_user_profile(1)

    container = st.container(key="profile_container")

    with container:
        st.title("User Profile")
        
        # User Info Section
        col1, col2 = st.columns([1, 4])
        with col1:
            st.markdown("<h1 style='font-size: 100px; margin: 0;'>👤</h1>", unsafe_allow_html=True)
        with col2:
            st.subheader(f"{user_info['first_name']} {user_info['last_name']}")
            #st.write("**University:** Google Cloud Tech")
            #st.write("**Major:** Computer Science")

            # Stop email hyperlinking
            email = user_info['email']
            email = email.replace("@", "<span>@</span>") 
            st.markdown(f"**Email:** {email}", unsafe_allow_html=True)

            st.write(f"**Date created:** {user_info['date_created']}")
            if user_info['is_verified']:
                st.write(f"**Verified:** ✅")
            else:
                st.write(f"**Verified:** ❌")
        
        st.divider()

        # User Resumes Dropdown Menu
        resumes = get_user_resume(1)
        options = {
            r_id: resumes[r_id]["FILENAME"]
            for r_id in resumes
        }

        st.title("Resumes")
        if options:
            st.selectbox(label="All submitted resumes", options=list(options.keys()), format_func=lambda x: options[x])
        else:
            st.write("No resumes found.")

        st.divider()

        # START CENTERED RESUME AREA (No border)
        st.markdown('<div class="resume-section">', unsafe_allow_html=True)
        
        # Centered Subheader
        st.markdown("<h2 style='text-align: center;'>⬇️Resume Analysis</h2>", unsafe_allow_html=True)
        st.markdown("<p style='text-align: center;'>Provide your resume to match with job keywords.</p>", unsafe_allow_html=True)

        # Center columns for buttons
        _, btn_col1, btn_col2, _ = st.columns([1.5, 2, 2, 1.5])

        # Initialize selection state if not exists
        if "resume_mode" not in st.session_state:
            st.session_state.resume_mode = "File"

        with btn_col1:
            st.markdown('<span class="upload-label">File Upload</span>', unsafe_allow_html=True)
            if st.button("📁", use_container_width=True, key="btn_file"):
                st.session_state.resume_mode = "File"
                st.rerun()

        with btn_col2:
            st.markdown('<span class="upload-label">Text Upload</span>', unsafe_allow_html=True)
            if st.button("📝", use_container_width=True, key="btn_text"):
                st.session_state.resume_mode = "Text"
                st.rerun()

        # Display the input area based on button selection
        st.write("") # Spacer
        
        # Create a nested column to keep the input area from stretching too wide
        _, input_col, _ = st.columns([1, 4, 1])
        with input_col:
            if st.session_state.resume_mode == "File":
                uploaded_file = st.file_uploader("Upload PDF", type=["pdf"], key="resume_upload", label_visibility="collapsed")
                
                if uploaded_file:
                    with st.spinner("Extracting text from resume..."):
                        extracted_text = extract_text_from_pdf(uploaded_file)
                        
                        if extracted_text:
                            st.session_state.user_resume = extracted_text
                            st.success("✅ Resume text extracted and saved!")
                        else:
                            st.error("Could not extract text. Try a different PDF or use Text Upload.")
            else:
                resume_text = st.text_area("Paste resume text here...", height=200, key="resume_text_area", label_visibility="collapsed")
                if resume_text:
                    st.session_state.user_resume = resume_text
                    st.info("Resume saved to session.")

        st.markdown('</div>', unsafe_allow_html=True)

custom_job_carousel = components.declare_component(
    "job_carousel", 
    path="job_carousel"
)

def Render_Job(container, jobs):
    if jobs and 'current_job_desc' not in st.session_state:
        st.session_state['current_job_desc'] = jobs[0].get('description', 'No description available.')
        st.session_state['current_job_id'] = jobs[0].get('id')

    with container:
        clicked_data = custom_job_carousel(jobs=jobs, key="main_carousel")

        if clicked_data:
            event = clicked_data.get("event")

            if event == "active_changed":
                job_id = clicked_data.get("id")

                for job in jobs:
                    if job.get("id") == job_id:
                        st.session_state["current_job_id"] = job.get("id")
                        st.session_state["current_job_desc"] = job.get("description", "")
                        break

            elif event == "save_clicked":
                job_id_to_save = clicked_data["id"]
                current_user_id = st.session_state.get('user_id', '1')

                with st.spinner("Saving job to favorites..."):
                    success = add_saved_job(current_user_id, job_id_to_save)

                    if success:
                        st.toast("✅ Job saved to favorites!")
                        if 'saved_jobs_loaded' in st.session_state:
                            del st.session_state['saved_jobs_loaded']
                    else:
                        st.error("Job already saved to favorites.")
        
def render_skills(skills): 
    chips = "" 
    for skill in skills: 
        chips += f'<span class="chip">{skill}</span>' 
    return chips

def render_apply_window_contents(job):
    st.markdown(f"### {job['title']}")
    st.write(f"Apply for **{job['company']}** via the official link below:")
    st.link_button(
        "Go to Application Site",
        job["link"],
        type="primary",
        use_container_width=True
    )


@st.dialog("Apply to this job")
def show_apply_window(job):
    render_apply_window_contents(job)   

def ResumeUploader(container):
    """
    Module 5: Function 1 - Upload Resume with High-Contrast Button Styling
    """
    # Targeting the internal Streamlit upload button and container
    st.markdown("""
        <style>
            /* 1. Style the main uploader box */
            [data-testid="stFileUploader"] {
                border-radius: 20px;
                padding: 10px;
                background-color: #ffffff;
                box-shadow: 5px 8px 20px rgba(0, 0, 0, 0.08);
                border: 1px solid #e5e7eb;
            }

            /* 2. Target the 'Browse files' button specifically */
            [data-testid="stFileUploader"] section button {
                background-color: #000000 !important;
                color: white !important;
                border-radius: 10px !important;
                border: none !important;
                padding: 0.5rem 1rem !important;
                transition: 0.3s;
            }

            /* FIX: Target the filename and file size text */
            [data-testid="stFileUploaderFileName"], 
            [data-testid="stFileUploaderFileData"] {
                color: #000000 !important;
                font-weight: 500 !important;
            }

            /* FIX: Target the 'Uploaded' checkmark and status text */
            [data-testid="stFileUploaderFileStatus"] {
                color: #000000 !important;
            }

            /* 3. Add a hover effect for the button */
            [data-testid="stFileUploader"] section button:hover {
                background-color: #333333 !important;
                box-shadow: 0px 4px 10px rgba(0,0,0,0.2);
            }

            /* 4. Style the text instruction (e.g., 'Limit 200MB per file') */
            [data-testid="stFileUploader"] section {
                color: #000000;
            }
        </style>
    """, unsafe_allow_html=True)

    with container:
        st.markdown("<p style='font-weight: bold; color: #31333F; margin-bottom: 10px;'>Upload Resume</p>", unsafe_allow_html=True)
        uploaded_file = st.file_uploader(
            "Upload Resume", 
            type=["pdf"], 
            key="home_resume_uploader",
            label_visibility="collapsed"
        )
        if uploaded_file:
            # Check file extension and extract text (Removed DOCX logic)
            if uploaded_file.name.lower().endswith('.pdf'):
                extracted_text = extract_text_from_pdf(uploaded_file)
            else:
                extracted_text = ""

            if 'current_resume_id' not in st.session_state:
                with st.spinner("Processing & Saving to Database..."):
                    # Call your new pipeline function
                    new_id = save_resume_pipeline(extracted_text) 
                    
                    # 3. STORE THE NEW ID IN SESSION STATE
                    st.session_state['current_resume_id'] = new_id
                    st.session_state['user_resume'] = extracted_text
                
                st.success(f"✅ Resume Processed! (ID: {st.session_state.get('current_resume_id')})")
        else:
            if 'current_resume' in st.session_state:
                del st.session_state['current_resume']
                st.rerun()

def KeywordMatcher(container):
    """
    Module 5: Function 2 - Compare Keywords with Styling
    """
    # Custom CSS for the match results area
    st.markdown("""
        <style>
            /* 1. Style for the ENABLED (Active) button */
            div.stButton > button[kind="primary"] {
                background-color: #000000 !important;
                color: white !important;
                border: 2px solid #000000 !important;
                border-radius: 10px !important;
                transition: 0.3s;
            }

            /* 2. Style for the DISABLED button - MAKING IT VISIBLE */
            div.stButton > button:disabled {
                background-color: #f0f2f6 !important; /* Light gray background */
                color: #808080 !important;          /* Darker gray text for contrast */
                border: 2px dashed #cccccc !important; /* Dashed border to show it's 'inactive' */
                cursor: not-allowed !important;
                opacity: 1 !important;              /* Prevent Streamlit from fading it out too much */
            }
            
            .match-card {
                background-color: white;
                border: 2px solid #000000;
                padding: 20px;
                border-radius: 15px;
                text-align: center;
                margin-top: 10px;
            }
        </style>
    """, unsafe_allow_html=True)

    with container:
        st.markdown("<p style='font-weight: bold; color: #31333F; margin-bottom: 5px;'>Compare to Job Description </p>", unsafe_allow_html=True)
                
        # 1. Define the condition: Is the resume missing?
        resume_id = st.session_state.get('current_resume_id')
        job_id = st.session_state.get('current_job_id')
        is_disabled = resume_id is None
         # 2. Use a single button with a dynamic 'disabled' property
        if st.button("Analyze Match Score", type="primary", use_container_width=True, key="analyze_match_btn", disabled=is_disabled):
            with st.spinner("Analyzing..."):
                import time
                time.sleep(1.5) 
                
                score, match_found = get_match_score(resume_id, job_id)
                # score = 78
                st.markdown(f"""
                    <div class="match-card">
                        <h2 style='margin:0; color:#000000;'>{score}%</h2>
                        <p style='color: #666;'>Keyword Match Score</p>
                    </div>
                """, unsafe_allow_html=True)
                if match_found:
                    st.info(f"**Matches found:** {', '.join(match_found)}")
                else:
                    st.warning("No matching skills found between your resume and this job.")

        # 3. Show the warning caption only if disabled
        if is_disabled:
            st.caption("⚠️ Please upload a resume to enable analysis.")


def extract_text_from_pdf(pdf_file):
    """ Uses pdfplumber to pull text from all PDF pages. """
    text = ""
    try:
        with pdfplumber.open(pdf_file) as pdf:
            for page in pdf.pages:
                page_text = page.extract_text()
                if page_text: text += page_text + "\n"
    except Exception as e:
        st.error(f"PDF Error: {e}")
    return text

@st.dialog("Confirm Deletion")
def confirm_delete_dialog(job):
    st.write(f"Are you sure you want to remove **{job['position']}** at **{job['company']}** from your saved jobs?")
    
    col1, col2 = st.columns(2)
    with col1:
        if st.button("Cancel", key=f"cancel_{job['id']}", use_container_width=True):
            st.rerun() 
            
    with col2:
        if st.button("Yes, Delete", key=f"confirm_{job['id']}", type="primary", use_container_width=True):
            
            # Fetch the current user ID (using the default 'user1' from your app.py if not set)
            current_user_id = st.session_state.get('user_id', '1')
            
            with st.spinner("Deleting..."):
                # Call the database function
                db_success = delete_saved_job(current_user_id, job["id"])
                
                if db_success:
                    # Database deletion worked! Now update the UI.
                    st.session_state.saved_jobs = [j for j in st.session_state.saved_jobs if j["id"] != job["id"]]
                    st.rerun() 
                else:
                    # Something went wrong in the DB
                    st.error("⚠️ Failed to delete from the database. Please try again later.")

    

def SavedJobs(container):
    # 2. Setup mock data if it doesn't exist
    if 'saved_jobs_loaded' not in st.session_state:
        current_user_id = st.session_state.get('user_id', '1') # Default to '1' if not logged in
        
        with st.spinner("Loading your saved jobs..."):
            # Call your freshly updated database function!
            st.session_state.saved_jobs = get_user_saved_jobs(current_user_id)
            st.session_state.saved_jobs_loaded = True

    # 3. Inject CSS to style the specific container and the buttons inside it
    st.markdown("""
        <style>
        /* Target the specific container key */
        div[data-testid="stVerticalBlock"] > div.st-key-saved_jobs_block {
            background-color: #24252C;
            border-radius: 12px;
            padding: 15px 20px;
            box-shadow: 0 4px 10px rgba(0,0,0,0.1);
        }

        /* Style the Streamlit buttons to look like transparent icons */
        div.st-key-saved_jobs_block button {
            background-color: transparent !important;
            border: none !important;
            box-shadow: none !important;
            font-size: 22px !important;
            color: white !important;
            padding: 0 !important;
            display: flex;
            justify-content: flex-end;
        }
        
        div.st-key-saved_jobs_block button:hover {
            color: #ff4b4b !important;
        }

        /* Custom divider for rows */
        hr.table-divider {
            border: 0;
            border-top: 1px solid #4f5058;
            margin: 0px 0;
        }
        </style>
    """, unsafe_allow_html=True)

    with container:
        st.title("Saved Jobs")
        # Wrap everything in a key-targeted container so the CSS only affects this table
        table_container = st.container(key="saved_jobs_block")
        
        with table_container:
            if not st.session_state.saved_jobs:
                st.markdown("<p style='text-align: center; color: #888;'>No saved jobs.</p>", unsafe_allow_html=True)
                return

            # --- Table Header ---
            col1, col2, col3, col4 = st.columns([2.5, 3.5, 2.5, 0.5])
            with col1: st.markdown("<p style='font-weight: bold;'>Company</p>", unsafe_allow_html=True)
            with col2: st.markdown("<p style='font-weight: bold;'>Position</p>", unsafe_allow_html=True)
            with col3: st.markdown("<p style='font-weight: bold;'>Deadline</p>", unsafe_allow_html=True)
            with col4: st.empty() # Placeholder for the trash icon column

            st.markdown("<hr class='table-divider'>", unsafe_allow_html=True)

            # --- Table Rows ---
            for i, job in enumerate(st.session_state.saved_jobs):
                c1, c2, c3, c4 = st.columns([2.5, 3.5, 2.5, 0.5], vertical_alignment="center")
                
                with c1: st.markdown(f"<p>{job['company']}</p>", unsafe_allow_html=True)
                with c2: st.markdown(f"<p>{job['position']}</p>", unsafe_allow_html=True)
                with c3: st.markdown(f"<p>{job['deadline']}</p>", unsafe_allow_html=True)
                with c4: 
                    # The delete button logic
                    if st.button("🗑️", key=f"del_job_{job['id']}"):
                        confirm_delete_dialog(job)

                # Add a divider under every row EXCEPT the last one
                if i < len(st.session_state.saved_jobs) - 1:
                    st.markdown("<hr class='table-divider'>", unsafe_allow_html=True)

def application_tracker(container):
    """
    Module for tracking job applications. 
    Allows users to add, edit status, and delete job applications.
    """
    with container:
        st.title("📋 Application Status Tracker")
        st.write("Keep track of your job hunt progress below.")

        if 'job_tracker' not in st.session_state:
            st.session_state.job_tracker = fetch_applications_from_bigquery()

        # 1. CREATE: Section to add a new job
        with st.expander("➕ Add New Job to Tracker", expanded=False):
            with st.form("add_job_form", clear_on_submit=True):
                new_job = st.text_input("Job Title", placeholder="e.g. Data Scientist at Google")
                
                # --- NEW: Date Input Field ---
                applied_date = st.date_input("Date Applied", value=datetime.date.today())
                
                submit_job = st.form_submit_button("Add to List")
                
                if submit_job and new_job:
                    application_id = str(uuid.uuid4())
                    applied_date_str = applied_date.strftime("%Y-%m-%d")

                    new_entry = {
                        "application_id": application_id,
                        "title": new_job,
                        "date": applied_date_str,
                        "status": "Applied"
                    }
                    st.session_state.job_tracker.append(new_entry)
                    
                    try:
                        insert_application_to_bigquery(application_id, new_job, applied_date_str)
                        st.toast(f"✅ Added {new_job} to database")
                    except Exception as e:
                        st.error(f"Database sync failed: {e}")
                    st.rerun()

        st.divider()

        # 2. LIST & EDIT/DELETE: Display the jobs
        if not st.session_state.job_tracker:
            st.info("No applications tracked yet. Use the button above to start!")
        else:
            for index, job in enumerate(st.session_state.job_tracker):
                with st.container(border=True):
                    # Adjusted column ratios to fit the date
                    col1, col2, col3, col4 = st.columns([3, 2, 2, 1])
                    
                    with col1:
                        st.markdown(f"**{job['title']}**")
                    
                    with col2:
                        # --- DISPLAY: The manual date ---
                        st.caption(f"📅 Applied: {job['date']}")
                    
                    with col3:
                        status_options = ["Applied", "Interview", "Rejected", "Accepted"]
                        current_index = status_options.index(job['status'])
                        
                        new_status = st.selectbox(
                            "Status",
                            options=status_options,
                            index=current_index,
                            key=f"status_{index}",
                            label_visibility="collapsed"
                        )
                        
                        if new_status != job['status']:
                            old_status = job['status']
                            st.session_state.job_tracker[index]['status'] = new_status
                            try:
                                update_application_status_in_bigquery(job['application_id'], new_status)
                                st.toast(f"Updated status for {job['title']}!")
                            except Exception as e:
                                # Revert UI state if database sync failed
                                st.session_state.job_tracker[index]['status'] = old_status
                                if "streaming buffer" in str(e).lower():
                                    st.error("⏳ Cannot update yet: BigQuery is still buffering this row. Try again in 30 mins.")
                                else:
                                    st.session_state.job_tracker[index]['status'] = old_status
                                    st.error(f"Update failed: {e}")
                            st.rerun()

                    with col4:
                        if st.button("🗑️", key=f"delete_{index}", help="Delete this application"):
                            deleted_job = st.session_state.job_tracker.pop(index)
                            try:
                                delete_application_from_bigquery(deleted_job['application_id'])
                                st.toast(f"Removed {deleted_job['title']}")
                            except Exception as e:
                                # Revert UI state (put the job back) if database deletion failed
                                st.session_state.job_tracker.insert(index, deleted_job)
                                if "streaming buffer" in str(e).lower():
                                    st.error("⏳ Cannot delete yet: This row is locked in BigQuery's buffer. Try again in 30 mins.")
                                else:
                                    st.session_state.job_tracker.insert(index, deleted_job)
                                    st.error(f"Delete failed: {e}")
                            st.rerun()
