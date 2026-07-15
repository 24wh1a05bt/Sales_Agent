"""Lead Details: full profile, enrichment data, score breakdown, routing status, audit trail."""

import streamlit as st

from auth import require_login, current_user
from database import (get_leads, get_lead, get_enrichment, get_icp, update_lead,
                       upsert_enrichment, insert_email_draft, get_latest_draft,
                       get_audit_logs, log_action)
from enrichment import enrich_lead
from scoring import score_lead
from email_agent import generate_email
from utils import badge_color
from ai_client import get_api_key
from theme import inject_css

st.set_page_config(page_title="Lead Details", page_icon="🔍", layout="wide")
require_login()
user = current_user()
inject_css()

st.title("🔍 Lead Details")

leads = get_leads()
if not leads:
    st.info("No leads yet. Add one from Lead Intake.")
    st.stop()

default_id = st.session_state.get("selected_lead_id", leads[0]["id"])
id_options = {f"#{l['id']} — {l['name']} ({l['company']})": l["id"] for l in leads}
default_label = next((k for k, v in id_options.items() if v == default_id), list(id_options.keys())[0])
label = st.selectbox("Lead", list(id_options.keys()), index=list(id_options.keys()).index(default_label))
lead_id = id_options[label]
st.session_state["selected_lead_id"] = lead_id

lead = get_lead(lead_id)
enrichment = get_enrichment(lead_id)
icp = get_icp()

col1, col2 = st.columns([2, 1])
with col1:
    st.subheader(f"{lead['name']} — {lead['company']}")
    st.write(f"**Role:** {lead['role'] or '—'}  |  **Email:** {lead['email'] or '—'}  |  **Phone:** {lead['phone'] or '—'}")
    st.write(f"**Website:** {lead['website'] or '—'}  |  **Country:** {lead['country'] or '—'}")
    if lead["notes"]:
        st.write(f"**Notes:** {lead['notes']}")
with col2:
    cls = lead["classification"]
    st.metric("Score", lead["score"])
    st.markdown(f"### {badge_color(cls)} {cls}")
    st.caption(f"Status: {lead['status']}  |  Source: {lead['source']}")

st.divider()

t1, t2, t3, t4 = st.tabs(["🧬 Enrichment", "🎯 Scoring", "📬 Outreach", "📜 History"])

with t1:
    use_ai = bool(get_api_key())
    if st.button("Run enrichment" + (" (AI)" if use_ai else " (mock)")):
        data = enrich_lead(lead, use_ai=use_ai)
        upsert_enrichment(lead_id, data)
        log_action(lead_id, "Lead Enriched", response=str(data), actor=user["name"])
        st.rerun()

    if enrichment:
        c1, c2, c3 = st.columns(3)
        c1.write(f"**Industry:** {enrichment['industry']}")
        c1.write(f"**Company size:** {enrichment['company_size']}")
        c1.write(f"**Employees:** {enrichment['employee_count']}")
        c2.write(f"**Revenue:** {enrichment['revenue']}")
        c2.write(f"**Funding:** {enrichment['funding']}")
        c2.write(f"**Decision maker status:** {enrichment['decision_maker_status']}")
        c3.write(f"**Technology stack:** {enrichment['technology_stack']}")
        c3.write(f"**Buying signals:** {enrichment['buying_signals']}")
        c3.write(f"**LinkedIn:** {enrichment['linkedin']}")
    else:
        st.info("No enrichment data yet. Click 'Run enrichment' above.")

with t2:
    if st.button("Score this lead", disabled=(enrichment is None)):
        result = score_lead(lead, enrichment, icp)
        update_lead(lead_id, {
            "score": result["score"],
            "classification": result["classification"],
            "classification_reason": " | ".join(result["reasons"]),
            "status": "Scored",
        })
        log_action(lead_id, "Lead Scored", reason=result["reasons"][-1],
                   response=f"score={result['score']}", actor=user["name"])
        st.rerun()
    if enrichment is None:
        st.caption("Run enrichment first.")

    if lead["classification_reason"]:
        st.write("**Reasoning:**")
        for r in lead["classification_reason"].split(" | "):
            st.write(f"- {r}")

with t3:
    if lead["classification"] == "Hot":
        st.write("Routing: Lead → Email Draft → Human Approval → CRM → Email Sent")
        if st.button("✨ Draft outreach email", type="primary"):
            result = {"score": lead["score"], "classification": lead["classification"]}
            draft = generate_email(lead, enrichment or {}, result)
            insert_email_draft(lead_id, draft["subject"], draft["body"])
            log_action(lead_id, "Email Drafted", prompt=str(lead), response=str(draft), actor=user["name"])
            st.rerun()

        draft = get_latest_draft(lead_id)
        if draft:
            st.text_input("Subject", value=draft["subject"], disabled=True, key="preview_subject")
            st.text_area("Body", value=draft["body"], disabled=True, height=200, key="preview_body")
            st.caption(f"Status: {draft['status']}  |  Version: {draft['version']}")
            st.page_link("pages/4_Email_Approval.py", label="Go review this in Email Approval →")
    elif lead["classification"] == "Nurture":
        st.write("Routing: Lead → Marketing Sequence → CRM")
        st.info("This lead is enrolled in the nurture marketing sequence (simulated CRM sync).")
    elif lead["classification"] == "Disqualified":
        st.write("Routing: Lead → Archive → Reason Logged")
        st.warning(f"Disqualified reason: {lead['classification_reason']}")
    else:
        st.info("Score this lead to determine routing.")

with t4:
    logs = get_audit_logs(lead_id)
    if logs:
        for entry in logs:
            st.write(f"`{entry['timestamp']}` — **{entry['action']}** by {entry['actor']}")
            if entry["reason"]:
                st.caption(f"Reason: {entry['reason']}")
    else:
        st.info("No audit history for this lead yet.")