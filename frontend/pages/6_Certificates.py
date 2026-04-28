"""
Certificates Page
Upload & extract certificate information using AI
Mirrors the standalone CertExtract tool, integrated into the registration system.
"""

import streamlit as st
import requests
import json
from utils.session import init_session, get_student, is_logged_in
from utils.ui import load_css
from components.sidebar import render_sidebar

# ── Page config ────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Certificates - AMU Registration",
    page_icon="🏅",
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
student_id = student.get("id")

CERT_API = "http://localhost:8001"
MAIN_API = "http://localhost:8000"

# ── Helpers ────────────────────────────────────────────────────────────────────

def cert_api_online() -> bool:
    try:
        r = requests.get(f"{CERT_API}/health", timeout=3)
        return r.status_code == 200
    except Exception:
        return False


def upload_certificate(file_bytes: bytes, filename: str, mime_type: str):
    """POST to cert service /extract then persist via main backend."""
    try:
        r = requests.post(
            f"{CERT_API}/extract",
            files={"file": (filename, file_bytes, mime_type)},
            timeout=60,
        )
        r.raise_for_status()
        cert_data = r.json()
    except requests.exceptions.ConnectionError:
        return None, "Certificate service is offline. Start it on port 8001."
    except requests.exceptions.HTTPError as e:
        return None, f"Service error: {e.response.text}"
    except Exception as e:
        return None, str(e)

    # Also persist to main backend DB (links cert to this student)
    try:
        requests.post(
            f"{MAIN_API}/api/certificates/upload",
            params={"student_id": student_id},
            files={"file": (filename, file_bytes, mime_type)},
            timeout=60,
        )
    except Exception:
        pass  # best-effort persistence; cert data already extracted

    return cert_data, None


def fetch_student_certificates():
    try:
        r = requests.get(f"{MAIN_API}/api/certificates/{student_id}", timeout=5)
        r.raise_for_status()
        return r.json().get("certificates", [])
    except Exception:
        return []


def get_mime(filename: str, content_type: str) -> str:
    ext_map = {
        ".jpg": "image/jpeg", ".jpeg": "image/jpeg",
        ".png": "image/png", ".webp": "image/webp",
        ".pdf": "application/pdf",
    }
    from pathlib import Path
    return ext_map.get(Path(filename).suffix.lower(), content_type)


def category_chip(label: str, chip_type: str = "default") -> str:
    colors = {
        "tech":   ("#1e1a36", "#a89af8", "#3d3575"),
        "acad":   ("#101e34", "#74aef5", "#1e3d6e"),
        "sports": ("#0e2218", "#5fcb8a", "#1a4a30"),
        "arts":   ("#2a1229", "#e08cd4", "#5a2a58"),
        "biz":    ("#271c08", "#e8a94a", "#5a3f10"),
        "social": ("#0d2424", "#4ec9c9", "#1a4e4e"),
        "default":("#22222a", "#9090a8", "#3a3a48"),
    }
    bg, text, border = colors.get(chip_type, colors["default"])
    return f'<span style="background:{bg};color:{text};border:1px solid {border};padding:2px 8px;border-radius:99px;font-size:11px;margin:2px;display:inline-block">{label}</span>'


def cert_type_color(ctype: str) -> str:
    return {
        "winner": "🥇", "winner_1st": "🥇",
        "runner_up": "🥈",
        "achievement": "🏆",
        "completion": "📜", "certification_completion": "📜",
        "participation": "🎫",
        "appreciation": "🌟",
        "scholarship": "💰",
    }.get((ctype or "").lower(), "📋")


# ── Page header ────────────────────────────────────────────────────────────────
st.title("🏅 Certificate Upload & Extraction")
st.markdown("Upload your certificates for AI-powered extraction and classification.")

# API status badge
online = cert_api_online()
if online:
    st.success("✅ Certificate AI service is online", icon="🟢")
else:
    st.error(
        "❌ Certificate AI service offline — start it with: `uvicorn main:app --port 8001`",
        icon="🔴"
    )

st.markdown("---")

# ── Tabs ───────────────────────────────────────────────────────────────────────
tab_upload, tab_bulk, tab_records = st.tabs([
    "📤 Upload Single", "📦 Bulk Upload", "📋 My Certificates"
])

