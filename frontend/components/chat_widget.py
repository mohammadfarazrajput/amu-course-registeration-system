"""
Chat Widget Component
Display chat messages with styling
"""

import streamlit as st


def render_chat_message(message: str, is_user: bool = True):
    """
    Render a chat message bubble
    
    Args:
        message: Message text
        is_user: True if user message, False if agent message
    """
    
    if is_user:
        # User message
        st.markdown(
            f"""
            <div class="chat-message user">
                <strong>You:</strong><br>
                {message}
            </div>
            """,
            unsafe_allow_html=True
        )
    else:
        # Agent message
        st.markdown(
            f"""
            <div class="chat-message assistant">
                <strong>🤖 Assistant:</strong><br>
                {message}
            </div>
            """,
            unsafe_allow_html=True
        )