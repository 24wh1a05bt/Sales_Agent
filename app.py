"""
app.py
Main entry point for the Lead Qualification & Outreach Agent (Streamlit).

Run with:  streamlit run app.py

Other pages live in pages/ and are auto-discovered by Streamlit's
built-in multipage navigation.
"""

import streamlit as st

from database import init_db, get_leads
from auth import login, logout, current_user
from theme import inject_css

st.set_page_config(page_title="Lead Qualification & Outreach Agent", page_icon="🎯", layout="wide")

init_db()
inject_css()


def render_login():
    st.title("🎯 Lead Qualification & Outreach Agent")
    st.caption("AI-powered B2B lead scoring, classification, and outreach — with a human always in the loop.")

    with st.form("login_form"):
        st.subheader("Sign in")
        email = st.text_input("Email", placeholder="sdr@demo.com")
        password = st.text_input("Password", type="password", placeholder="password123")
        submitted = st.form_submit_button("Log in", use_container_width=True)
        if submitted:
            if login(email, password):
                st.success("Logged in successfully.")
                st.rerun()
            else:
                st.error("Invalid email or password.")

    with st.expander("Demo accounts"):
        st.markdown(
            """
            | Role | Email | Password |
            |---|---|---|
            | SDR | sdr@demo.com | password123 |
            | Sales Manager | manager@demo.com | password123 |
            | Admin | admin@demo.com | password123 |
            """
        )


def render_dashboard():
    user = current_user()
    st.title("🎯 Lead Qualification & Outreach Agent")

    with st.sidebar:
        st.markdown(f"**{user['name']}**  \n`{user['role']}`")
        if st.button("Log out", use_container_width=True):
            logout()
            st.rerun()
        st.divider()
        st.page_link("app.py", label="🏠 Home")
        st.page_link("pages/1_Lead_Intake.py", label="📥 Lead Intake")
        st.page_link("pages/2_Lead_List.py", label="📋 Lead List")
        st.page_link("pages/3_Lead_Details.py", label="🔍 Lead Details")
        st.page_link("pages/4_Email_Approval.py", label="✉️ Email Approval")
        st.page_link("pages/5_Analytics.py", label="📊 Analytics")
        st.page_link("pages/6_Audit_Logs.py", label="📜 Audit Logs")
        st.page_link("pages/7_Settings.py", label="⚙️ Settings")

    leads = get_leads()
    hot = [l for l in leads if l["classification"] == "Hot"]
    nurture = [l for l in leads if l["classification"] == "Nurture"]
    disq = [l for l in leads if l["classification"] == "Disqualified"]
    unscored = [l for l in leads if l["classification"] == "Unscored"]

    c1, c2, c3, c4, c5 = st.columns(5)
    c1.metric("Total Leads", len(leads))
    c2.metric("🔴 Hot", len(hot))
    c3.metric("🟡 Nurture", len(nurture))
    c4.metric("⚪ Disqualified", len(disq))
    c5.metric("🔵 Unscored", len(unscored))

    st.divider()
    st.subheader("Quick actions")
    q1, q2, q3 = st.columns(3)
    with q1:
        st.markdown("**📥 Add leads**")
        st.write("Upload a CSV/Excel file or enter leads manually.")
        st.page_link("pages/1_Lead_Intake.py", label="Go to Lead Intake →")
    with q2:
        st.markdown("**✉️ Review AI drafts**")
        st.write("Approve, reject, edit, or regenerate outreach emails.")
        st.page_link("pages/4_Email_Approval.py", label="Go to Email Approval →")
    with q3:
        st.markdown("**📊 View performance**")
        st.write("Track conversion, approval rate, and fairness compliance.")
        st.page_link("pages/5_Analytics.py", label="Go to Analytics →")

    if leads:
        st.divider()
        st.subheader("Recently added leads")
        import pandas as pd

        df = pd.DataFrame(leads)[["id", "name", "company", "role", "score", "classification", "status", "created_at"]].head(10)
        st.dataframe(df, use_container_width=True, hide_index=True)
    else:
        st.info("No leads yet. Head to **Lead Intake** to add your first lead.")


if current_user():
    render_dashboard()
else:
    render_login()