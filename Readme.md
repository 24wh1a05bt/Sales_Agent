# Lead Qualification & Outreach Agent (Streamlit)

A Streamlit implementation of the AI-powered Lead Qualification & Outreach Agent
described in the spec: enrich B2B leads, score them against an editable ICP,
classify as Hot / Nurture / Disqualified, draft personalized outreach emails,
and require human approval before anything is sent.

## Setup

```bash
pip install -r requirements.txt
cp .env.example .env   # optionally add your OPENAI_API_KEY
streamlit run app.py
```

The app creates a local SQLite database (`lead_agent.db`) on first run and
seeds three demo accounts:

| Role | Email | Password |
|---|---|---|
| SDR | sdr@demo.com | password123 |
| Sales Manager | manager@demo.com | password123 |
| Admin | admin@demo.com | password123 |

## AI mode vs demo mode

If no `OPENAI_API_KEY` is configured (env var, Streamlit secrets, or entered
by an Admin in Settings → AI Configuration), the app automatically falls
back to deterministic mock enrichment and templated email drafts, so the
full workflow is demoable with zero external dependencies. Add a real key
to switch on AI-assisted enrichment and GPT-generated outreach emails.

## File structure

```
app.py                     # Login + home dashboard
auth.py                    # Session-based auth / RBAC
database.py                # SQLite schema + all data access
scoring.py                 # ICP-based lead scoring & classification
enrichment.py              # Mock + AI-assisted lead enrichment
email_agent.py             # AI email drafting (+ template fallback)
ai_client.py                # Shared OpenAI client wrapper
utils.py                   # Fairness guardrails, badges
pages/
  1_Lead_Intake.py         # CSV/Excel upload, manual entry, API notes
  2_Lead_List.py           # Filter, bulk enrich + score
  3_Lead_Details.py        # Full profile, scoring breakdown, routing, draft
  4_Email_Approval.py      # Approve / Reject / Edit / Regenerate
  5_Analytics.py           # Evaluation metrics dashboard
  6_Audit_Logs.py          # Full audit trail
  7_Settings.py            # ICP config, AI key, users, fairness rules
```

## Notes on scope

This is a self-contained Streamlit app covering all functional modules
from the spec (intake, enrichment, ICP, scoring, classification, routing,
email generation, human approval, audit logs, analytics, RBAC). CRM
integrations (HubSpot/Salesforce/Zoho/Pipedrive) and a standalone FastAPI
backend are simulated in-app; wire real connectors in `database.py` /
a separate service for production use.