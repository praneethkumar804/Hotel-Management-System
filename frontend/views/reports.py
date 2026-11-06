from datetime import date, timedelta

import streamlit as st

from frontend import api_client


def _friendly_error(exc: api_client.APIError) -> str:
    message = str(exc)
    if "customer not found" in message.lower():
        return "Customer not found."
    if "start date" in message.lower():
        return "Start date must be before or equal to end date."
    return message


def _show_table(rows: list[dict], empty_message: str, column_config: dict | None = None):
    if not rows:
        st.info(empty_message)
        return
    st.dataframe(rows, column_config=column_config, hide_index=True, width="stretch")


def render():
    st.title("📊 Reports & Analytics")
    filter_by_date = st.checkbox("Filter revenue by date range")
    date_range = st.date_input("Revenue date range", value=(date.today() - timedelta(days=30), date.today()), disabled=not filter_by_date)
    if filter_by_date:
        if not isinstance(date_range, tuple) or len(date_range) != 2:
            st.info("Select both a start date and an end date.")
            return
        start_date, end_date = date_range
        if start_date > end_date:
            st.warning("Start date must be before or equal to end date.")
            return
        date_parameters = (str(start_date), str(end_date))
    else:
        date_parameters = (None, None)

    try:
        dashboard = api_client.get_dashboard_stats()
        revenue = api_client.get_revenue_report(*date_parameters)
        monthly = api_client.get_monthly_revenue(*date_parameters)
        most_booked = api_client.get_most_booked_room()
        room_summary = api_client.get_room_booking_summary()
        customer_summary = api_client.get_customer_summary()
        payment_status = api_client.get_payment_status_summary()
        booking_status = api_client.get_booking_status_summary()
        customers = api_client.get_customers()
    except api_client.APIError as exc:
        st.error(f"Unable to load reports: {_friendly_error(exc)}")
        return

    with st.container():
        metrics = [("💰 Total Revenue", f"₹{revenue['total_revenue']:,.2f}"), ("📅 Total Bookings", dashboard["total_bookings"]), ("👥 Total Customers", dashboard["total_customers"]), ("💳 Total Paid Payments", revenue["paid_payments"])]
        columns = st.columns(4)
        for column, (label, value) in zip(columns, metrics):
            column.metric(label, value)

    st.subheader("💰 Revenue Summary")
    summary_columns = st.columns(4)
    summary_values = [("Paid Revenue", revenue["total_revenue"]), ("Pending Amount", revenue["pending_amount"]), ("Failed Amount", revenue["failed_amount"]), ("Total Payment Amount", revenue["total_payment_amount"])]
    for column, (label, value) in zip(summary_columns, summary_values):
        column.metric(label, f"₹{value:,.2f}")

    st.subheader("📈 Monthly Revenue")
    _show_table(monthly, "No revenue data available.", {"month": "Month", "revenue": st.column_config.NumberColumn("Revenue", format="₹%.2f")})
    if monthly:
        st.bar_chart({row["month"]: row["revenue"] for row in monthly})

    st.subheader("🏆 Most Booked Room")
    if most_booked:
        st.metric(f"Room {most_booked['room_number']} · {most_booked['room_type']}", f"{most_booked['booking_count']} Bookings")
    else:
        st.info("No bookings found.")

    st.subheader("🛏️ Room Booking Summary")
    _show_table(room_summary, "No room booking data available.", {"room_number": "Room Number", "room_type": "Room Type", "booking_count": "Booking Count"})
    if room_summary:
        st.bar_chart({row["room_number"]: row["booking_count"] for row in room_summary})

    st.subheader("👥 Customer Reports")
    if not customers:
        st.info("No customers found.")
    else:
        selected_customer = st.selectbox("Customer", customers, format_func=lambda customer: f"{customer['name']} (#{customer['customer_id']})")
        customer_id = selected_customer["customer_id"]
        try:
            booking_history = api_client.get_customer_booking_history(customer_id)
            payment_history = api_client.get_customer_payment_history(customer_id)
        except api_client.APIError as exc:
            st.error(f"Unable to load customer history: {_friendly_error(exc)}")
        else:
            st.markdown("#### 👤 Customer Booking History")
            _show_table(booking_history, "No booking history found for this customer.")
            st.markdown("#### 💳 Customer Payment History")
            _show_table(payment_history, "No payment history found for this customer.", {"amount": st.column_config.NumberColumn("Amount", format="₹%.2f")})

    st.subheader("🏆 Top Customers")
    _show_table(customer_summary, "No customer summary data available.", {"customer_name": "Customer Name", "booking_count": "Booking Count", "total_paid_amount": st.column_config.NumberColumn("Total Paid Amount", format="₹%.2f")})

    st.subheader("💳 Payment Status Summary")
    _show_table(payment_status, "No payment status data available.", {"payment_status": "Status", "count": "Count", "total_amount": st.column_config.NumberColumn("Total Amount", format="₹%.2f")})
    if payment_status:
        st.bar_chart({row["payment_status"]: row["total_amount"] for row in payment_status})

    st.subheader("📅 Booking Status Summary")
    _show_table(booking_status, "No booking status data available.", {"booking_status": "Status", "count": "Count"})