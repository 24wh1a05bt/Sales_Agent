"""
ai_client.py
Thin wrapper around the OpenAI client (per the spec's AI stack:
OpenAI GPT / LangChain / LangGraph). The rest of the app never talks
to OpenAI directly - it calls get_client() so that:
  * a missing/invalid API key doesn't crash the app
  * the model name is configured in one place
  * enrichment/email modules can fall back to deterministic mocks
"""

import os
import streamlit as st

MODEL = os.environ.get("OPENAI_MODEL", "gpt-4o-mini")

_client_cache = {}


def get_api_key() -> str | None:
    # Priority: st.secrets (Streamlit Cloud) -> environment variable ->
    # a key entered by an Admin in the running session (see Settings page)
    key = None
    try:
        key = st.secrets.get("OPENAI_API_KEY")
    except Exception:
        key = None
    if not key:
        key = os.environ.get("OPENAI_API_KEY")
    if not key:
        key = st.session_state.get("openai_api_key") if hasattr(st, "session_state") else None
    return key or None


def get_client():
    """Returns an OpenAI client, or None if no API key is configured.
    Callers MUST handle the None case by falling back to mock logic."""
    key = get_api_key()
    if not key:
        return None
    if key in _client_cache:
        return _client_cache[key]
    try:
        from openai import OpenAI

        client = OpenAI(api_key=key)
        _client_cache[key] = client
        return client
    except Exception:
        return None