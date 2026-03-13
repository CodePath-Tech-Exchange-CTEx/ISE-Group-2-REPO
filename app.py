#############################################################################
# app.py
#
# This file contains the entrypoint for the app.
#
#############################################################################

import streamlit as st

from modules import GeminiChatbot, NavBar, CompanySearch, Render_Job, ProfilePage, ResumeUploader, KeywordMatcher
from data_fetcher import get_jobs
from db_handler import init_db, save_chat_log

init_db() #initialize database on startup

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

        #MODULE4
        if search_query:
            jobs_to_show = [j for j in jobs if search_query.lower() in j.get('company', '').lower()]
        else:
            jobs_to_show = jobs 
        #CompanySearch(app_container)

        # Store the description of the top job so the chatbot can see it
        if jobs_to_show:
            st.session_state['current_job_desc'] = jobs_to_show[0].get('description')
        

        Render_Job(app_container, jobs_to_show)
        GeminiChatbot(app_container)

        # with app_container.expander("🚀 Quick Match: Compare your Resume", expanded=True):
        #     col1, col2 = st.columns(2)
        ResumeUploader(app_container)
        KeywordMatcher(app_container)
        # st.divider()
        # -----------------------------

        # Render Profile Page
    elif st.session_state.page == "profile":
        ProfilePage(app_container)
        #################################


    # Render nav bar outside main containe
NavBar()