# ══════════════════════════════════════════════════════════════════════════════
# TAB 1 — Single Upload
# ══════════════════════════════════════════════════════════════════════════════
with tab_upload:
    col_form, col_info = st.columns([3, 2], gap="large")

    with col_form:
        st.markdown("### 📤 Upload Certificate")
        uploaded = st.file_uploader(
            "Choose a certificate file",
            type=["pdf", "jpg", "jpeg", "png", "webp"],
            key="single_upload",
            help="PDF or image of your certificate",
        )

        if uploaded:
            # Preview
            if uploaded.type != "application/pdf":
                st.image(uploaded, caption=uploaded.name, use_column_width=True)
            else:
                st.info(f"📄 PDF ready: **{uploaded.name}** ({uploaded.size/1024:.1f} KB)")

            st.markdown("")
            if st.button("🚀 Extract with AI", type="primary", use_container_width=True, disabled=not online):
                file_bytes = uploaded.read()
                mime = get_mime(uploaded.name, uploaded.type)

                with st.spinner("🤖 Analysing certificate with Gemini AI..."):
                    result, err = upload_certificate(file_bytes, uploaded.name, mime)

                if err:
                    st.error(f"❌ {err}")
                elif result:
                    st.session_state["last_cert_result"] = result
                    st.success("✅ Certificate extracted successfully!")

    with col_info:
        st.markdown("### ℹ️ What gets extracted")
        st.markdown("""
        - 👤 **Student name** on certificate
        - 🏢 **Issuing organisation**
        - 📌 **Event / course name**
        - 📅 **Event & issue dates**
        - ⏱️ **Duration**
        - 🏷️ **Primary category**
        - 🔖 **AI-generated tags**
        - 🗂️ **Multi-label classification** (80+ categories)
        - 📊 **Confidence score**
        """)
        st.info("Supported: **PDF, JPG, PNG, WEBP**")

    # Result card
    if "last_cert_result" in st.session_state:
        r = st.session_state["last_cert_result"]
        st.markdown("---")
        st.markdown("### 📊 Extracted Data")

        c1, c2, c3 = st.columns(3)
        c1.metric("Certificate Type", f"{cert_type_color(r.get('certificate_type',''))} {r.get('certificate_type','—')}")
        c2.metric("Confidence", f"{float(r.get('confidence_score') or 0):.0%}")
        c3.metric("Category", r.get("primary_category") or "—")

        st.markdown("")
        col_l, col_r = st.columns(2)
        with col_l:
            st.markdown(f"**👤 Recipient:** {r.get('student_name') or '—'}")
            st.markdown(f"**🏢 Organisation:** {r.get('organisation') or '—'}")
            st.markdown(f"**📌 Event:** {r.get('event_name') or '—'}")
        with col_r:
            st.markdown(f"**📅 Event Date:** {r.get('event_date') or '—'}")
            st.markdown(f"**📋 Issue Date:** {r.get('issue_date') or '—'}")
            st.markdown(f"**⏱️ Duration:** {r.get('duration') or '—'}")

        if r.get("description"):
            st.markdown(f"**📝 Description:** {r['description']}")

        if r.get("suggested_tags"):
            tags_html = " ".join(category_chip(t, "acad") for t in r["suggested_tags"])
            st.markdown(f"**🔖 Tags:** {tags_html}", unsafe_allow_html=True)

        # Category labels grid
        cat_labels = r.get("category_labels") or {}
        active_cats = [k.replace("cat_", "").replace("_", " ").title()
                       for k, v in cat_labels.items() if v == 1]
        if active_cats:
            st.markdown("**🗂️ Matched Categories:**")
            chips_html = " ".join(category_chip(c, "tech") for c in active_cats)
            st.markdown(chips_html, unsafe_allow_html=True)

        if st.button("🗑️ Clear Result", key="clear_single"):
            del st.session_state["last_cert_result"]
            st.rerun()


