#############################################################################
# app.py
#
# This file contains the entrypoint for the app.
#
#############################################################################

import streamlit as st
from modules import *
from modules import GeminiChatbot, NavBar, CompanySearch

userId = 'user1'


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


    #jobs = get_jobs()
    #Render_Job_Swiping(app_container, jobs)

    #MODULE4 
    CompanySearch(app_container)


    # NEW: Render the chatbot prototype
    GeminiChatbot(app_container)

    # Render nav bar outside main container
    NavBar()


