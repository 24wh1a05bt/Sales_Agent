"""Settings: Module 3 (ICP - editable by Sales Manager/Admin), Admin API key
configuration, user list, and Module 11 fairness & governance rules (read-only)."""

import streamlit as st

from auth import require_login
from database import get_icp, update_icp, get_all_users
from utils import PROTECTED_FIELDS
from theme import inject_css

st.set_page_config(page_title="Settings", page_icon="⚙️", layout="wide")
user = require_login()
inject_css()

st.title("⚙️ Settings")

tab_icp, tab_ai, tab_users, tab_fairness = st.tabs(
    ["🎯 ICP Settings", "🤖 AI Configuration", "👥 Users", "⚖️ Fairness & Governance"]
)

with tab_icp:
    if user["role"] not in ("Sales Manager", "Admin"):
        st.info("Only Sales Managers and Admins can modify the Ideal Customer Profile. "
                "You can view the current settings below.")

    icp = get_icp()
    editable = user["role"] in ("Sales Manager", "Admin")

    industries = st.text_input("Target industries (comma-separated)",
                                value=", ".join(icp["industry_targets"]), disabled=not editable)
    c1, c2 = st.columns(2)
    rev_min = c1.number_input("Revenue min ($)", value=int(icp["revenue_min"]), step=100_000, disabled=not editable)
    rev_max = c2.number_input("Revenue max ($)", value=int(icp["revenue_max"]), step=100_000, disabled=not editable)
    emp_min = c1.number_input("Employee count min", value=int(icp["employee_min"]), step=10, disabled=not editable)
    emp_max = c2.number_input("Employee count max", value=int(icp["employee_max"]), step=10, disabled=not editable)
    job_titles = st.text_input("Target job titles (comma-separated)",
                                value=", ".join(icp["job_titles"]), disabled=not editable)
    intent_keywords = st.text_input("Buying intent keywords (comma-separated)",
                                     value=", ".join(icp["buying_intent_keywords"]), disabled=not editable)
    growth = st.text_input("Company growth stage", value=icp["company_growth"], disabled=not editable)

    st.write("**Scoring weights** (should total 100)")
    w = icp["weights"]
    wc = st.columns(6)
    weights = {}
    labels = [("industry_match", "Industry"), ("decision_maker", "Decision Maker"),
              ("buying_intent", "Buying Intent"), ("revenue", "Revenue"),
              ("company_size", "Company Size"), ("technology_match", "Technology")]
    for i, (key, label) in enumerate(labels):
        weights[key] = wc[i].number_input(label, value=int(w.get(key, 0)), min_value=0, max_value=100,
                                           disabled=not editable, key=f"w_{key}")

    if editable and st.button("Save ICP settings", type="primary"):
        if sum(weights.values()) != 100:
            st.warning(f"Weights currently total {sum(weights.values())}, not 100. Saved anyway — "
                       "scores will be scaled to the 0-100 range regardless.")
        update_icp({
            "industry_targets": [x.strip() for x in industries.split(",") if x.strip()],
            "revenue_min": rev_min, "revenue_max": rev_max,
            "employee_min": emp_min, "employee_max": emp_max,
            "job_titles": [x.strip() for x in job_titles.split(",") if x.strip()],
            "buying_intent_keywords": [x.strip() for x in intent_keywords.split(",") if x.strip()],
            "company_growth": growth,
            "weights": weights,
        })
        st.success("ICP settings saved.")
        st.rerun()

with tab_ai:
    if user["role"] != "Admin":
        st.info("Only Admins can configure API keys.")
    else:
        st.write("Configure the OpenAI API key used for AI-assisted enrichment and email generation. "
                 "If left blank, the app runs in deterministic demo/mock mode.")
        current_key = st.session_state.get("openai_api_key", "")
        new_key = st.text_input("OpenAI API key", value=current_key, type="password",
                                 help="Stored only in this browser session. For production, set the "
                                      "OPENAI_API_KEY environment variable or Streamlit secrets instead.")
        if st.button("Save key for this session"):
            st.session_state["openai_api_key"] = new_key
            st.success("Key saved for this session.")
        st.caption("Preferred for deployment: add `OPENAI_API_KEY` to `.streamlit/secrets.toml` "
                   "or as an environment variable — see .env.example.")

with tab_users:
    if user["role"] != "Admin":
        st.info("Only Admins can manage users.")
    else:
        users = get_all_users()
        st.dataframe(users, use_container_width=True, hide_index=True)
        st.caption("Full user management (add/remove/reset password) belongs in the FastAPI backend "
                   "with POST /register per the spec's API endpoints (Module 9).")

with tab_fairness:
    st.subheader("Module 11 — Fairness & Governance")
    st.error("The AI must **never** use the following as scoring or enrichment inputs:")
    st.write(", ".join(sorted(f.capitalize() for f in PROTECTED_FIELDS)))
    st.success("Allowed inputs: Industry, Revenue, Company Size, Technology, Buying Intent, "
               "Job Role, Company Growth.")
    st.info("This is enforced in code by `utils.assert_no_protected_fields()`, which every scoring "
            "call passes through before computing a score. Every classification includes a "
            "human-readable business reason (see Lead Details → Scoring tab).")