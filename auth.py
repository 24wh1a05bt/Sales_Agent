"""
auth.py
Lightweight session-based authentication + Role-Based Access Control
(Module: Authentication / Security - JWT is simulated here via Streamlit
session_state since Streamlit has no native JWT transport; swap in a
real JWT-issuing FastAPI backend for production per the spec's stack).
"""

import bcrypt
import streamlit as st

from database import get_user_by_email

ROLE_HOME = {
    "SDR": "Lead List",
    "Sales Manager": "Analytics",
    "Admin": "Settings",
}


def login(email: str, password: str) -> bool:
    user = get_user_by_email(email)
    if not user:
        return False
    if not bcrypt.checkpw(password.encode(), user["password_hash"].encode()):
        return False
    st.session_state["user"] = {"id": user["id"], "name": user["name"],
                                 "email": user["email"], "role": user["role"]}
    return True


def logout():
    st.session_state.pop("user", None)


def current_user():
    return st.session_state.get("user")


def require_login(allowed_roles=None):
    """Call at the top of every page. Stops rendering with a friendly
    message if the user isn't logged in or lacks the required role."""
    user = current_user()
    if not user:
        st.warning("Please log in from the Home page first.")
        st.stop()
    if allowed_roles and user["role"] not in allowed_roles:
        st.error(f"Your role ({user['role']}) doesn't have access to this page.")
        st.stop()
    return user