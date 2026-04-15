"""
Registration Page
Select courses and submit registration
"""

import streamlit as st
from utils.session import init_session, get_student, is_logged_in
from utils.api_client import api_client
from utils.ui import load_css
from components.sidebar import render_sidebar


# Page config
st.set_page_config(
    page_title="Register - AMU Registration",
    page_icon="✅",
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

# Initialize selected courses in session
if 'selected_course_ids' not in st.session_state:
    st.session_state.selected_course_ids = []

# Page header
st.title("✅ Course Registration")
st.markdown("Select courses and submit your registration")
st.markdown("---")

# Check eligibility first
with st.spinner("Checking eligibility..."):
    eligibility = api_client.check_eligibility(student.get('id'))

if "error" in eligibility:
    st.error(f"❌ Error: {eligibility['error']}")
    st.stop()

# Check if student can register
can_register = eligibility.get('can_register', False)

if not can_register:
    st.error("### ⛔ Registration Blocked")
    st.markdown("You are currently not eligible to register for courses.")
    
    errors = eligibility.get('errors', [])
    for error in errors:
        st.error(error)
    
    st.markdown("---")
    st.info("Please contact your academic advisor for assistance.")
    st.stop()

# Get course recommendations
with st.spinner("Loading available courses..."):
    recommendations = api_client.get_course_recommendations(student.get('id'))

if "error" in recommendations:
    st.error(f"❌ Error: {recommendations['error']}")
    st.stop()

# Extract courses
current_courses = recommendations.get('courses', {}).get('current', [])
backlog_courses = recommendations.get('courses', {}).get('backlogs', [])
advance_courses = recommendations.get('courses', {}).get('advance', [])

# Registration mode selection
st.markdown("### 📋 Registration Mode")
st.info("""
**Registration Modes:**
- **Mode A:** Full attendance + All evaluations (Coursework, Mid-sem, End-sem)
- **Mode B:** Evaluations only (For theory courses with attendance fulfilled)
- **Mode C:** End-sem only (Previous sessional marks reused)
""")

registration_mode = st.radio(
    "Select Registration Mode",
    options=["a", "b", "c"],
    format_func=lambda x: f"Mode {x.upper()}",
    horizontal=True
)

st.markdown("---")

# Course selection
st.markdown("### 📚 Select Courses")

# Helper function to render course selection
def render_course_selection(courses, category_name, color):
    if not courses:
        return
    
    st.markdown(f"#### {color} {category_name}")
    
    for course in courses:
        course_id = course['course_id']
        
        # Checkbox for selection
        is_selected = st.checkbox(
            f"**{course['course_code']}** - {course['course_name']} ({course['credits']} credits)",
            key=f"course_{course_id}",
            value=course_id in st.session_state.selected_course_ids
        )
        
        # Update selection
        if is_selected and course_id not in st.session_state.selected_course_ids:
            st.session_state.selected_course_ids.append(course_id)
        elif not is_selected and course_id in st.session_state.selected_course_ids:
            st.session_state.selected_course_ids.remove(course_id)
        
        # Show course details
        if is_selected:
            with st.expander(f"ℹ️ Course Details - {course['course_code']}", expanded=False):
                col1, col2 = st.columns(2)
                with col1:
                    st.markdown(f"**Category:** {course['category']}")
                    st.markdown(f"**Credits:** {course['credits']}")
                with col2:
                    course_type = "Theory" if course.get('is_theory', True) else "Lab"
                    st.markdown(f"**Type:** {course_type}")

# Render course categories
if current_courses:
    render_course_selection(current_courses, "Current Semester Courses", "📖")
    st.markdown("---")

if backlog_courses:
    render_course_selection(backlog_courses, "Backlog Courses", "⚠️")
    st.markdown("---")

if advance_courses:
    render_course_selection(advance_courses, "Advancement Courses", "🚀")
    st.markdown("---")

# Calculate total credits
selected_courses_data = []
for course_id in st.session_state.selected_course_ids:
    # Find course in all lists
    for course in current_courses + backlog_courses + advance_courses:
        if course['course_id'] == course_id:
            selected_courses_data.append(course)
            break

total_selected_credits = sum(c['credits'] for c in selected_courses_data)

# Summary section
st.markdown("### 📊 Registration Summary")

col1, col2, col3, col4 = st.columns(4)

with col1:
    st.metric("Courses Selected", len(st.session_state.selected_course_ids))
with col2:
    st.metric("Total Credits", total_selected_credits)
with col3:
    within_limit = total_selected_credits <= 40
    st.metric(
        "Credit Status",
        "✅ OK" if within_limit else "⚠️ Exceeded",
        delta=f"{total_selected_credits}/40"
    )
with col4:
    st.metric("Mode", registration_mode.upper())

# Warnings
if total_selected_credits > 40:
    st.error("⚠️ **Warning:** Total credits exceed the maximum limit of 40 credits per semester!")
    st.markdown("Please deselect some courses.")

if total_selected_credits == 0:
    st.warning("⚠️ No courses selected. Please select at least one course.")

st.markdown("---")

# Selected courses list
if st.session_state.selected_course_ids:
    st.markdown("### 📋 Selected Courses")
    
    for course in selected_courses_data:
        col1, col2, col3 = st.columns([3, 1, 1])
        with col1:
            st.markdown(f"**{course['course_code']}** - {course['course_name']}")
        with col2:
            st.markdown(f"{course['credits']} credits")
        with col3:
            st.markdown(f"{course['category']}")
    
    st.markdown("---")

# Confirmation checkbox
st.markdown("### ✍️ Confirmation")

confirm = st.checkbox(
    "I confirm that I have reviewed my course selection and agree to the registration",
    value=False
)

# Submit button
st.markdown("---")

col1, col2, col3 = st.columns([2, 1, 2])

with col2:
    submit_disabled = (
        not confirm or 
        len(st.session_state.selected_course_ids) == 0 or 
        total_selected_credits > 40
    )
    
    if st.button(
        "🚀 Submit Registration",
        type="primary",
        use_container_width=True,
        disabled=submit_disabled
    ):
        with st.spinner("Submitting registration..."):
            # Submit registration
            result = api_client.submit_registration(
                student.get('id'),
                st.session_state.selected_course_ids,
                registration_mode
            )
            
            if "error" in result or not result.get("success"):
                st.error(f"❌ Registration failed: {result.get('message', 'Unknown error')}")
            else:
                st.success("✅ Registration submitted successfully!")
                st.balloons()
                
                # Show registration details
                st.markdown("---")
                st.markdown("### 🎉 Registration Confirmed!")
                
                col1, col2 = st.columns(2)
                with col1:
                    st.metric("Courses Registered", len(result.get('registration_ids', [])))
                with col2:
                    st.metric("Total Credits", result.get('total_credits', 0))
                
                st.info(f"""
                **Registration Details:**
                - Mode: {registration_mode.upper()}
                - Courses: {len(result.get('registration_ids', []))}
                - Credits: {result.get('total_credits', 0)}
                
                Your registration has been recorded. Check your dashboard for updated status.
                """)
                
                # Clear selected courses
                st.session_state.selected_course_ids = []
                
                # Navigation buttons
                st.markdown("---")
                col1, col2 = st.columns(2)
                with col1:
                    if st.button("📊 View Dashboard", use_container_width=True):
                        st.switch_page("pages/1_Dashboard.py")
                with col2:
                    if st.button("💬 Ask Assistant", use_container_width=True):
                        st.switch_page("pages/2_Chat.py")

# Help section
st.markdown("---")
with st.expander("ℹ️ Need Help?"):
    st.markdown("""
    **Registration Tips:**
    
    1. **Check Eligibility:** Make sure you meet all promotion requirements
    2. **Review Backlogs:** Clear backlog courses first if possible
    3. **Credit Limit:** Maximum 40 credits per semester
    4. **Prerequisites:** Ensure you've completed prerequisite courses
    5. **Mode Selection:** Choose appropriate registration mode
    
    **Registration Modes:**
    - **Mode A:** For new courses or if attendance not fulfilled
    - **Mode B:** For courses where you have attendance but failed evaluations
    - **Mode C:** For courses where you want to appear only for end-sem
    
    **Contact:**
    - Academic Office: academics@zhcet.ac.in
    - Help Desk: +91-XXX-XXXXXXX
    """)