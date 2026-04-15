"""
Dashboard Page
Student overview with eligibility analysis
"""

import streamlit as st
import plotly.graph_objects as go
from utils.session import init_session, get_student, is_logged_in
from utils.api_client import api_client
from utils.ui import load_css
from components.sidebar import render_sidebar


# Page config
st.set_page_config(
    page_title="Dashboard - AMU Registration",
    page_icon="📊",
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
st.title("📊 Student Dashboard")
st.markdown(f"**Welcome back, {student.get('name')}!**")
st.markdown("---")

# Fetch eligibility data
with st.spinner("Loading your data..."):
    eligibility = api_client.check_eligibility(student.get('id'))

if "error" in eligibility:
    st.error(f"❌ Error loading data: {eligibility['error']}")
    st.stop()

# Key Metrics Row
col1, col2, col3, col4 = st.columns(4)

with col1:
    cgpa = eligibility.get('cgpa', 0.0)
    cgpa_color = "normal" if cgpa >= 6.5 else "off"
    st.metric(
        "CGPA",
        f"{cgpa:.2f}",
        delta=f"{'Good' if cgpa >= 7.5 else 'Fair' if cgpa >= 6.5 else 'Low'}"
    )

with col2:
    credits = eligibility.get('total_earned_credits', 0)
    st.metric("Total Credits", credits)

with col3:
    semester = eligibility.get('current_semester', 1)
    st.metric("Current Semester", semester)

with col4:
    backlogs = eligibility.get('backlog_count', 0)
    st.metric("Backlogs", backlogs, delta=f"{'✅ None' if backlogs == 0 else '⚠️ Clear these'}")

st.markdown("---")

# Status Cards
col1, col2 = st.columns(2)

with col1:
    # Eligibility Status
    status = eligibility.get('status', 'UNKNOWN')
    can_register = eligibility.get('can_register', False)
    
    if status == "ELIGIBLE":
        st.success("### ✅ Eligibility Status: ELIGIBLE")
        st.markdown("You can proceed with course registration.")
    else:
        st.error("### ⛔ Eligibility Status: BLOCKED")
        st.markdown("Registration is currently blocked.")
    
    # Risk Level
    risk_level = eligibility.get('risk_level', 'LOW')
    if risk_level == "CRITICAL":
        st.error(f"🚨 **Risk Level:** {risk_level}")
    elif risk_level == "HIGH":
        st.warning(f"⚠️ **Risk Level:** {risk_level}")
    elif risk_level == "MEDIUM":
        st.info(f"ℹ️ **Risk Level:** {risk_level}")
    else:
        st.success(f"✅ **Risk Level:** {risk_level}")

with col2:
    # Advancement Status
    can_advance = eligibility.get('can_advance', False)
    
    if can_advance:
        st.success("### 🚀 Advancement: ELIGIBLE")
        st.markdown("You can register for advanced courses!")
    else:
        st.info("### ℹ️ Advancement: Not Eligible")
        st.markdown("Focus on current semester courses.")
    
    # Allowed Registration Types
    allowed_types = eligibility.get('allowed_registration_types', [])
    st.markdown("**Allowed Registrations:**")
    for reg_type in allowed_types:
        st.markdown(f"- ✅ {reg_type}")

st.markdown("---")

# Warnings
warnings = eligibility.get('warnings', [])
if warnings:
    st.warning("### ⚠️ Warnings")
    for warning in warnings:
        st.markdown(f"- {warning}")
    st.markdown("---")

# Recommendations
recommendations = eligibility.get('recommendations', [])
if recommendations:
    st.info("### 💡 Recommendations")
    for rec in recommendations:
        st.markdown(f"- {rec}")
    st.markdown("---")

# Backlog Courses
backlogs = eligibility.get('backlog_courses', [])
if backlogs:
    st.error("### 📚 Backlog Courses")
    for backlog in backlogs:
        with st.expander(f"{backlog.get('course_code')} - {backlog.get('course_name')}"):
            st.markdown(f"**Credits:** {backlog.get('credits')}")
            st.markdown(f"**Semester:** {backlog.get('semester')}")
            st.markdown(f"**Attempts:** {backlog.get('attempt_number')}")
            if backlog.get('attendance_fulfilled'):
                st.success("✅ Attendance fulfilled - Can register in Mode B or C")
            else:
                st.warning("⚠️ Must register in Mode A (Full attendance)")
    st.markdown("---")

# CGPA Progress Chart
st.markdown("### 📈 Academic Progress")

# Create a simple gauge chart for CGPA
fig = go.Figure(go.Indicator(
    mode="gauge+number+delta",
    value=cgpa,
    domain={'x': [0, 1], 'y': [0, 1]},
    title={'text': "CGPA", 'font': {'size': 24}},
    delta={'reference': 7.5, 'increasing': {'color': "green"}},
    gauge={
        'axis': {'range': [None, 10], 'tickwidth': 1, 'tickcolor': "darkblue"},
        'bar': {'color': "darkblue"},
        'bgcolor': "white",
        'borderwidth': 2,
        'bordercolor': "gray",
        'steps': [
            {'range': [0, 5.5], 'color': '#ffcdd2'},
            {'range': [5.5, 6.5], 'color': '#fff9c4'},
            {'range': [6.5, 7.5], 'color': '#c5e1a5'},
            {'range': [7.5, 10], 'color': '#a5d6a7'}
        ],
        'threshold': {
            'line': {'color': "red", 'width': 4},
            'thickness': 0.75,
            'value': 6.5
        }
    }
))

fig.update_layout(height=300)
st.plotly_chart(fig, use_container_width=True)

# Quick Actions
st.markdown("---")
st.markdown("### 🚀 Quick Actions")

col1, col2, col3 = st.columns(3)

with col1:
    if st.button("💬 Ask Assistant", use_container_width=True):
        st.switch_page("pages/2_Chat.py")

with col2:
    if st.button("📚 Browse Courses", use_container_width=True):
        st.switch_page("pages/4_Courses.py")

with col3:
    if can_register:
        if st.button("✅ Register Now", use_container_width=True, type="primary"):
            st.switch_page("pages/5_Register.py")
    else:
        st.button("✅ Register (Blocked)", use_container_width=True, disabled=True)