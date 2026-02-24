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



def GeminiChatbot(container):
   st.markdown(
        """
        <style>
        
        div[data-testid="stExpander"] {
            border: 2px solid black !important;
            border-radius: 30px; 
        }
        

        div[data-testid="stExpander"] p {
            color: black !important;
            font-weight: bold;
        }
   

        /* Makes the chat input box also have a black outline */
        .stChatInput {
            border: 1px solid black !important;
            border-radius: 30px;
        }
        </style>
        """,
        unsafe_allow_html=True
    )
   with container:

        st.markdown('<div id="chatbot-section-wrapper"> <div id ="chatbot-expander">', unsafe_allow_html=True)
        # Use an expander to act as a "pop-up" drawer
        with st.expander("🔎 Ask AI Assistant", expanded=False):
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

        st.markdown('</div></div>', unsafe_allow_html=True)


def Render_Job(container, jobs):
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