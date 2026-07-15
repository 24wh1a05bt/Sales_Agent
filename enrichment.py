"""
enrichment.py
Module 2 - Lead Enrichment.

In production this would call a real data provider (Clearbit, Apollo,
ZoomInfo, etc). Since no such API key is configured by default, this
module ships a deterministic mock enrichment engine, and an optional
AI-assisted path that uses the OpenAI API (via ai_client) to infer
plausible firmographic data from the lead's company/website/notes when
an API key IS configured. This keeps the app fully runnable offline
while still demonstrating the intended AI workflow.
"""

import hashlib
import json
import random

from ai_client import get_client, MODEL

INDUSTRIES = ["Software", "SaaS", "Fintech", "E-commerce", "Healthcare",
              "Manufacturing", "Education", "Logistics", "Media", "Retail"]
TECH_STACKS = ["React/Node", "AWS + Kubernetes", "Salesforce", "Shopify",
               "HubSpot", "Django/Postgres", "Snowflake", "Azure"]
SIGNALS = ["Recently raised funding", "Hiring sales team", "Launched new product",
           "Expanding to new region", "Posted RFP for vendor", "No recent signal"]


def _seeded_random(seed_str: str) -> random.Random:
    """Deterministic pseudo-randomness per lead so re-runs are stable."""
    seed = int(hashlib.sha256(seed_str.encode()).hexdigest(), 16) % (10 ** 8)
    return random.Random(seed)


def mock_enrich(lead: dict) -> dict:
    rnd = _seeded_random(f"{lead.get('company')}-{lead.get('email')}")
    return {
        "industry": rnd.choice(INDUSTRIES),
        "company_size": rnd.choice(["1-10", "11-50", "51-200", "201-1000", "1000+"]),
        "revenue": rnd.choice(["<$1M", "$1M-$10M", "$10M-$50M", "$50M-$500M", "$500M+"]),
        "employee_count": rnd.choice([8, 35, 120, 450, 2000]),
        "linkedin": f"linkedin.com/company/{(lead.get('company') or 'company').lower().replace(' ', '-')}",
        "technology_stack": rnd.choice(TECH_STACKS),
        "funding": rnd.choice(["Bootstrapped", "Seed", "Series A", "Series B+", "Public"]),
        "buying_signals": rnd.choice(SIGNALS),
        "decision_maker_status": "Decision Maker" if any(
            t in (lead.get("role") or "").lower()
            for t in ["ceo", "cto", "vp", "head", "founder", "director"]
        ) else "Influencer",
    }


def ai_enrich(lead: dict) -> dict:
    """Use the AI model to infer enrichment fields when a real key is present.
    Falls back to mock_enrich on any failure."""
    client = get_client()
    if client is None:
        return mock_enrich(lead)

    prompt = f"""You are a B2B lead enrichment engine. Given this lead, infer plausible
firmographic data. Respond ONLY with valid JSON, no markdown fences, matching this schema:
{{"industry": str, "company_size": str, "revenue": str, "employee_count": int,
"linkedin": str, "technology_stack": str, "funding": str, "buying_signals": str,
"decision_maker_status": "Decision Maker" or "Influencer"}}

Lead:
Name: {lead.get('name')}
Company: {lead.get('company')}
Role: {lead.get('role')}
Website: {lead.get('website')}
Country: {lead.get('country')}
Notes: {lead.get('notes')}

Do not infer or use gender, race, religion, nationality, age, or disability status."""

    try:
        resp = client.chat.completions.create(
            model=MODEL,
            max_tokens=500,
            messages=[{"role": "user", "content": prompt}],
        )
        text = resp.choices[0].message.content.strip()
        text = text.replace("```json", "").replace("```", "").strip()
        data = json.loads(text)
        return data
    except Exception:
        return mock_enrich(lead)


def enrich_lead(lead: dict, use_ai: bool = False) -> dict:
    return ai_enrich(lead) if use_ai else mock_enrich(lead)