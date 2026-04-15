"""
UI Utilities
Common UI components and styling
"""

import streamlit as st
import os

def load_css():
    """Load custom CSS from assets/styles.css"""
    css_file = os.path.join(os.path.dirname(os.path.dirname(__file__)), "assets", "styles.css")
    
    if os.path.exists(css_file):
        with open(css_file, "r") as f:
            st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)
    else:
        # Fallback styles if file not found
        st.markdown("""
        <style>
            .stApp {
                font-family: sans-serif;
            }
        </style>
        """, unsafe_allow_html=True)

def header(title: str, subtitle: str = None):
    """Render page header with consistent styling"""
    st.markdown(f"# {title}")
    if subtitle:
        st.markdown(f"### {subtitle}")
    st.markdown("---")

def card_metric(label: str, value: str, delta: str = None, color: str = None):
    """Render a metric card"""
    st.metric(label, value, delta=delta)
