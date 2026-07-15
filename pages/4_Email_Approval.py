"""Module 8 - Human Approval: Approve, Reject, Edit, Regenerate. No email is ever auto-sent."""

import streamlit as st

from auth import require_login, current_user
from database import get_all_drafts, get_lead, get_enrichment, update_draft, log_action, insert_email_draft
from email_agent import generate_email

st.set_page_config(page_title="Email Approval", page_icon="✉️", layout="wide")
require_login()
user = current_user()

st.title("✉️ Email Approval")
st.caption("No email is ever sent automatically. Every AI draft requires human approval.")

status_filter = st.selectbox("Filter", ["Pending Review", "Approved", "Rejected", "Sent", "All"])
drafts = get_all_drafts(status=None if status_filter == "All" else status_filter)

if not drafts:
    st.info("No email drafts in this filter.")
    st.stop()

for draft in drafts:
    lead = get_lead(draft["lead_id"])
    with st.expander(f"#{draft['id']} — {draft['subject']}  |  {lead['company']} ({lead['name']})  |  {draft['status']}"):
        st.write(f"**To:** {lead['email']}  |  **Role:** {lead['role']}  |  **Score:** {lead['score']} ({lead['classification']})")

        subject_key = f"subject_{draft['id']}"
        body_key = f"body_{draft['id']}"
        subject = st.text_input("Subject", value=draft["subject"], key=subject_key)
        body = st.text_area("Body", value=draft["body"], height=220, key=body_key)

        c1, c2, c3, c4 = st.columns(4)
        if c1.button("✅ Approve", key=f"approve_{draft['id']}", type="primary", disabled=draft["status"] != "Pending Review"):
            update_draft(draft["id"], {"subject": subject, "body": body, "approved": 1,
                                        "approved_by": user["name"], "status": "Approved"})
            log_action(draft["lead_id"], "Email Approved", actor=user["name"],
                       response=f"draft_id={draft['id']}")
            st.success("Approved. Draft is queued for CRM update + sending.")
            st.rerun()

        if c2.button("❌ Reject", key=f"reject_{draft['id']}", disabled=draft["status"] != "Pending Review"):
            update_draft(draft["id"], {"status": "Rejected"})
            log_action(draft["lead_id"], "Email Rejected", actor=user["name"], response=f"draft_id={draft['id']}")
            st.warning("Draft rejected.")
            st.rerun()

        if c3.button("💾 Save edits", key=f"save_{draft['id']}"):
            update_draft(draft["id"], {"subject": subject, "body": body, "status": draft["status"]})
            log_action(draft["lead_id"], "Email Edited", actor=user["name"], response=f"draft_id={draft['id']}")
            st.success("Edits saved.")
            st.rerun()

        if c4.button("🔄 Regenerate", key=f"regen_{draft['id']}"):
            enrichment = get_enrichment(draft["lead_id"]) or {}
            new_draft = generate_email(lead, enrichment, {"score": lead["score"], "classification": lead["classification"]})
            insert_email_draft(draft["lead_id"], new_draft["subject"], new_draft["body"])
            log_action(draft["lead_id"], "Email Regenerated", actor=user["name"], response=str(new_draft))
            st.success("New version generated.")
            st.rerun()

        if draft["status"] == "Approved":
            st.info(f"Approved by {draft['approved_by']}. This would sync to CRM and send via the backend "
                    "(POST /lead/{id}/send) in the full FastAPI deployment.")
            if st.button("📤 Mark as Sent (simulate CRM + send)", key=f"send_{draft['id']}"):
                update_draft(draft["id"], {"status": "Sent"})
                log_action(draft["lead_id"], "Email Sent", actor=user["name"], response=f"draft_id={draft['id']}")
                st.rerun()