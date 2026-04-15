"""
Upload Page
Marksheet upload and processing
"""

import streamlit as st
from utils.session import init_session, get_student, is_logged_in
from utils.ui import load_css
from components.sidebar import render_sidebar


# Page config
st.set_page_config(
    page_title="Upload Marksheet - AMU Registration",
    page_icon="📄",
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
st.title("📄 Upload Marksheet")
st.markdown("Upload your marksheet for automatic grade extraction")
st.markdown("---")

# Information section
col1, col2 = st.columns([2, 1])

with col1:
    st.markdown("### 📋 Instructions")
    st.markdown("""
    **Supported formats:**
    - 📄 PDF files
    - 🖼️ Images (JPG, PNG)
    
    **What happens after upload:**
    1. ✅ Document is processed using OCR
    2. ✅ Tables and grades are extracted
    3. ✅ Courses are identified automatically
    4. ✅ Backlog courses are detected
    5. ✅ Your records are updated
    
    **Tips for best results:**
    - Ensure the document is clear and readable
    - Avoid blurry or skewed images
    - Use official marksheets if possible
    """)

with col2:
    st.info("""
    **📊 Extracted Information:**
    
    - Student ID
    - Semester
    - Course codes
    - Grades obtained
    - Credits earned
    - CGPA/SGPA
    """)

st.markdown("---")

# File upload
st.markdown("### 📤 Upload Document")

uploaded_file = st.file_uploader(
    "Choose a file",
    type=['pdf', 'jpg', 'jpeg', 'png'],
    help="Upload your marksheet (PDF or Image)"
)

if uploaded_file is not None:
    # Display file info
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Filename", uploaded_file.name)
    with col2:
        st.metric("File Size", f"{uploaded_file.size / 1024:.1f} KB")
    with col3:
        st.metric("Type", uploaded_file.type)
    
    st.markdown("---")
    
    # Preview
    st.markdown("### 👀 Preview")
    
    if uploaded_file.type == "application/pdf":
        st.info("📄 PDF uploaded. Preview not available in browser.")
        st.markdown("*PDF will be processed for text and table extraction.*")
    else:
        # Display image preview
        st.image(uploaded_file, caption="Uploaded Image", use_column_width=True)
    
    st.markdown("---")
    
    # Process button
    col1, col2, col3 = st.columns([2, 1, 2])
    
    with col2:
        if st.button("🚀 Process Document", type="primary", use_container_width=True):
            with st.spinner("Processing document..."):
                # Simulate processing (in real implementation, call backend API)
                import time
                time.sleep(2)
                
                st.success("✅ Document processed successfully!")
                
                # Show extracted data (demo)
                st.markdown("### 📊 Extracted Information")
                
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("Semester", "4")
                with col2:
                    st.metric("SGPA", "8.5")
                with col3:
                    st.metric("Credits Earned", "26")
                
                st.markdown("---")
                
                # Extracted courses (demo)
                st.markdown("### 📚 Courses Found")
                
                demo_courses = [
                    {"code": "AIC2042", "name": "Machine Learning", "grade": "A", "credits": 4},
                    {"code": "AIC2142", "name": "Design & Analysis", "grade": "A", "credits": 4},
                    {"code": "AIC2152", "name": "AI Tools", "grade": "B+", "credits": 4},
                    {"code": "AMS2632", "name": "Discrete Structures", "grade": "A+", "credits": 4},
                ]
                
                for course in demo_courses:
                    with st.expander(f"{course['code']} - {course['name']}"):
                        col1, col2 = st.columns(2)
                        with col1:
                            st.markdown(f"**Grade:** {course['grade']}")
                        with col2:
                            st.markdown(f"**Credits:** {course['credits']}")
                
                st.markdown("---")
                
                st.info("""
                ℹ️ **Next Steps:**
                
                The extracted information has been saved to your academic records.
                You can now:
                - View updated records in your Dashboard
                - Check eligibility status
                - Proceed with course registration
                """)
                
                if st.button("📊 Go to Dashboard", use_container_width=False):
                    st.switch_page("pages/1_Dashboard.py")

else:
    # No file uploaded yet
    st.info("👆 Please upload a marksheet to begin processing")
    
    # Sample marksheet
    st.markdown("---")
    with st.expander("📄 Don't have a marksheet? See sample format"):
        st.markdown("""
        **Sample Marksheet Format:**
        
        ```
        ALIGARH MUSLIM UNIVERSITY
        Faculty of Engineering & Technology
        
        Student Name: Ahmed Khan
        Faculty Number: 23AIB001
        Enrollment: 202300101
        Branch: Artificial Intelligence
        Semester: 4
        
        ┌──────────┬────────────────────────┬────────┬───────┐
        │ Code     │ Course Name            │ Grade  │Credits│
        ├──────────┼────────────────────────┼────────┼───────┤
        │ AIC2042  │ Machine Learning       │   A    │   4   │
        │ AIC2142  │ Design & Analysis      │   A    │   4   │
        │ AIC2152  │ AI Tools & Techniques  │   B+   │   4   │
        │ AMS2632  │ Discrete Structures    │   A+   │   4   │
        └──────────┴────────────────────────┴────────┴───────┘
        
        SGPA: 8.50  |  CGPA: 8.20
        ```
        """)

# Footer note
st.markdown("---")
st.info("""
**🔒 Privacy Note:**

Your uploaded documents are processed securely and stored only for academic record purposes.
Documents are never shared with third parties.
""")