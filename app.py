#############################################################################
# app.py
#
# This file contains the entrypoint for the app.
#
#############################################################################

import streamlit as st

from modules import GeminiChatbot, NavBar, CompanySearch, Render_Job, ProfilePage, ResumeUploader, KeywordMatcher

from data_fetcher import get_jobs


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


    #jobs = get_jobs()
    #Render_Job_Swiping(app_container, jobs)

    #MODULE4 
    #CompanySearch(app_container)


    # NEW: Render the chatbot prototype
    #GeminiChatbot(app_container)

    #jobs = get_jobs()
    #Render_Job(app_container, jobs)

   
    ########## code change ##########
    # Logic to switch between Home and Profile
    if st.session_state.page == "home":
        # Render Home Page
        CompanySearch(app_container)
        
        
        jobs = get_jobs()
        Render_Job(app_container, jobs)
        
        GeminiChatbot(app_container)
        # --- NEW: MODULE 5 SECTION ---
   
        # with app_container.expander("🚀 Quick Match: Compare your Resume", expanded=True):
        #     col1, col2 = st.columns(2)
        ResumeUploader(app_container)
        KeywordMatcher(app_container)
        # st.divider()
        # -----------------------------
    
    elif st.session_state.page == "profile":
        # Render Profile Page
        ProfilePage(app_container)
    #################################


    # Render nav bar outside main container
    NavBar()


