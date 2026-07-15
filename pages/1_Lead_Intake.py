"""Module 1 - Lead Intake: CSV Upload, Excel Upload, Manual Entry, API."""

import pandas as pd
import streamlit as st

from auth import require_login, current_user
from database import insert_lead, log_action

st.set_page_config(page_title="Lead Intake", page_icon="📥", layout="wide")
require_login()
user = current_user()

st.title("📥 Lead Intake")
st.caption("Accept leads from CSV, Excel, manual entry, or the API.")

FIELDS = ["name", "company", "email", "phone", "role", "website", "country", "notes"]

tab_upload, tab_manual, tab_api = st.tabs(["📄 CSV / Excel Upload", "✍️ Manual Entry", "🔌 API"])

with tab_upload:
    st.write("Upload a CSV or Excel file. Expected columns: " + ", ".join(FIELDS))
    file = st.file_uploader("Choose file", type=["csv", "xlsx", "xls"])
    if file:
        try:
            df = pd.read_csv(file) if file.name.endswith(".csv") else pd.read_excel(file)
        except Exception as e:
            st.error(f"Could not read file: {e}")
            df = None

        if df is not None:
            df.columns = [c.strip().lower() for c in df.columns]
            missing = [f for f in FIELDS if f not in df.columns]
            if missing:
                st.warning(f"Missing columns will be left blank: {', '.join(missing)}")
                for m in missing:
                    df[m] = ""

            st.dataframe(df[FIELDS], use_container_width=True, hide_index=True)

            if st.button("Import all rows", type="primary"):
                count = 0
                source = "CSV Upload" if file.name.endswith(".csv") else "Excel Upload"
                for _, row in df.iterrows():
                    data = {f: (str(row[f]) if pd.notna(row[f]) else "") for f in FIELDS}
                    if not data.get("name") and not data.get("company"):
                        continue
                    lead_id = insert_lead(data, source=source)
                    log_action(lead_id, "Lead Imported", reason=f"Imported via {source}", actor=user["name"])
                    count += 1
                st.success(f"Imported {count} leads.")

with tab_manual:
    with st.form("manual_lead_form", clear_on_submit=True):
        c1, c2 = st.columns(2)
        name = c1.text_input("Name*")
        company = c2.text_input("Company*")
        email = c1.text_input("Email")
        phone = c2.text_input("Phone")
        role = c1.text_input("Role / Job Title")
        website = c2.text_input("Website")
        country = c1.text_input("Country")
        notes = st.text_area("Notes")

        submitted = st.form_submit_button("Add lead", type="primary")
        if submitted:
            if not name or not company:
                st.error("Name and Company are required.")
            else:
                data = {"name": name, "company": company, "email": email, "phone": phone,
                        "role": role, "website": website, "country": country, "notes": notes}
                lead_id = insert_lead(data, source="Manual Entry")
                log_action(lead_id, "Lead Created", reason="Manual entry", actor=user["name"])
                st.success(f"Lead #{lead_id} added for {company}.")

with tab_api:
    st.write("Leads can also be pushed programmatically via the API endpoint:")
    st.code("POST /lead\nContent-Type: application/json\n\n"
            '{\n  "name": "Jane Doe",\n  "company": "Acme Inc",\n  "email": "jane@acme.com",\n'
            '  "phone": "+1 555 0100",\n  "role": "VP Sales",\n  "website": "acme.com",\n'
            '  "country": "USA",\n  "notes": "Inbound demo request"\n}', language="http")
    st.info("This Streamlit app is the operator UI. Wire the FastAPI backend described in "
            "the spec (Module 9 - API Endpoints) to POST leads directly into this same database "
            "for a true webhook/API intake path.")