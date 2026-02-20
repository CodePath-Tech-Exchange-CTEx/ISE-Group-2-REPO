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

# Add this to modules.py

def GeminiChatbot(container):
   with container:
        # Use an expander to act as a "pop-up" drawer
        with st.expander("💬 Ask AI Assistant", expanded=False):
            st.info("The Gemini API is currently inactive. System is in UI-Preview mode.")
            
            # Chat history logic stays the same
            if "messages" not in st.session_state:
                st.session_state.messages = []

            for message in st.session_state.messages:
                with st.chat_message(message["role"]):
                    st.markdown(message["content"])

            if prompt := st.chat_input("Ask a question..."):
                with st.chat_message("user"):
                    st.markdown(prompt)
                st.session_state.messages.append({"role": "user", "content": prompt})

                # Mock response
                response = "I'll be ready to analyze your resume once the API is linked!"
                with st.chat_message("assistant"):
                    st.write(response)
                st.session_state.messages.append({"role": "assistant", "content": response})