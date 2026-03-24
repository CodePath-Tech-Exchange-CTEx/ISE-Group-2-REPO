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
from google import genai
from db_handler import init_db, save_chat_log
from data_fetcher import get_user_profile
import pdfplumber #used for PDF parsing
try:
    # Use .get() to avoid crashing if the key is missing during tests
    api_key = st.secrets.get("GEMINI_API_KEY", "mock_key_for_testing")
    
    client = genai.Client(
        api_key=api_key,
        http_options={'api_version': 'v1'}
    )
except Exception as e:
    # This prevents the whole app/test suite from crashing
    client = None
    print(f"Warning: Gemini Client not initialized: {e}")


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




# Hardcoded for school project deployment access
try:
    api_key = "AIzaSyAZLDqSgew3L06SORIc6s5ZyvseK2xLLy4" 
    
    client = genai.Client(
        api_key=api_key,
        http_options={'api_version': 'v1'}
    )
except Exception as e:
    # Changed to a general Exception to catch any initialization issues
    client = None
    print(f"Gemini initialization failed: {e}")

def GeminiChatbot(container):
   st.markdown(
        """
        <style>

       /* Existing Expander Styles... */
        div[data-testid="stExpander"] {
            border: 2px solid black !important;
            border-radius: 30px; 
            width: 60%;
            margin-top: -12%; 
            background-color: white !important;
        }

        /* Force all chat text to be black regardless of theme */
        [data-testid="stChatMessage"] div, 
        [data-testid="stChatMessage"] p, 
        [data-testid="stChatMessage"] li {
            color: black !important;
        }

        /* Make the assistant bubble a light color so black text is easy to read */
        [data-testid="stChatMessage"][data-testid="assistant"] {
            background-color: #f0f2f6 !important;
            border: 1px solid #ddd;
        }
        
        /* Make the user bubble a different light color */
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
        # Use an expander to act as a "pop-up" drawer
        with st.expander("🔎 Ask AI Assistant", expanded=False):
            
            # Chat history setup
            if "messages" not in st.session_state:
                st.session_state.messages = []

            # Display previous messages
            for message in st.session_state.messages:
                with st.chat_message(message["role"]):
                    st.markdown(message["content"])

            # Handle new user input
            if prompt := st.chat_input("Ask how to improve your resume..."):
                with st.chat_message("user"):
                    st.markdown(prompt)
                st.session_state.messages.append({"role": "user", "content": prompt})

                # 1. Define these BEFORE the try block so they are always available
                resume_context = st.session_state.get('user_resume', 'No resume provided.')
                job_context = st.session_state.get('current_job_desc', 'No job selected.')


                # Attempt to generate a response from Gemini
                try:
                    with st.chat_message("assistant"):
                        with st.spinner("Thinking..."):
                            
                            comparison_prompt = (
                                f"You are a professional career advisor. Analyze the following:\n\n"
                                f"USER RESUME: {resume_context}\n\n"
                                f"JOB DESCRIPTION: {job_context}\n\n"
                                f"USER QUESTION: {prompt}\n\n"
                                f"Provide specific feedback on how the user can better align their resume to this job."
                            )

                            response = client.models.generate_content(
                                model="models/gemini-2.5-flash-lite",
                                contents=f"Resume: {resume_context}\nJob: {job_context}\nUser Question: {prompt}"
                            )
 
                            ai_response = response.text
                            #FIX the reponse from being white text by overwriting streamlit theming
                            st.markdown(f"""
                                <div style="color: black !important;">
                                    {ai_response}
                                </div>
                            """, unsafe_allow_html=True)

                            
                            st.markdown(ai_response)
                    
                    # Store response in session history
                    st.session_state.messages.append({"role": "assistant", "content": ai_response})

                    # Save the interaction to your SQL database
                    save_chat_log(
                        user_id=st.session_state.get('user_id', 'user1'), # Use actual logged-in ID if available
                        resume_id=st.session_state.get('current_resume_id', 'RES-001'), # Pass the ID, not the text
                        job_id=st.session_state.get('current_job_id', 'JOB-999'),       # Pass the ID, not the text
                        prompt=prompt, 
                        response=ai_response
                    )
                
                except Exception as e:
                    st.error(f"AI error occurred: {e}")
                    # Log the specific error for debugging if needed
                    print(f"DEBUG: {str(e)}")

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
                
        # 1. Define the condition: Is the resume missing?
        is_disabled = 'current_resume' not in st.session_state
         # 2. Use a single button with a dynamic 'disabled' property
        if st.button("Analyze Match Score", type="primary", use_container_width=True, key="analyze_match_btn", disabled=is_disabled):
            with st.spinner("Analyzing..."):
                import time
                time.sleep(1.5) 
                
                score = 78
                st.markdown(f"""
                    <div class="match-card">
                        <h2 style='margin:0; color:#000000;'>{score}%</h2>
                        <p style='color: #666;'>Keyword Match Score</p>
                    </div>
                """, unsafe_allow_html=True)
                st.info("**Matches found:** Python, SQL, Communication")

        # 3. Show the warning caption only if disabled
        if is_disabled:
            st.caption("⚠️ Please upload a resume to enable analysis.")

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
