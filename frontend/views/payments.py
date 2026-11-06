from datetime import date

import streamlit as st

from frontend import api_client


PAYMENT_METHODS = ["Cash", "UPI", "Card", "Net Banking"]
PAYMENT_STATUSES = ["Paid", "Pending", "Failed"]
STATUS_INDICATORS = {"Paid": "🟢 Paid", "Pending": "🟡 Pending", "Failed": "🔴 Failed"}


def _validate_payment(amount: float) -> str | None:
    if amount <= 0:
        return "Payment amount must be greater than 0."
    return None


def _payment_payload(booking_id: int, customer_id: int, amount: float, method: str, payment_date: date, status: str) -> dict:
    return {"booking_id": booking_id, "customer_id": customer_id, "amount": amount, "payment_method": method, "payment_date": str(payment_date), "payment_status": status}


def _friendly_error(exc: api_client.APIError) -> str:
    message = str(exc)
    lowered = message.lower()
    if "customer does not belong" in lowered:
        return "Selected customer does not belong to this booking."
    if "booking not found" in lowered:
        return "Selected booking was not found."
    if "customer not found" in lowered:
        return "Selected customer was not found."
    if "payment not found" in lowered:
        return "Payment not found."
    if "amount" in lowered:
        return "Payment amount must be greater than 0."
    return message


def _customer_options(customers: list[dict]) -> dict[str, int]:
    return {f"{customer['name']} · ID {customer['customer_id']}": customer["customer_id"] for customer in customers}


def _booking_options(bookings: list[dict]) -> dict[str, int]:
    return {f"Booking #{booking['booking_id']} · Room {booking['room_number']} · {booking['customer_name']}": booking["booking_id"] for booking in bookings}


def _payment_form(customers: list[dict], bookings: list[dict], form_key: str, submit_label: str, payment: dict | None = None):
    customer_options = _customer_options(customers)
    booking_options = _booking_options(bookings)
    if not booking_options:
        st.info("No bookings available. Please create a booking first.")
        return False, None
    if not customer_options:
        st.info("No customers available. Please add a customer first.")
        return False, None
    booking_id = payment.get("booking_id") if payment else next(iter(booking_options.values()))
    customer_id = payment.get("customer_id") if payment else next(iter(customer_options.values()))
    booking_label = next((label for label, identifier in booking_options.items() if identifier == booking_id), next(iter(booking_options)))
    customer_label = next((label for label, identifier in customer_options.items() if identifier == customer_id), next(iter(customer_options)))
    with st.form(form_key):
        first_column, second_column = st.columns(2)
        with first_column:
            selected_booking = st.selectbox("Booking", list(booking_options), index=list(booking_options).index(booking_label))
            selected_customer = st.selectbox("Customer", list(customer_options), index=list(customer_options).index(customer_label))
            amount = st.number_input("Amount", min_value=0.01, value=float(payment.get("amount", 100.0)) if payment else 100.0, step=0.01, format="%.2f")
        with second_column:
            method = st.selectbox("Payment Method", PAYMENT_METHODS, index=PAYMENT_METHODS.index(payment["payment_method"]) if payment and payment.get("payment_method") in PAYMENT_METHODS else 0)
            payment_date = st.date_input("Payment Date", value=date.fromisoformat(payment["payment_date"]) if payment else date.today())
            status = st.selectbox("Payment Status", PAYMENT_STATUSES, index=PAYMENT_STATUSES.index(payment["payment_status"]) if payment and payment.get("payment_status") in PAYMENT_STATUSES else 0)
        submitted = st.form_submit_button(submit_label, type="primary")
    return submitted, (_payment_payload(booking_options[selected_booking], customer_options[selected_customer], amount, method, payment_date, status), amount)


def _load_data():
    try:
        return api_client.get_customers(), api_client.get_bookings(), api_client.get_payments()
    except api_client.APIError as exc:
        st.error(f"Unable to load payment data: {_friendly_error(exc)}")
        return None


