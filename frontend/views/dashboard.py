import streamlit as st

from frontend import api_client


def render():
    st.title("Nakshatra Hotel Dashboard")
    try:
        stats = api_client.get_dashboard_stats()
    except api_client.APIError as exc:
        st.error(str(exc)); return
    with st.container():
        cards = [
            ("👥 Total Customers", stats["total_customers"]),
            ("🛏 Total Rooms", stats["total_rooms"]),
            ("📅 Total Bookings", stats["total_bookings"]),
            ("💰 Total Revenue", f"₹{stats['total_revenue']:,.2f}"),
        ]
        columns = st.columns(4)
        for column, (label, value) in zip(columns, cards):
            column.metric(label, value)
    st.subheader("Room & Payment Status")
    with st.container():
        columns = st.columns(4)
        status_cards = [
            ("Available Rooms", "available_rooms"),
            ("Occupied Rooms", "occupied_rooms"),
            ("Maintenance Rooms", "maintenance_rooms"),
            ("Pending Payments", "pending_payments"),
        ]
        for column, (label, key) in zip(columns, status_cards):
            column.metric(label, stats[key])