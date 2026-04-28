"""
Chat Page - RAG-powered assistant
LLM is used ONLY here, for interpreting student questions + ordinances.
"""

import streamlit as st
from utils.session import init_session, get_student, is_logged_in
from utils.api_client import api_client
from utils.ui import load_css
from components.sidebar import render_sidebar

st.set_page_config(
    page_title="Chat Assistant - AMU Registration",
    page_icon="💬",
    layout="wide"
)

load_css()
init_session()

if not is_logged_in():
    st.warning("⚠️ Please login first")
    st.page_link("app.py", label="Go to Login", icon="🔐")
    st.stop()

render_sidebar()
student = get_student()

# ── Chat UI styles ─────────────────────────────────────────────────────────────
st.markdown("""
<style>
.chat-wrap { display: flex; flex-direction: column; gap: 12px; padding: 8px 0; }

.bubble-user {
    align-self: flex-end;
    background: #4f46e5;
    color: #fff;
    padding: 10px 15px;
    border-radius: 18px 18px 4px 18px;
    max-width: 75%;
    font-size: 14px;
    line-height: 1.5;
}
.bubble-bot {
    align-self: flex-start;
    background: #1e1e2e;
    color: #e2e2f0;
    border: 1px solid #2e2e45;
    padding: 10px 15px;
    border-radius: 18px 18px 18px 4px;
    max-width: 80%;
    font-size: 14px;
    line-height: 1.6;
}
.bubble-label {
    font-size: 11px;
    color: #6b7280;
    margin-bottom: 2px;
}
.sources-box {
    margin-top: 8px;
    padding: 6px 10px;
    background: #111827;
    border-left: 3px solid #4f46e5;
    border-radius: 4px;
    font-size: 12px;
    color: #9ca3af;
}
.intent-chip {
    display: inline-block;
    background: #1e1e2e;
    border: 1px solid #3f3f60;
    color: #a5b4fc;
    font-size: 11px;
    padding: 2px 8px;
    border-radius: 99px;
    margin-bottom: 6px;
}
</style>
""", unsafe_allow_html=True)

# ── Header ─────────────────────────────────────────────────────────────────────
st.title("💬 AI Chat Assistant")
st.caption(
    "Ask about eligibility, ordinances, registration rules, or your courses. "
    "AI is used here to interpret your questions — not for data lookups."
)
st.divider()

# ── Session state ──────────────────────────────────────────────────────────────
if "chat_messages" not in st.session_state:
    st.session_state.chat_messages = []

# ── Render chat history ────────────────────────────────────────────────────────
chat_area = st.container()

with chat_area:
    if not st.session_state.chat_messages:
        st.markdown("""
        <div style="padding: 20px; background: #1e1e2e; border-radius: 12px; border: 1px solid #2e2e45;">
            <div style="font-size:15px; font-weight:600; color:#e2e2f0; margin-bottom:10px;">
                👋 Hi, I'm your AMU Registration Assistant
            </div>
            <div style="font-size:13px; color:#9ca3af; line-height:1.8;">
                I can help you with:<br>
                &nbsp;&nbsp;• Eligibility and promotion requirements<br>
                &nbsp;&nbsp;• AMU ordinance clauses and rules<br>
                &nbsp;&nbsp;• Registration modes (A / B / C)<br>
                &nbsp;&nbsp;• Course advancement criteria<br>
                &nbsp;&nbsp;• Backlog and credit queries
            </div>
        </div>
        """, unsafe_allow_html=True)
    else:
        html_parts = ['<div class="chat-wrap">']
        for msg in st.session_state.chat_messages:
            if msg["is_user"]:
                html_parts.append(f'''
                <div style="display:flex;flex-direction:column;align-items:flex-end;">
                    <div class="bubble-label">You</div>
                    <div class="bubble-user">{msg["content"]}</div>
                </div>''')
            else:
                sources_html = ""
                if msg.get("sources"):
                    src_list = "".join(f"<div>• {s}</div>" for s in msg["sources"])
                    sources_html = f'<div class="sources-box">📚 Sources:<br>{src_list}</div>'

                intent_html = ""
                if msg.get("intent"):
                    intent_html = f'<div class="intent-chip">#{msg["intent"]}</div><br>'

                content = msg["content"].replace("\n", "<br>")
                html_parts.append(f'''
                <div style="display:flex;flex-direction:column;align-items:flex-start;">
                    <div class="bubble-label">🤖 Assistant</div>
                    <div class="bubble-bot">{intent_html}{content}{sources_html}</div>
                </div>''')

        html_parts.append("</div>")
        st.markdown("".join(html_parts), unsafe_allow_html=True)

st.divider()

# ── Input row ──────────────────────────────────────────────────────────────────
col_input, col_send = st.columns([8, 1])

with col_input:
    user_input = st.text_input(
        "Message",
        key="chat_input",
        placeholder="e.g. What are the promotion rules for semester 4?",
        label_visibility="collapsed"
    )

with col_send:
    send = st.button("Send ➤", type="primary", use_container_width=True)

# ── Handle send ────────────────────────────────────────────────────────────────
if send and user_input.strip():
    st.session_state.chat_messages.append({
        "content": user_input.strip(),
        "is_user": True
    })

    with st.spinner("Thinking…"):
        resp = api_client.send_chat_message(student.get("id"), user_input.strip())

    if "error" in resp:
        bot_msg = {
            "content": f"Sorry, something went wrong: {resp['error']}",
            "is_user": False,
            "sources": [],
            "intent": None
        }
    else:
        bot_msg = {
            "content": resp.get("response", "I couldn't process that request."),
            "is_user": False,
            "sources": resp.get("sources", []),
            "intent": resp.get("intent")
        }

    st.session_state.chat_messages.append(bot_msg)
    st.rerun()

# ── Quick questions ────────────────────────────────────────────────────────────
st.markdown("**Quick questions:**")
q_cols = st.columns(4)
quick = [
    ("📋 Promotion rules", "What are the promotion requirements?"),
    ("🚀 Can I advance?", "Can I register for advanced courses?"),
    ("📖 Registration modes", "Explain registration modes A, B, and C"),
    ("⚠️ Backlog rules", "What happens if I fail a course?"),
]

for i, (label, question) in enumerate(quick):
    with q_cols[i]:
        if st.button(label, use_container_width=True, key=f"quick_{i}"):
            st.session_state.chat_messages.append({"content": question, "is_user": True})
            with st.spinner("Thinking…"):
                resp = api_client.send_chat_message(student.get("id"), question)
            bot_msg = {
                "content": resp.get("response", "Sorry, I couldn't process that."),
                "is_user": False,
                "sources": resp.get("sources", []),
                "intent": resp.get("intent")
            }
            st.session_state.chat_messages.append(bot_msg)
            st.rerun()

# ── Clear ──────────────────────────────────────────────────────────────────────
st.divider()
if st.button("🗑️ Clear chat", key="clear_chat"):
    st.session_state.chat_messages = []
    st.rerun()
