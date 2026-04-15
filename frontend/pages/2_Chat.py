"""
Chat Page
RAG-powered chat assistant for queries
"""

import streamlit as st
from utils.session import init_session, get_student, is_logged_in
from utils.api_client import api_client
from utils.ui import load_css
from components.sidebar import render_sidebar
from components.chat_widget import render_chat_message


# Page config
st.set_page_config(
    page_title="Chat Assistant - AMU Registration",
    page_icon="💬",
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
st.title("💬 Chat Assistant")
st.markdown("Ask questions about courses, eligibility, ordinances, and more!")
st.markdown("---")

# Initialize chat history in session state
if 'chat_messages' not in st.session_state:
    st.session_state.chat_messages = []

# Display chat history
chat_container = st.container()

with chat_container:
    if not st.session_state.chat_messages:
        st.info("""
        👋 **Hi! I'm your AI assistant.**
        
        I can help you with:
        - ✅ Eligibility questions
        - 📚 Course recommendations
        - 📖 AMU ordinances and rules
        - 🎓 Registration procedures
        - 📊 Academic requirements
        
        **Try asking:**
        - "What are the promotion requirements?"
        - "Can I advance to final year?"
        - "Explain registration mode B"
        - "What courses should I take?"
        """)
    else:
        # Display chat history
        for msg in st.session_state.chat_messages:
            render_chat_message(msg['content'], msg['is_user'])

st.markdown("---")

# Chat input
col1, col2 = st.columns([6, 1])

with col1:
    user_input = st.text_input(
        "Type your question...",
        key="chat_input",
        placeholder="e.g., What are the promotion requirements for semester 4?"
    )

with col2:
    send_button = st.button("Send", type="primary", use_container_width=True)

# Handle message sending
if send_button and user_input:
    # Add user message to history
    st.session_state.chat_messages.append({
        'content': user_input,
        'is_user': True
    })
    
    # Show loading
    with st.spinner("🤔 Thinking..."):
        # Call chat API
        response = api_client.send_chat_message(
            student.get('id'),
            user_input
        )
        
        if "error" in response:
            assistant_message = f"❌ Error: {response['error']}"
        else:
            assistant_message = response.get('response', 'Sorry, I could not process that.')
            
            # Show sources if available
            sources = response.get('sources', [])
            if sources:
                assistant_message += "\n\n📚 **Sources:**\n"
                for source in sources:
                    assistant_message += f"- {source}\n"
        
        # Add assistant response to history
        st.session_state.chat_messages.append({
            'content': assistant_message,
            'is_user': False
        })
    
    # Rerun to show new messages
    st.rerun()

# Quick questions
st.markdown("---")
st.markdown("### 💡 Quick Questions")

col1, col2, col3 = st.columns(3)

with col1:
    if st.button("📋 Promotion Requirements", use_container_width=True):
        st.session_state.chat_messages.append({
            'content': "What are the promotion requirements?",
            'is_user': True
        })
        st.rerun()

with col2:
    if st.button("🚀 Can I Advance?", use_container_width=True):
        st.session_state.chat_messages.append({
            'content': "Can I register for advanced courses?",
            'is_user': True
        })
        st.rerun()

with col3:
    if st.button("📖 Registration Modes", use_container_width=True):
        st.session_state.chat_messages.append({
            'content': "Explain registration modes A, B, and C",
            'is_user': True
        })
        st.rerun()

# Clear chat button
st.markdown("---")
if st.button("🗑️ Clear Chat History", use_container_width=False):
    st.session_state.chat_messages = []
    st.rerun()