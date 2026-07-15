"""Module 10 - Audit Logs. Full transparency: timestamp, lead, prompt, response,
score, classification, approval status, edits. SDRs cannot delete audit logs."""

import pandas as pd
import streamlit as st

from auth import require_login
from database import get_audit_logs, get_leads

st.set_page_config(page_title="Audit Logs", page_icon="📜", layout="wide")
user = require_login()

st.title("📜 Audit Logs")
st.caption("Complete, append-only log of every AI decision and human action. "
           "SDRs can view but not delete audit logs (per role permissions).")

leads = get_leads()
lead_map = {l["id"]: f"#{l['id']} {l['name']} ({l['company']})" for l in leads}

col1, col2 = st.columns(2)
lead_filter = col1.selectbox("Filter by lead", ["All leads"] + list(lead_map.values()))
action_filter = col2.text_input("Filter by action keyword (e.g. 'Scored', 'Approved')")

lead_id = None
if lead_filter != "All leads":
    lead_id = [k for k, v in lead_map.items() if v == lead_filter][0]

logs = get_audit_logs(lead_id=lead_id)
if action_filter:
    logs = [l for l in logs if action_filter.lower() in (l["action"] or "").lower()]

st.write(f"**{len(logs)} log entries**")

if logs:
    df = pd.DataFrame(logs)
    df["lead"] = df["lead_id"].map(lambda i: lead_map.get(i, f"#{i}"))
    st.dataframe(
        df[["timestamp", "lead", "action", "actor", "reason", "response"]],
        use_container_width=True, hide_index=True,
    )

    if user["role"] == "Admin":
        csv = df.to_csv(index=False).encode()
        st.download_button("⬇️ Export audit log (CSV)", csv, "audit_log.csv", "text/csv")
else:
    st.info("No matching log entries.")