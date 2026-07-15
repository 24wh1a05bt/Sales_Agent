"""
utils.py
Shared helpers, including the fairness guardrail described in
Module 11 - Fairness & Governance: the AI must never use gender, race,
religion, nationality, age, or disability as a scoring/enrichment input.
"""

PROTECTED_FIELDS = {"gender", "race", "religion", "nationality", "age", "disability"}


class FairnessViolation(Exception):
    pass


def assert_no_protected_fields(data: dict):
    """Raises FairnessViolation if a protected attribute key is present
    anywhere in a data dict passed into scoring or enrichment logic."""
    if not data:
        return
    found = PROTECTED_FIELDS.intersection({k.lower() for k in data.keys()})
    if found:
        raise FairnessViolation(
            f"Protected attribute(s) {found} must not be used in AI scoring or enrichment."
        )


def badge_color(classification: str) -> str:
    return {"Hot": "🔴", "Nurture": "🟡", "Disqualified": "⚪"}.get(classification, "🔵")


def status_color(status: str) -> str:
    return {
        "Pending Review": "🟡",
        "Approved": "🟢",
        "Rejected": "🔴",
        "Sent": "🔵",
        "Archived": "⚪",
    }.get(status, "🔵")