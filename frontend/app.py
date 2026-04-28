"""
AMU Course Registration System - Main App
Login Page
"""

import streamlit as st
from utils.session import init_session, set_student, is_logged_in
from utils.api_client import api_client
from components.sidebar import render_sidebar


from utils.ui import load_css

# Page config
st.set_page_config(
    page_title="AMU Registration System",
    page_icon="🎓",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Load custom CSS
load_css()

# Initialize session
init_session()

# If already logged in, show sidebar and redirect
if is_logged_in():
    render_sidebar()
    st.success("✅ You are already logged in!")
    st.info("👈 Use the sidebar to navigate to different pages")
    st.markdown("---")
    st.markdown("### Quick Links")
    col1, col2, col3 = st.columns(3)
    with col1:
        st.page_link("pages/1_Dashboard.py", label="📊 Dashboard", use_container_width=True)
    with col2:
        st.page_link("pages/2_Chat.py", label="💬 Chat", use_container_width=True)
    with col3:
        st.page_link("pages/5_Register.py", label="✅ Register", use_container_width=True)
    st.stop()


# Login Page UI
st.title("🎓 AMU Course Registration System")
st.markdown("### Zakir Husain College of Engineering & Technology")
st.markdown("---")

# Check backend health
with st.spinner("Checking backend connection..."):
    health = api_client.health_check()
    if health.get("status") == "offline":
        st.error("❌ Backend server is offline. Please start the backend first.")
        st.code("cd backend\npython main.py", language="bash")
        st.stop()
    else:
        st.success("✅ Backend server is online")

st.markdown("---")

# Login form
col1, col2, col3 = st.columns([1, 2, 1])

with col2:
    st.markdown("### 🔐 Student Login")
    
    with st.form("login_form"):
        faculty_number = st.text_input(
            "Faculty Number",
            placeholder="e.g., 23AIB001",
            help="Your faculty number (Format: YYBRANCHBnnn)"
        )
        
        enrollment_number = st.text_input(
            "Enrollment Number",
            placeholder="e.g., 202300101",
            help="Your enrollment number"
        )
        
        submit = st.form_submit_button("🚀 Login", use_container_width=True)
        
        if submit:
            if not faculty_number or not enrollment_number:
                st.error("❌ Please enter both faculty number and enrollment number")
            else:
                with st.spinner("Verifying credentials..."):
                    # Call login API
                    result = api_client.login(faculty_number, enrollment_number)
                    
                    if "error" in result:
                        st.error(f"❌ Login failed: {result['error']}")
                    elif result.get("verified"):
                        # Login successful
                        student_data = result.get("student")
                        set_student(student_data)
                        st.success(f"✅ {result.get('message', 'Login successful')}")
                        st.balloons()
                        st.rerun()
                    else:
                        st.error("❌ Invalid credentials. Please check your faculty number and enrollment number.")

# Demo credentials info
st.markdown("---")
with st.expander("ℹ️ Demo Credentials (For Testing)"):
    st.info("""
    **Demo Student Credentials:**
    
    After running `scripts/seed_database.py`, you can use:
    - Faculty Number: 23AIB001
    - Enrollment Number: 202300101
    
    Or any other student created by the seeding script.
    """)

# Footer
st.markdown("---")
st.markdown(
    """
    <div style='text-align: center; color: gray; font-size: 0.9em;'>
        Built with ❤️ for AMU ZHCET | Powered by AI & RAG
    </div>
    """,
    unsafe_allow_html=True
)