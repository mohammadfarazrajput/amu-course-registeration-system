"""
Chat Widget Component - kept for backward compatibility
The main chat UI is rendered inline in 2_Chat.py
"""
import streamlit as st


def render_chat_message(message: str, is_user: bool = True):
    if is_user:
        st.markdown(
            f'<div style="text-align:right;background:#4f46e5;color:#fff;'
            f'padding:10px 15px;border-radius:18px 18px 4px 18px;'
            f'margin:4px 0;font-size:14px;">{message}</div>',
            unsafe_allow_html=True
        )
    else:
        st.markdown(
            f'<div style="background:#1e1e2e;color:#e2e2f0;border:1px solid #2e2e45;'
            f'padding:10px 15px;border-radius:18px 18px 18px 4px;'
            f'margin:4px 0;font-size:14px;">{message}</div>',
            unsafe_allow_html=True
        )
