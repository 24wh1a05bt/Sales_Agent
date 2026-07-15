"""
email_agent.py
Module 7 - AI Email Generation.

Generates Subject / Greeting / Personalized Body / Call-to-Action using
company, role, buying signals, industry, and company information.
Uses OpenAI when an API key is configured (see ai_client.py); otherwise
falls back to a deterministic template so the app is fully demoable
without any external credentials.
"""

import json

from ai_client import get_client, MODEL

SYSTEM_PROMPT = """You are an SDR outreach assistant. Write concise, warm,
non-generic B2B cold emails. Never mention gender, race, religion,
nationality, age, or disability. Base personalization only on company,
role, industry, and buying signals provided. Respond ONLY with valid JSON:
{"subject": str, "body": str} where body includes greeting, 2-3 sentence
personalized body referencing the buying signal/industry, and a clear
low-friction call-to-action (e.g. offer a 15-minute call). No markdown."""


def _template_fallback(lead: dict, enrichment: dict) -> dict:
    first_name = (lead.get("name") or "there").split(" ")[0]
    company = lead.get("company") or "your company"
    industry = enrichment.get("industry") or "your industry"
    signal = enrichment.get("buying_signals") or "your recent growth"

    subject = f"Quick idea for {company}"
    body = (
        f"Hi {first_name},\n\n"
        f"I noticed {company} is active in {industry} and saw signals around "
        f"\"{signal}\". Companies at this stage often struggle to keep up with "
        f"lead follow-up while scaling — that's exactly the kind of problem we help solve.\n\n"
        f"Would you be open to a quick 15-minute call next week to see if it's a fit?\n\n"
        f"Best,\nSDR Team"
    )
    return {"subject": subject, "body": body}


def generate_email(lead: dict, enrichment: dict, score_result: dict) -> dict:
    client = get_client()
    if client is None:
        return _template_fallback(lead, enrichment)

    user_prompt = f"""Lead:
Name: {lead.get('name')}
Company: {lead.get('company')}
Role: {lead.get('role')}
Industry: {enrichment.get('industry')}
Buying signals: {enrichment.get('buying_signals')}
Technology stack: {enrichment.get('technology_stack')}
Lead score: {score_result.get('score')} ({score_result.get('classification')})
"""
    try:
        resp = client.chat.completions.create(
            model=MODEL,
            max_tokens=500,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user_prompt},
            ],
        )
        text = resp.choices[0].message.content.strip()
        text = text.replace("```json", "").replace("```", "").strip()
        data = json.loads(text)
        if "subject" in data and "body" in data:
            return data
        return _template_fallback(lead, enrichment)
    except Exception:
        return _template_fallback(lead, enrichment)