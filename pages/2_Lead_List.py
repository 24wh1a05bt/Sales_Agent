"""Lead List: view/filter leads, run enrichment + scoring + classification + routing."""

import pandas as pd
import streamlit as st

from auth import require_login, current_user
from database import get_leads, update_lead, upsert_enrichment, get_icp, log_action
from enrichment import enrich_lead
from scoring import score_lead
from utils import badge_color
from ai_client import get_api_key

st.set_page_config(page_title="Lead List", page_icon="📋", layout="wide")
require_login()
user = current_user()

st.title("📋 Lead List")

use_ai = bool(get_api_key())
st.caption(
    ("🤖 AI-assisted enrichment is ACTIVE (OpenAI key detected)." if use_ai
     else "🧪 Running in demo mode with mock enrichment (no OpenAI key configured — see ⚙️ Settings).")
)

f1, f2, f3 = st.columns(3)
status_filter = f1.selectbox("Status", ["All", "New", "Enriched", "Scored", "Archived"])
class_filter = f2.selectbox("Classification", ["All", "Unscored", "Hot", "Nurture", "Disqualified"])
search = f3.text_input("Search company / name")

leads = get_leads(
    status=None if status_filter == "All" else status_filter,
    classification=None if class_filter == "All" else class_filter,
)
if search:
    s = search.lower()
    leads = [l for l in leads if s in (l["name"] or "").lower() or s in (l["company"] or "").lower()]

st.write(f"**{len(leads)} lead(s)**")

bulk_col1, bulk_col2 = st.columns([1, 3])
with bulk_col1:
    run_bulk = st.button("⚙️ Enrich + Score all unscored", type="primary")

if run_bulk:
    icp = get_icp()
    targets = [l for l in leads if l["classification"] == "Unscored"]
    progress = st.progress(0.0, text="Processing leads...")
    for i, lead in enumerate(targets):
        enrichment = enrich_lead(lead, use_ai=use_ai)
        upsert_enrichment(lead["id"], enrichment)
        log_action(lead["id"], "Lead Enriched", prompt=str(lead), response=str(enrichment), actor=user["name"])

        result = score_lead(lead, enrichment, icp)
        update_lead(lead["id"], {
            "score": result["score"],
            "classification": result["classification"],
            "classification_reason": " | ".join(result["reasons"]),
            "status": "Scored",
        })
        log_action(
            lead["id"], "Lead Scored",
            reason=result["reasons"][-1],
            response=f"score={result['score']} class={result['classification']}",
            actor=user["name"],
        )
        progress.progress((i + 1) / max(len(targets), 1), text=f"Processed {lead['company']}")
    st.success(f"Enriched and scored {len(targets)} lead(s).")
    st.rerun()

if leads:
    df = pd.DataFrame(leads)
    df["classification"] = df["classification"].apply(lambda c: f"{badge_color(c)} {c}")
    st.dataframe(
        df[["id", "name", "company", "role", "email", "score", "classification", "status", "source"]],
        use_container_width=True, hide_index=True,
    )

    st.divider()
    st.subheader("Open a lead")
    options = {f"#{l['id']} — {l['name']} ({l['company']})": l["id"] for l in leads}
    choice = st.selectbox("Select a lead to view details", list(options.keys()))
    if st.button("View lead details"):
        st.session_state["selected_lead_id"] = options[choice]
        st.switch_page("pages/3_Lead_Details.py")
else:
    st.info("No leads match these filters.")