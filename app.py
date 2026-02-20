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
    page_title="Mobile App",
    layout="wide"
)

# App container
def main_container():
    # Create the master container
    container = st.container()

    # Put any initial content inside it
    with container:
        st.title("My App")
        st.write("All future modules will be stored inside this container.")

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
