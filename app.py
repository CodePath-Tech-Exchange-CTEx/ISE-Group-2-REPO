#############################################################################
# app.py
#
# This file contains the entrypoint for the app.
#
#############################################################################

import streamlit as st
from modules import *
from data_fetcher import get_user_posts, get_genai_advice, get_user_profile, get_user_sensor_data, get_user_workouts, get_jobs

userId = 'user1'


# Page config
st.set_page_config(
    page_title="InternMatch",
    layout="wide"
)

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

<<<<<<< HEAD
    # Put any initial content inside it
    with container:
    
        st.markdown(
            "<h3 style='text-align: right;'>InternMatch 🟰</h3>", 
            unsafe_allow_html=True
        )
        
=======
>>>>>>> 37a9588 (module 3 implementation)
    return container


# Render app container
if __name__ == '__main__':
    app_container = main_container()


    jobs = get_jobs()
    Render_Job_Swiping(app_container, jobs)

    # NEW: Render the chatbot prototype
    GeminiChatbot(app_container)

    # Render nav bar outside main container
    NavBar()

    

