"""
Courses Page
Browse and filter available courses
"""

import streamlit as st
import pandas as pd
from utils.session import init_session, get_student, is_logged_in
from utils.api_client import api_client
from utils.ui import load_css
from components.sidebar import render_sidebar


# Page config
st.set_page_config(
    page_title="Browse Courses - AMU Registration",
    page_icon="📚",
    layout="wide"
)

# Load custom CSS
load_css()

# Initialize and check login
init_session()
if not is_logged_in():
    st.warning("⚠️ Please login first")
    st.page_link("app.py", label="Go to Login", icon="🔐")
    st.stop()

# Render sidebar
render_sidebar()

# Get student data
student = get_student()

# Page header
st.title("📚 Browse Courses")
st.markdown("View available courses and recommendations")
st.markdown("---")

# Fetch course recommendations
with st.spinner("Loading course recommendations..."):
    recommendations = api_client.get_course_recommendations(student.get('id'))

if "error" in recommendations:
    st.error(f"❌ Error loading courses: {recommendations['error']}")
    st.stop()

# Extract courses
current_courses = recommendations.get('courses', {}).get('current', [])
backlog_courses = recommendations.get('courses', {}).get('backlogs', [])
advance_courses = recommendations.get('courses', {}).get('advance', [])

# Summary metrics
st.markdown("### 📊 Course Summary")
col1, col2, col3, col4 = st.columns(4)

with col1:
    st.metric("Current Semester", len(current_courses))
with col2:
    st.metric("Backlogs", len(backlog_courses))
with col3:
    st.metric("Advancement", len(advance_courses))
with col4:
    total_credits = recommendations.get('total_credits', 0)
    within_limit = recommendations.get('summary', {}).get('within_limit', True)
    st.metric(
        "Total Credits",
        total_credits,
        delta=f"{'✅ Within limit' if within_limit else '⚠️ Exceeds limit'}"
    )

st.markdown("---")

# Tabs for different course categories
tab1, tab2, tab3 = st.tabs(["📖 Current Semester", "⚠️ Backlogs", "🚀 Advancement"])

# Tab 1: Current Semester Courses
with tab1:
    if not current_courses:
        st.info("No current semester courses available.")
    else:
        st.markdown(f"### 📖 Current Semester Courses ({len(current_courses)})")
        st.markdown("These are courses for your current semester.")
        
        # Create dataframe
        df_current = pd.DataFrame(current_courses)
        
        # Display filters
        col1, col2 = st.columns(2)
        
        with col1:
            # Category filter
            categories = ["All"] + list(df_current['category'].unique())
            selected_category = st.selectbox("Filter by Category", categories, key="cat_current")
        
        with col2:
            # Type filter
            show_theory = st.checkbox("Theory Courses", value=True, key="theory_current")
            show_lab = st.checkbox("Lab Courses", value=True, key="lab_current")
        
        # Apply filters
        filtered_df = df_current.copy()
        
        if selected_category != "All":
            filtered_df = filtered_df[filtered_df['category'] == selected_category]
        
        if not show_theory:
            filtered_df = filtered_df[filtered_df['is_theory'] == False]
        if not show_lab:
            filtered_df = filtered_df[~filtered_df.get('is_lab', pd.Series([False] * len(filtered_df)))]
        
        st.markdown("---")
        
        # Display courses
        for _, course in filtered_df.iterrows():
            with st.expander(f"**{course['course_code']}** - {course['course_name']}"):
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    st.markdown(f"**Credits:** {course['credits']}")
                    st.markdown(f"**Category:** {course['category']}")
                
                with col2:
                    course_type = "Theory" if course.get('is_theory', True) else "Lab"
                    st.markdown(f"**Type:** {course_type}")
                    st.markdown(f"**Course ID:** {course['course_id']}")
                
                with col3:
                    if course.get('prerequisites'):
                        st.markdown(f"**Prerequisites:** {course['prerequisites']}")
                    else:
                        st.markdown("**Prerequisites:** None")

# Tab 2: Backlog Courses
with tab2:
    if not backlog_courses:
        st.success("✅ No backlog courses! Great job!")
    else:
        st.warning(f"### ⚠️ Backlog Courses ({len(backlog_courses)})")
        st.markdown("You must clear these courses.")
        
        for course in backlog_courses:
            with st.expander(f"**{course['course_code']}** - {course['course_name']} ⚠️"):
                col1, col2 = st.columns(2)
                
                with col1:
                    st.markdown(f"**Credits:** {course['credits']}")
                    st.markdown(f"**Semester:** {course.get('semester', 'N/A')}")
                
                with col2:
                    st.markdown(f"**Attempts:** {course.get('attempt_number', 1)}")
                    
                    if course.get('attendance_fulfilled'):
                        st.success("✅ Attendance fulfilled")
                        st.markdown("*Can register in Mode B or C*")
                    else:
                        st.warning("⚠️ Must register in Mode A")

# Tab 3: Advancement Courses
with tab3:
    if not advance_courses:
        st.info("ℹ️ No advancement courses available. Check eligibility requirements.")
    else:
        st.markdown(f"### 🚀 Advancement Courses ({len(advance_courses)})")
        st.markdown("You are eligible to register for these advanced courses!")
        
        for course in advance_courses:
            with st.expander(f"**{course['course_code']}** - {course['course_name']} 🚀"):
                col1, col2 = st.columns(2)
                
                with col1:
                    st.markdown(f"**Credits:** {course['credits']}")
                    st.markdown(f"**Category:** {course['category']}")
                
                with col2:
                    st.markdown(f"**Type:** Theory")
                    st.markdown(f"**Course ID:** {course['course_id']}")

# Warning about credit limit
st.markdown("---")
warning = recommendations.get('warning')
if warning:
    st.warning(f"⚠️ {warning}")

# Action buttons
st.markdown("---")
col1, col2, col3 = st.columns([2, 1, 2])

with col2:
    if st.button("✅ Proceed to Registration", type="primary", use_container_width=True):
        st.switch_page("pages/5_Register.py")