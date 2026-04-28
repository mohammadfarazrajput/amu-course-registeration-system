"""
Sidebar Component
Navigation and student info display
"""

import streamlit as st
from utils.session import get_student, clear_session


def render_sidebar():
    """Render sidebar with student info and navigation"""
    
    student = get_student()
    
    if not student:
        return
    
    with st.sidebar:
        # Header
        st.markdown("### 🎓 AMU ZHCET")
        st.markdown("**Course Registration System**")
        st.divider()
        
        # Student Info
        st.markdown("#### 👤 Student Profile")
        st.markdown(f"**Name:** {student.get('name', 'N/A')}")
        st.markdown(f"**Faculty #:** {student.get('faculty_number', 'N/A')}")
        st.markdown(f"**Branch:** {student.get('branch', 'N/A')}")
        st.markdown(f"**Semester:** {student.get('current_semester', 'N/A')}")
        
        st.divider()
        
        # Performance Metrics
        st.markdown("#### 📊 Performance")
        
        col1, col2 = st.columns(2)
        with col1:
            st.metric("CGPA", f"{student.get('cgpa', 0.0):.2f}")
        with col2:
            st.metric("Credits", student.get('total_earned_credits', 0))
        
        st.divider()
        
        # Navigation
        st.markdown("#### 📋 Navigation")
        st.page_link("app.py", label="🏠 Home", icon="🏠")
        st.page_link("pages/1_Dashboard.py", label="📊 Dashboard", icon="📊")
        st.page_link("pages/2_Chat.py", label="💬 Chat Assistant", icon="💬")
        st.page_link("pages/3_Upload.py", label="📄 Upload Marksheet", icon="📄")
        st.page_link("pages/4_Courses.py", label="📚 Browse Courses", icon="📚")
        st.page_link("pages/5_Register.py", label="✅ Register", icon="✅")
        st.page_link("pages/6_Certificates.py", label="🏅 Certificates", icon="🏅")
        
        st.divider()
        
        # Logout button
        if st.button("🚪 Logout", use_container_width=True):
            clear_session()
            st.rerun()