#############################################################################
# app.py
#
# This file contains the entrypoint for the app.
#
#############################################################################

import streamlit as st


from modules import GeminiChatbot, NavBar, CompanySearch, Render_Job, ProfilePage, ResumeUploader, KeywordMatcher, SavedJobs, render_apply_window_contents, application_tracker
from data_fetcher import get_jobs

#init_db() #initialize database on startup

userId = 'user1'


# Page config
st.set_page_config(
    page_title="InternMatch",
    layout="wide"
)


########## code change ##########
# Initialize navigation state
if "page" not in st.session_state:
    st.session_state.page = "home"
#################################

#style font color of the app to be black and background color to white
st.markdown(
    """
    <style>
    .stApp {
        background-color: white;
        color: black;
    }

    /* Target only the Apply button's text (letter) color */
    .st-key-apply_btn_bottom button p {
        color: #6B5CA5 !important;
    }
    </style>
    """,
    unsafe_allow_html=True
)
# App container
def main_container():
    # Create the master container
    container = st.container()


    # Put any initial content inside it
    with container:
    
        st.markdown(
            "<h3 style='text-align: right;'>InternMatch 🟰</h3>", 
            unsafe_allow_html=True
        )
        
    return container



# Render app container
if __name__ == '__main__':
    app_container = main_container()

    if st.session_state.page == "home":

        search_query = CompanySearch(app_container)
        jobs = get_jobs()
        #Render_Job_Swiping(app_container, jobs)

        # Performs the "Live Filter" based on the search bar input above
        if search_query:
            # Filters by company name OR job title
            jobs_to_show = [j for j in jobs if search_query.lower() in j.get('company', '').lower() 
                            or search_query.lower() in j.get('title', '').lower()]
        else:
            # Default view (limiting to 20 for speed at scale)
            jobs_to_show = jobs[:20] 

        # dropdown allows users to specify which job description Gemini should reference.
        # Placing it here ensures users see the 'Selection' before they see the 'Visuals'.
        selected_job = None
        with app_container:
            if jobs_to_show:
                job_titles = [f"{j.get('title')} at {j.get('company')}" for j in jobs_to_show]
                
                selected_job_name = st.selectbox(
                    f"🎯 Found {len(jobs_to_show)} jobs. Select one to analyze with Gemini:", 
                    options=job_titles,
                    key="ai_job_selector"
                )
                
                # Update the session state so the chatbot has the correct context
                for j in jobs_to_show:
                    if f"{j.get('title')} at {j.get('company')}" == selected_job_name:
                        st.session_state['current_job_desc'] = j.get('description')
                        st.session_state['current_job_id'] = j.get('id') # for match score          
                        selected_job = j
                        break
            else:
                st.warning("No jobs found matching your search.")

        Render_Job(app_container, jobs_to_show)

        # Render the Apply button below the job card info
        with app_container:
            active_job = None
            current_job_id = st.session_state.get("current_job_id")

            if current_job_id:
                for job in jobs_to_show:
                    if job.get("id") == current_job_id:
                        active_job = job
                        break

            if active_job is None and selected_job:
                active_job = selected_job

            if active_job:
                if st.button("🚀 Apply for this Job", key="apply_btn_bottom", use_container_width=True):
                    render_apply_window_contents(active_job)

        GeminiChatbot(app_container)

        st.divider()
        col_left, col_right = app_container.columns(2)
        with col_left:
            ResumeUploader(st.container())
        with col_right:
            KeywordMatcher(st.container())

    elif st.session_state.page == "tracker":
        application_tracker(app_container)
           
        # Render Profile Page
    elif st.session_state.page == "profile":
        ProfilePage(app_container)

        st.divider()
        KeywordMatcher(st.container())
        st.divider()
        SavedJobs(st.container())
            

            
    # Render nav bar outside main containe
NavBar()
