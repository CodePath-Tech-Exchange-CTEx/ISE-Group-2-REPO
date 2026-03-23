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
from data_fetcher import get_resume_with_skills, save_chat_session, get_chat_context
import pdfplumber


PROJECT_ID = "oluwanifemi-elias-hu"
LOCATION = "us-central1"

vertexai.init(project=PROJECT_ID, location=LOCATION)
model = GenerativeModel("gemini-2.0-flash")


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
    .st-key-nav_container .st-key-nav_settings_btn button {
        background: inherit !important;
        font-size: 24px !important;
        color: gray !important;
        display: flex;
        text-align: center;
    }

    /*Button text styling*/
    .st-key-nav_container .st-key-nav_home_btn button p,
    .st-key-nav_container .st-key-nav_profile_btn button p,
    .st-key-nav_container .st-key-nav_settings_btn button p{
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
        col1, col2, col3 = st.columns([1, 1, 1], vertical_alignment="center", gap="small")

        with col1:
            st.button("⚙️", key="nav_settings_btn")

        with col2:
            if st.button("🏠", key="nav_home_btn"):
                st.session_state.page = "home"
                st.rerun()
        with col3: 
            if st.button("👤", key="nav_profile_btn"):
                st.session_state.page = "profile"
                st.rerun()



def GeminiChatbot(container):
    # --- CSS STYLING ---
    st.markdown(
        """
        <style>
        /* Expander as a "pop-up" drawer */
        div[data-testid="stExpander"] {
            border: 2px solid black !important;
            border-radius: 30px; 
            width: 60%;
            margin-top: -12%; 
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
                    
                    with st.chat_message("assistant"):
                        with st.spinner("Analyzing with Vertex AI..."):
                            
                            # 4. CONSTRUCT THE STRUCTURED PROMPT (Prompt Engineering)
                            # We inject real data from BigQuery into the instructions
                            full_prompt = (
                                f"You are a professional career advisor.\n\n"
                                f"CANDIDATE PROFILE:\n"
                                f"- Name: {resume_data.get('name', 'Applicant')}\n"
                                f"- University: {resume_data.get('university', 'Not Specified')}\n"
                                f"- Skills: {skills_list}\n\n"
                                f"JOB CONTEXT: {st.session_state.get('current_job_desc', 'General Career Advice')}\n\n"
                                f"USER QUESTION: {prompt}"
                            )

                            # 5. VERTEX AI GENERATION
                            # We use 'model' defined at the top of modules.py via vertexai.init
                            response = model.generate_content(full_prompt)
                            ai_response = response.text
                            
                            # Display AI response in the UI
                            st.markdown(ai_response)
                    
                    # 6. SAVE INTERACTION BACK TO BIGQUERY
                    # This closes the loop: Data -> AI -> Data Storage
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


        </style>
    """, unsafe_allow_html=True)

    with container:
        st.title("User Profile")
        
        # User Info Section
        col1, col2 = st.columns([1, 4])
        with col1:
            st.markdown("<h1 style='font-size: 100px; margin: 0;'>👤</h1>", unsafe_allow_html=True)
        with col2:
            st.subheader("John Doe")
            st.write("**University:** Google Cloud Tech")
            st.write("**Major:** Computer Science")
        
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
                uploaded_file = st.file_uploader("Upload PDF or Word Doc", type=["pdf", "docx"], key="resume_upload", label_visibility="collapsed")
                
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

def Render_Job(container, jobs):
    # Ensures the first job in the carousel is the active context if none is selected
    if jobs and 'current_job_desc' not in st.session_state:
        st.session_state['current_job_desc'] = jobs[0].get('description', 'No description available.')
    
    html = """
    <style>
    /* Horizontal swipe container */
    .carousel {
    display : flex;    /* cards side by side */
    overflow-x : auto;    /* allow horizontal scroll */
    scroll-snap-type : x mandatory;    /* snap page by page */
    -webkit-overflow-scrolling: touch;    /* smooth iOS scrolling */
    gap: 16px;
    padding: 12px 2px;
    width: 100%;
    touch-action: pan-x;
    }
    /*Remove scroll bar*/
    .carousel::-webkit-scrollbar { display: none; }

    /* Job page*/
    .card {
    flex: 0 0 100%;    /*Manages the space of the card in the screen*/
    scroll-snap-align: start;    /*When snapping, allign card with screen*/
    border: 1px solid #e5e7eb;
    border-radius: 18px;
    padding: 22px;
    background: #ffffff;
    min-height: 52vh;
    box-shadow: 0 8px 20px rgba(0, 0, 0, 0.08);
    box-sizing: border-box;
    font-family: ui-sans-serif, system-ui, -apple-system, Segoe UI, Roboto, Arial;
    }
    .header {
    display: flex;
    align-items: center;
    gap: 12px;
    margin-bottom: 10px;
    }
    /* simple logo circle */
    .logo {
    width: 44px;
    height: 44px;
    border-radius: 12px;
    background: #f3f4f6;
    display: flex;
    align-items: center;
    justify-content: center;
    font-weight: 800;
    color: #111827;
    font-size: 18px;
    flex: 0 0 auto;
      }
    .company { 
    font-size: 28px; 
    font-weight: 700; 
    margin: 0; 
    }
    .title { 
    color: #555; 
    margin-top: 4px; 
    margin-bottom: 16px; 
    }
    .label { 
    font-weight: 700; 
    margin-top: 18px; 
    margin-bottom: 6px; 
    }
    .subtext {
    margin: 10px 0 14px 0;
    color: #6b7280;
    font-size: 16px;
    }

    /* badges */
    .badges { display: flex; gap: 10px; flex-wrap: wrap; margin: 10px 0 14px 0; }
    .badge-open {
    background: #d1fae5;
    color: #065f46;
    padding: 8px 12px;
    border-radius: 10px;
    font-weight: 700;
    font-size: 14px;
    display: inline-flex;
    align-items: center;
    gap: 8px;
    }
    .badge-salary {
    background: #fee2e2;
    color: #991b1b;
    padding: 8px 12px;
    border-radius: 10px;
    font-weight: 700;
    font-size: 14px;
    display: inline-flex;
    align-items: center;
    gap: 8px;
    }
    /* skills row */
    .skills-row {
    display: flex;
    flex-wrap: wrap;
    gap: 8px;
    margin: 10px 0 18px 0;
    }
    .chip { 
    display: inline-block; 
    padding: 8px 10px; 
    border-radius: 10px; 
    border: 1px solid #e5e7eb; 
    background: #f9fafb; 
    font-size: 14px;
    font-weight: 650;
    color: #111827; 
    }
    /* bottom location badge */
    .location {
    background: #dcfce7;
    color: #166534;
    display: inline-flex;
    align-items: center;
    gap: 8px;
    padding: 8px 12px;
    border-radius: 10px;
    font-weight: 800;
    font-size: 14px;
    margin-top: 10px;
    }

    .section {
    margin-top: 14px;
    color: #111827;
    }
    .section b { color: #111827; }
    .section p { margin: 6px 0; color: #374151; }
    </style>
    <div class="carousel">
    """

    # HTML Container
    for job in jobs:
        company = job.get("company", "")
        title = job.get("title", "")
        description = job.get("description", "")
        experience = job.get("experience", "")
        location = job.get("location", "")
        skills_html = render_skills(job.get("skills", []))


        html += f"""
        <section class="card">
          <div class="header">
            <div>
              <h2 class="title">{title}</h2>
              <div class="company">{company}</div>
            </div>
          </div>

          <div class="badges">
            <div class="badge-open">✅ Open for applications</div>
          </div>

          <div class="skills-row">
            {skills_html}
          </div>

          <div class="section">
            <p><b>Job Description:</b> {description}</p>
            <p><b>Experience:</b> {experience}</p>
          </div>

          <div class="location">📍 {location}</div>
        </section>
        """

    html += "</div>"

    with container:
        components.html(html, height=550, scrolling=True) 
        
def render_skills(skills): 
    chips = "" 
    for skill in skills: 
        chips += f'<span class="chip">{skill}</span>' 
    return chips

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
            type=["pdf", "docx"], 
            key="home_resume_uploader",
            label_visibility="collapsed"
        )
        if uploaded_file:
            # Extract text so Gemini can read it later
            extracted_text = extract_text_from_pdf(uploaded_file)
            st.session_state['user_resume'] = extracted_text
            st.session_state['current_resume'] = uploaded_file # For UI tracking
            st.success("✅ File Ready & Processed!")
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
        
        # Check if file exists in session state
        if 'current_resume' not in st.session_state:
            st.button("Compare to Job Descriptions", disabled=True, use_container_width=True, key="disabled_match_btn")
            st.caption("⚠️ Please upload a resume to enable analysis.")
        else:
            if st.button("Analyze Match Score", type="primary", use_container_width=True):
                with st.spinner("Analyzing..."):
                    import time
                    time.sleep(1.5) 
                    
                    score = 78
                    
                    # Styled results container
                    st.markdown(f"""
                        <div class="match-card">
                            <h2 style='margin:0; color:#000000;'>{score}%</h2>
                            <p style='color: #666;'>Keyword Match Score</p>
                        </div>
                    """, unsafe_allow_html=True)
                    
                    st.info("**Matches found:** Python, SQL, Communication")




def extract_text_from_pdf(pdf_file):
    """
    Parses an uploaded PDF file and concatenates text from all available pages.
    
    Args:
        pdf_file (file-like object): The PDF file uploaded via Streamlit.
        
    Returns:
        str: A single string containing the full text of the PDF, 
             separated by newlines. Returns an empty string if extraction fails.
    """
    text = ""
    try:
        # Open the PDF binary stream
        with pdfplumber.open(pdf_file) as pdf:
            # Iterate through each page to ensure multi-page resumes are captured
            for page in pdf.pages:
                page_text = page.extract_text()
                
                # Only append if the page actually contains extractable text
                if page_text:
                    text += page_text + "\n"
                    
    except Exception as e:
        # Log the specific error to the Streamlit UI for user feedback
        st.error(f"Error reading PDF: {e}")
        
    return text

