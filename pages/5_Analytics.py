"""Module 13 - Evaluation Metrics dashboard."""

import pandas as pd
import plotly.express as px
import streamlit as st

from auth import require_login
from database import get_leads, get_all_drafts

st.set_page_config(page_title="Analytics", page_icon="📊", layout="wide")
require_login()

st.title("📊 Analytics")

leads = get_leads()
drafts = get_all_drafts()

if not leads:
    st.info("No lead data yet.")
    st.stop()

df = pd.DataFrame(leads)

c1, c2, c3, c4 = st.columns(4)
c1.metric("Total Leads", len(df))
scored = df[df["classification"] != "Unscored"]
c2.metric("Scored Leads", len(scored))
avg_score = round(scored["score"].mean(), 1) if len(scored) else 0
c3.metric("Avg Lead Score", avg_score)

approved = [d for d in drafts if d["status"] in ("Approved", "Sent")]
total_reviewed = [d for d in drafts if d["status"] != "Pending Review"]
approval_rate = round(100 * len(approved) / len(total_reviewed), 1) if total_reviewed else 0
c4.metric("Human Approval Rate", f"{approval_rate}%")

st.divider()

col1, col2 = st.columns(2)
with col1:
    st.subheader("Classification distribution")
    class_counts = df["classification"].value_counts().reset_index()
    class_counts.columns = ["classification", "count"]
    fig = px.pie(class_counts, names="classification", values="count", hole=0.4,
                 color="classification",
                 color_discrete_map={"Hot": "#e74c3c", "Nurture": "#f1c40f",
                                      "Disqualified": "#bdc3c7", "Unscored": "#3498db"})
    st.plotly_chart(fig, use_container_width=True)

with col2:
    st.subheader("Score distribution")
    if len(scored):
        fig2 = px.histogram(scored, x="score", nbins=20)
        st.plotly_chart(fig2, use_container_width=True)
    else:
        st.info("No scored leads yet.")

st.divider()
st.subheader("Email draft outcomes")
if drafts:
    ddf = pd.DataFrame(drafts)
    status_counts = ddf["status"].value_counts().reset_index()
    status_counts.columns = ["status", "count"]
    fig3 = px.bar(status_counts, x="status", y="count", color="status")
    st.plotly_chart(fig3, use_container_width=True)
else:
    st.info("No email drafts generated yet.")

st.divider()
st.subheader("SQL conversion funnel (proxy)")
funnel_df = pd.DataFrame({
    "stage": ["Leads Received", "Enriched/Scored", "Hot", "Email Approved", "Email Sent"],
    "count": [
        len(df),
        len(scored),
        len(df[df["classification"] == "Hot"]),
        len([d for d in drafts if d["status"] in ("Approved", "Sent")]),
        len([d for d in drafts if d["status"] == "Sent"]),
    ],
})
fig4 = px.funnel(funnel_df, x="count", y="stage")
st.plotly_chart(fig4, use_container_width=True)

st.caption("Fairness Compliance: all scoring inputs are restricted to industry, revenue, company size, "
           "technology, buying intent, job role, and company growth — see Settings → Fairness & Governance.")