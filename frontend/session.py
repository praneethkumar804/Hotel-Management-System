import streamlit as st


def initialize():
    st.session_state.setdefault("authenticated", False)
    st.session_state.setdefault("username", "")


def logout():
    st.session_state.clear()
    initialize()