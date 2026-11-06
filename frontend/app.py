import sys
from pathlib import Path

import streamlit as st


# Streamlit runs this file directly, so make the project root importable.
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

LOGO_PATH = Path(__file__).resolve().parent / "assets" / "nakshatra_hotel_logo.png"

from frontend import api_client, session
from frontend.views import bookings, customers, dashboard, payments, reports, rooms, services


st.set_page_config(page_title="Nakshatra Hotel Management System", layout="wide")
session.initialize()


def login_page():
    st.title("Nakshatra Hotel Management System")
    st.caption("Operations dashboard")
    with st.form("login"):
        username = st.text_input("Username", value="admin"); password = st.text_input("Password", type="password")
        if st.form_submit_button("Sign in"):
            try:
                result = api_client.login(username, password); st.session_state.authenticated = result["authenticated"]; st.session_state.username = result["username"]; st.rerun()
            except api_client.APIError as exc: st.error(str(exc))


def application():
    if LOGO_PATH.exists():
        st.sidebar.image(str(LOGO_PATH), width=150)
    st.sidebar.markdown("**NAKSHATRA**  \n**HOTEL MANAGEMENT**  \n**SYSTEM**")
    st.sidebar.write(f"Welcome, {st.session_state.username}")
    page = st.sidebar.radio(
        "Navigate",
        ["Dashboard", "Customers", "Rooms", "Bookings", "Payments", "Services", "Reports"],
    )
    if st.sidebar.button("Logout"):
        session.logout(); st.rerun()
    page_renders = {
        "Dashboard": dashboard.render,
        "Customers": customers.render,
        "Rooms": rooms.render,
        "Bookings": bookings.render,
        "Payments": payments.render,
        "Services": services.render,
        "Reports": reports.render,
    }
    page_renders[page]()


if st.session_state.authenticated: application()
else: login_page()