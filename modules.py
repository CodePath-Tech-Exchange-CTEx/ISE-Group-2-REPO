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


def NavBar():
    st.markdown("""
        <style>
            .bottom-nav {
                position: fixed;
                bottom: 0;
                left: 0;
                width: 100%;
                background: white;
                border-top: 1px solid #ccc;
                padding: 12px;
                text-align: center;
                z-index: 9999;
            }
            .bottom-nav span {
                color: black
            }
        </style>

        <div class="bottom-nav">
            <span>Navbar</span>
        </div>
    """, unsafe_allow_html=True)

def UserProfile(container):
    with container:
        st.subheader("User Profile")
        st.write("Example of how to write into the main container from a module")
