"""
scoring.py
Module 4 - Lead Scoring (0-100) and Module 5 - Classification.

Only fairness-approved inputs are used (Module 11 - Fairness & Governance):
industry, revenue, company size, technology, buying intent, job role,
company growth. Protected attributes (gender, race, religion, nationality,
age, disability) are never accepted as scoring inputs - see
utils.assert_no_protected_fields().
"""

from utils import assert_no_protected_fields

DECISION_TITLES = ["ceo", "cto", "cfo", "coo", "founder", "co-founder",
                    "vp", "vice president", "head of", "director"]


def _industry_score(enrichment: dict, icp: dict, weight: int):
    industry = (enrichment.get("industry") or "").lower()
    targets = [t.lower() for t in icp.get("industry_targets", [])]
    if industry in targets:
        return weight, f"Industry '{enrichment.get('industry')}' matches ICP target industries."
    return 0, f"Industry '{enrichment.get('industry')}' is outside ICP target industries."


def _decision_maker_score(lead: dict, enrichment: dict, weight: int):
    status = (enrichment.get("decision_maker_status") or "").lower()
    role = (lead.get("role") or "").lower()
    is_dm = status == "decision maker" or any(t in role for t in DECISION_TITLES)
    if is_dm:
        return weight, f"'{lead.get('role')}' is a decision-making role."
    return int(weight * 0.3), f"'{lead.get('role')}' is likely an influencer, not final decision-maker."


def _buying_intent_score(enrichment: dict, icp: dict, weight: int):
    signal = (enrichment.get("buying_signals") or "").lower()
    keywords = [k.lower() for k in icp.get("buying_intent_keywords", [])]
    if signal == "no recent signal" or not signal:
        return 0, "No recent buying-intent signal detected."
    if any(k in signal for k in keywords):
        return weight, f"Buying signal detected: '{enrichment.get('buying_signals')}'."
    return int(weight * 0.5), f"Weak/unmatched buying signal: '{enrichment.get('buying_signals')}'."


def _revenue_score(enrichment: dict, icp: dict, weight: int):
    revenue_map = {"<$1M": 500_000, "$1M-$10M": 5_000_000, "$10M-$50M": 30_000_000,
                    "$50M-$500M": 200_000_000, "$500M+": 1_000_000_000}
    rev = revenue_map.get(enrichment.get("revenue"), 0)
    if icp.get("revenue_min", 0) <= rev <= icp.get("revenue_max", float("inf")):
        return weight, f"Revenue '{enrichment.get('revenue')}' fits ICP range."
    return int(weight * 0.4), f"Revenue '{enrichment.get('revenue')}' outside ideal ICP range."


def _company_size_score(enrichment: dict, icp: dict, weight: int):
    emp = enrichment.get("employee_count") or 0
    if icp.get("employee_min", 0) <= emp <= icp.get("employee_max", float("inf")):
        return weight, f"Company size ({emp} employees) fits ICP range."
    return int(weight * 0.4), f"Company size ({emp} employees) outside ICP range."


def _technology_score(enrichment: dict, weight: int):
    tech = enrichment.get("technology_stack")
    if tech:
        return weight, f"Technology stack on file: '{tech}'."
    return 0, "No technology stack data available."


def score_lead(lead: dict, enrichment: dict, icp: dict) -> dict:
    """Returns {score, classification, reasons: [...], breakdown: {...}}"""
    assert_no_protected_fields(lead)
    assert_no_protected_fields(enrichment)

    weights = icp.get("weights", {})
    breakdown, reasons, total = {}, [], 0

    steps = [
        ("industry_match", _industry_score(enrichment, icp, weights.get("industry_match", 20))),
        ("decision_maker", _decision_maker_score(lead, enrichment, weights.get("decision_maker", 20))),
        ("buying_intent", _buying_intent_score(enrichment, icp, weights.get("buying_intent", 20))),
        ("revenue", _revenue_score(enrichment, icp, weights.get("revenue", 15))),
        ("company_size", _company_size_score(enrichment, icp, weights.get("company_size", 15))),
        ("technology_match", _technology_score(enrichment, weights.get("technology_match", 10))),
    ]
    for key, (points, reason) in steps:
        breakdown[key] = points
        reasons.append(reason)
        total += points

    total = max(0, min(100, total))
    classification, class_reason = classify(total)
    reasons.append(class_reason)

    return {
        "score": total,
        "classification": classification,
        "reasons": reasons,
        "breakdown": breakdown,
    }


def classify(score: int):
    if score >= 80:
        return "Hot", f"Score {score} >= 80: classified as Hot - route to email draft + human approval."
    if score >= 50:
        return "Nurture", f"Score {score} in 50-79: classified as Nurture - route to marketing sequence."
    return "Disqualified", f"Score {score} < 50: classified as Disqualified - archive with reason logged."