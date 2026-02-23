#############################################################################
# app.py
#
# This file contains the entrypoint for the app.
#
#############################################################################

import streamlit as st
from modules import *
from data_fetcher import get_user_posts, get_genai_advice, get_user_profile, get_user_sensor_data, get_user_workouts

userId = 'user1'

import streamlit as st

# Page config
st.set_page_config(
    page_title="InternMatch",
    layout="wide"
)

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

    # Write "user profile" into the container by passing the container into the function parameter
    UserProfile(app_container)

    # NEW: Render the chatbot prototype
    GeminiChatbot(app_container)

    # Render nav bar outside main container
    NavBar()