def render():
    st.title("💳 Payment Management")
    data = _load_data()
    if data is None:
        return
    customers, bookings, all_payments = data
    try:
        summary = api_client.get_payment_summary()
    except api_client.APIError as exc:
        st.error(f"Unable to load payment summary: {_friendly_error(exc)}")
        return

    with st.container():
        metrics = [("Total Payments", summary["total_payments"]), ("Paid", summary["paid_payments"]), ("Pending", summary["pending_payments"]), ("Failed", summary["failed_payments"]), ("Total Paid Revenue", f"₹{summary['total_paid_revenue']:,.2f}")]
        columns = st.columns(5)
        for column, (label, value) in zip(columns, metrics):
            column.metric(label, value)

    st.subheader("➕ Create New Payment")
    submitted, form_result = _payment_form(customers, bookings, "create_payment_form", "➕ Create Payment")
    if submitted and form_result:
        payload, amount = form_result
        validation_error = _validate_payment(amount)
        if validation_error:
            st.warning(validation_error)
        else:
            try:
                api_client.create_payment(payload)
                st.success("Payment created successfully.")
                st.rerun()
            except api_client.APIError as exc:
                st.error(f"Could not create payment: {_friendly_error(exc)}")

    st.subheader("🔎 Search & Filter Payments")
    filter_columns = st.columns(4)
    filter_status = filter_columns[0].selectbox("Payment Status", ["All"] + PAYMENT_STATUSES)
    filter_method = filter_columns[1].selectbox("Payment Method", ["All"] + PAYMENT_METHODS)
    customer_filter_options = {"All": None, **_customer_options(customers)}
    booking_filter_options = {"All": None, **_booking_options(bookings)}
    selected_customer = filter_columns[2].selectbox("Customer", list(customer_filter_options), key="payment_filter_customer")
    selected_booking = filter_columns[3].selectbox("Booking", list(booking_filter_options), key="payment_filter_booking")
    use_date = st.checkbox("Filter by payment date")
    selected_date = st.date_input("Payment Date", value=date.today(), disabled=not use_date, key="payment_filter_date")
    filter_params = {"payment_status": None if filter_status == "All" else filter_status, "payment_method": None if filter_method == "All" else filter_method, "customer_id": customer_filter_options[selected_customer], "booking_id": booking_filter_options[selected_booking], "payment_date": str(selected_date) if use_date else None}
    try:
        payments = api_client.filter_payments(**filter_params) if any(value is not None for value in filter_params.values()) else all_payments
    except api_client.APIError as exc:
        st.error(f"Unable to filter payments: {_friendly_error(exc)}")
        payments = []

    st.subheader("📋 Payment List")
    if not payments:
        st.info("No payments match the selected filters.")
    else:
        st.dataframe(
            [{"payment_id": row["payment_id"], "booking_id": row["booking_id"], "customer": row["customer_name"], "amount": row["amount"], "payment_method": row["payment_method"], "payment_date": row["payment_date"], "payment_status": STATUS_INDICATORS.get(row["payment_status"], row["payment_status"])} for row in payments],
            column_config={"payment_id": "Payment ID", "booking_id": "Booking ID", "customer": "Customer", "amount": st.column_config.NumberColumn("Amount", format="₹%.2f"), "payment_method": "Payment Method", "payment_date": "Payment Date", "payment_status": "Payment Status"},
            hide_index=True,
            width="stretch",
        )

    payment_options = {f"Payment #{payment['payment_id']} · {payment['customer_name']} · ₹{payment['amount']:,.2f}": payment for payment in payments}
    st.subheader("✏️ Edit Payment")
    edit_label = st.selectbox("Select a payment to edit", ["Choose a payment"] + list(payment_options), key="edit_payment_select")
    if edit_label != "Choose a payment":
        selected_payment = payment_options[edit_label]
        submitted, form_result = _payment_form(customers, bookings, "edit_payment_form", "✏️ Update Payment", selected_payment)
        if submitted and form_result:
            payload, amount = form_result
            validation_error = _validate_payment(amount)
            if validation_error:
                st.warning(validation_error)
            else:
                try:
                    api_client.update_payment(selected_payment["payment_id"], payload)
                    st.success("Payment updated successfully.")
                    st.rerun()
                except api_client.APIError as exc:
                    st.error(f"Could not update payment: {_friendly_error(exc)}")

    st.subheader("🗑️ Delete Payment")
    delete_label = st.selectbox("Select a payment to delete", ["Choose a payment"] + list(payment_options), key="delete_payment_select")
    if delete_label != "Choose a payment":
        selected_payment = payment_options[delete_label]
        st.warning(f"Are you sure you want to delete Payment #{selected_payment['payment_id']}?")
        confirm_delete = st.checkbox("I confirm this deletion.", key="confirm_payment_delete")
        if st.button("🗑️ Delete Payment", disabled=not confirm_delete):
            try:
                api_client.delete_payment(selected_payment["payment_id"])
                st.success("Payment deleted successfully.")
                st.rerun()
            except api_client.APIError as exc:
                st.error(f"Could not delete payment: {_friendly_error(exc)}")