# ══════════════════════════════════════════════════════════════════════════════
# TAB 2 — Bulk Upload
# ══════════════════════════════════════════════════════════════════════════════
with tab_bulk:
    st.markdown("### 📦 Bulk Certificate Upload")
    st.markdown("Upload multiple certificates at once — all processed in one go.")

    bulk_files = st.file_uploader(
        "Choose certificates",
        type=["pdf", "jpg", "jpeg", "png", "webp"],
        accept_multiple_files=True,
        key="bulk_upload",
    )

    if bulk_files:
        st.markdown(f"**{len(bulk_files)} file(s) selected:**")
        for f in bulk_files:
            st.markdown(f"  • `{f.name}` — {f.size/1024:.1f} KB")

        st.markdown("")
        if st.button("🚀 Extract All", type="primary", disabled=not online):
            results = []
            progress = st.progress(0, text="Starting...")

            for i, f in enumerate(bulk_files):
                progress.progress((i) / len(bulk_files), text=f"Processing {f.name}…")
                file_bytes = f.read()
                mime = get_mime(f.name, f.type)
                cert, err = upload_certificate(file_bytes, f.name, mime)
                results.append({"file": f.name, "cert": cert, "error": err})

            progress.progress(1.0, text="Done!")
            st.session_state["bulk_results"] = results

    if "bulk_results" in st.session_state:
        st.markdown("---")
        results = st.session_state["bulk_results"]
        ok = [r for r in results if r["cert"]]
        fail = [r for r in results if r["error"]]

        c1, c2, c3 = st.columns(3)
        c1.metric("Total", len(results))
        c2.metric("✅ Success", len(ok))
        c3.metric("❌ Failed", len(fail))

        if ok:
            st.markdown("#### ✅ Successfully Extracted")
            for item in ok:
                cert = item["cert"]
                with st.expander(f"🏅 {item['file']} — {cert.get('primary_category','?')}"):
                    col_l, col_r = st.columns(2)
                    with col_l:
                        st.markdown(f"**Recipient:** {cert.get('student_name') or '—'}")
                        st.markdown(f"**Organisation:** {cert.get('organisation') or '—'}")
                        st.markdown(f"**Event:** {cert.get('event_name') or '—'}")
                    with col_r:
                        st.markdown(f"**Type:** {cert.get('certificate_type') or '—'}")
                        st.markdown(f"**Confidence:** {float(cert.get('confidence_score') or 0):.0%}")
                    if cert.get("suggested_tags"):
                        tags_html = " ".join(category_chip(t, "acad") for t in cert["suggested_tags"])
                        st.markdown(tags_html, unsafe_allow_html=True)

        if fail:
            st.markdown("#### ❌ Failed")
            for item in fail:
                st.error(f"`{item['file']}` — {item['error']}")

        if st.button("🗑️ Clear Bulk Results", key="clear_bulk"):
            del st.session_state["bulk_results"]
            st.rerun()


# ══════════════════════════════════════════════════════════════════════════════
# TAB 3 — My Certificates (from DB)
# ══════════════════════════════════════════════════════════════════════════════
with tab_records:
    st.markdown("### 📋 My Uploaded Certificates")

    if st.button("🔄 Refresh", key="refresh_certs"):
        st.rerun()

    certs = fetch_student_certificates()

    if not certs:
        st.info("No certificates uploaded yet. Use the Upload tabs to add some.")
    else:
        st.markdown(f"**{len(certs)} certificate(s) on record**")
        st.markdown("")

        for cert in certs:
            ctype = cert.get("certificate_type") or "other"
            icon = cert_type_color(ctype)
            label = cert.get("event_name") or cert.get("filename") or "Certificate"

            with st.expander(f"{icon} {label} — {cert.get('primary_category','?')}"):
                c1, c2, c3 = st.columns(3)
                c1.metric("Type", ctype.replace("_", " ").title())
                c2.metric("Confidence", f"{float(cert.get('confidence_score') or 0):.0%}")
                c3.metric("Uploaded", (cert.get("uploaded_at") or "")[:10])

                col_l, col_r = st.columns(2)
                with col_l:
                    st.markdown(f"**👤 Name on cert:** {cert.get('student_name_on_cert') or '—'}")
                    st.markdown(f"**🏢 Organisation:** {cert.get('organisation') or '—'}")
                    st.markdown(f"**📌 Event:** {cert.get('event_name') or '—'}")
                with col_r:
                    st.markdown(f"**📅 Event Date:** {cert.get('event_date') or '—'}")
                    st.markdown(f"**📋 Issue Date:** {cert.get('issue_date') or '—'}")
                    st.markdown(f"**⏱️ Duration:** {cert.get('duration') or '—'}")

                if cert.get("description"):
                    st.markdown(f"**📝** {cert['description']}")

                tags = cert.get("suggested_tags") or []
                if tags:
                    tags_html = " ".join(category_chip(t, "acad") for t in tags)
                    st.markdown(f"**🔖 Tags:** {tags_html}", unsafe_allow_html=True)

                cat_labels = cert.get("category_labels") or {}
                active_cats = [k.replace("cat_", "").replace("_", " ").title()
                               for k, v in cat_labels.items() if v == 1]
                if active_cats:
                    chips_html = " ".join(category_chip(c, "tech") for c in active_cats)
                    st.markdown(f"**🗂️ Categories:** {chips_html}", unsafe_allow_html=True)

# ── Footer ─────────────────────────────────────────────────────────────────────
st.markdown("---")
st.caption("🔒 Certificates are processed securely and linked to your student profile.")
