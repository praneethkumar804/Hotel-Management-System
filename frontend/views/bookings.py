from datetime import date, timedelta

import streamlit as st

from frontend import api_client


BOOKING_STATUSES = ["Confirmed", "Checked-In", "Checked-Out", "Cancelled"]


def _booking_payload(customer_id: int, room_id: int, check_in: date, check_out: date, guests: int, status: str) -> dict:
    return {"customer_id": customer_id, "room_id": room_id, "check_in_date": str(check_in), "check_out_date": str(check_out), "number_of_guests": guests, "booking_status": status}


def _validate_booking(check_in: date, check_out: date, guests: int) -> str | None:
    if check_out <= check_in:
        return "Check-out date must be after check-in date."
    if guests < 1:
        return "Number of guests must be greater than 0."
    return None


def _friendly_error(exc: api_client.APIError) -> str:
    message = str(exc)
    lowered = message.lower()
    if "check-out date" in lowered:
        return "Check-out date must be after check-in date."
    if "maintenance" in lowered:
        return "This room is currently under maintenance."
    if "unavailable" in lowered or "occupied" in lowered:
        return "This room is not available for the selected dates."
    if "customer not found" in lowered:
        return "Selected customer was not found."
    if "room not found" in lowered:
        return "Selected room was not found."
    if "booking not found" in lowered:
        return "Booking not found."
    return message


def _customer_options(customers: list[dict]) -> dict[str, int]:
    return {f"{customer['name']} · ID {customer['customer_id']}": customer["customer_id"] for customer in customers}


def _room_options(rooms: list[dict], include_room_id: int | None = None) -> dict[str, int]:
    selectable = [room for room in rooms if room["room_status"] != "Maintenance" and (room["room_status"] == "Available" or room["room_id"] == include_room_id)]
    return {f"Room {room['room_number']} · {room['room_type']} · ₹{room['price_per_night']:,.2f}/night": room["room_id"] for room in selectable}


def _booking_form(customers: list[dict], rooms: list[dict], form_key: str, submit_label: str, booking: dict | None = None):
    customer_options = _customer_options(customers)
    room_options = _room_options(rooms, booking.get("room_id") if booking else None)
    if not customer_options:
        st.info("No customers available. Please add a customer first.")
        return False, None
    if not room_options:
        st.info("No available rooms. Please add or free a room first.")
        return False, None

    customer_ids = list(customer_options.values())
    room_ids = list(room_options.values())
    current_customer = booking.get("customer_id") if booking else customer_ids[0]
    current_room = booking.get("room_id") if booking else room_ids[0]
    customer_label = next(label for label, identifier in customer_options.items() if identifier == current_customer)
    room_label = next(label for label, identifier in room_options.items() if identifier == current_room)
    current_check_in = date.fromisoformat(booking["check_in_date"]) if booking else date.today()
    current_check_out = date.fromisoformat(booking["check_out_date"]) if booking else date.today() + timedelta(days=1)

    with st.form(form_key):
        first_column, second_column = st.columns(2)
        with first_column:
            selected_customer = st.selectbox("Customer", list(customer_options), index=list(customer_options).index(customer_label))
            check_in = st.date_input("Check-in Date", value=current_check_in)
            guests = st.number_input("Number of Guests", min_value=1, value=int(booking.get("number_of_guests", 1)) if booking else 1, step=1)
        with second_column:
            selected_room = st.selectbox("Room", list(room_options), index=list(room_options).index(room_label))
            check_out = st.date_input("Check-out Date", value=current_check_out)
            status = st.selectbox("Booking Status", BOOKING_STATUSES, index=BOOKING_STATUSES.index(booking["booking_status"]) if booking else 0)
        submitted = st.form_submit_button(submit_label, type="primary")
    return submitted, (_booking_payload(customer_options[selected_customer], room_options[selected_room], check_in, check_out, guests, status), check_in, check_out, guests)


def _load_booking_data():
    try:
        return api_client.get_customers(), api_client.get_rooms(), api_client.get_bookings()
    except api_client.APIError as exc:
        st.error(f"Unable to load booking data: {_friendly_error(exc)}")
        return None


def render():
    st.title("📅 Booking Management")
    data = _load_booking_data()
    if data is None:
        return
    customers, rooms, all_bookings = data

    try:
        stats = api_client.get_dashboard_stats()
    except api_client.APIError as exc:
        st.error(f"Unable to load booking summary: {_friendly_error(exc)}")
        return
    with st.container():
        summary = [("Total Bookings", "total_bookings"), ("Confirmed", "confirmed_bookings"), ("Checked-In", "checked_in_bookings"), ("Checked-Out", "checked_out_bookings"), ("Cancelled", "cancelled_bookings")]
        columns = st.columns(5)
        for column, (label, key) in zip(columns, summary):
            column.metric(label, stats[key])

    st.subheader("➕ Create New Booking")
    submitted, form_result = _booking_form(customers, rooms, "create_booking_form", "➕ Create Booking")
    if submitted and form_result:
        payload, check_in, check_out, guests = form_result
        validation_error = _validate_booking(check_in, check_out, guests)
        if validation_error:
            st.warning(validation_error)
        else:
            try:
                api_client.create_booking(payload)
                st.success("Booking created successfully.")
                st.rerun()
            except api_client.APIError as exc:
                st.error(f"Could not create booking: {_friendly_error(exc)}")

    st.subheader("🔎 Search & Filter Bookings")
    filter_columns = st.columns(4)
    filter_status = filter_columns[0].selectbox("Booking Status", ["All"] + BOOKING_STATUSES)
    filter_customer_options = {"All": None, **_customer_options(customers)}
    filter_customer = filter_columns[1].selectbox("Customer", list(filter_customer_options), key="booking_filter_customer")
    filter_room_options = {"All": None, **{f"Room {room['room_number']}": room["room_id"] for room in rooms}}
    filter_room = filter_columns[2].selectbox("Room", list(filter_room_options), key="booking_filter_room")
    use_date_filter = filter_columns[3].checkbox("Filter by dates")
    filter_check_in = st.date_input("Check-in date", value=date.today(), disabled=not use_date_filter, key="filter_check_in")
    filter_check_out = st.date_input("Check-out date", value=date.today(), disabled=not use_date_filter, key="filter_check_out")
    filter_params = {"booking_status": None if filter_status == "All" else filter_status, "customer_id": filter_customer_options[filter_customer], "room_id": filter_room_options[filter_room], "check_in_date": str(filter_check_in) if use_date_filter else None, "check_out_date": str(filter_check_out) if use_date_filter else None}
    try:
        bookings = api_client.filter_bookings(**filter_params) if any(value is not None for value in filter_params.values()) else all_bookings
    except api_client.APIError as exc:
        st.error(f"Unable to filter bookings: {_friendly_error(exc)}")
        bookings = []

    st.subheader("📋 Booking List")
    if not bookings:
        st.info("No bookings match the selected filters.")
    else:
        st.dataframe(
            [{"booking_id": row["booking_id"], "customer": row["customer_name"], "room": row["room_number"], "room_type": row["room_type"], "check_in_date": row["check_in_date"], "check_out_date": row["check_out_date"], "number_of_guests": row["number_of_guests"], "booking_status": row["booking_status"]} for row in bookings],
            column_config={"booking_id": "Booking ID", "customer": "Customer", "room": "Room", "room_type": "Room Type", "check_in_date": "Check-in Date", "check_out_date": "Check-out Date", "number_of_guests": "Guests", "booking_status": "Booking Status"},
            hide_index=True,
            width="stretch",
        )

    booking_options = {f"Booking #{booking['booking_id']} · {booking['customer_name']} · Room {booking['room_number']}": booking for booking in bookings}
    st.subheader("✏️ Edit Booking")
    edit_label = st.selectbox("Select a booking to edit", ["Choose a booking"] + list(booking_options), key="edit_booking_select")
    if edit_label != "Choose a booking":
        selected_booking = booking_options[edit_label]
        submitted, form_result = _booking_form(customers, rooms, "edit_booking_form", "✏️ Update Booking", selected_booking)
        if submitted and form_result:
            payload, check_in, check_out, guests = form_result
            validation_error = _validate_booking(check_in, check_out, guests)
            if validation_error:
                st.warning(validation_error)
            else:
                try:
                    api_client.update_booking(selected_booking["booking_id"], payload)
                    st.success("Booking updated successfully.")
                    st.rerun()
                except api_client.APIError as exc:
                    st.error(f"Could not update booking: {_friendly_error(exc)}")

    st.subheader("🗑️ Delete Booking")
    delete_label = st.selectbox("Select a booking to delete", ["Choose a booking"] + list(booking_options), key="delete_booking_select")
    if delete_label != "Choose a booking":
        selected_booking = booking_options[delete_label]
        st.warning(f"Are you sure you want to delete Booking #{selected_booking['booking_id']}?")
        confirm_delete = st.checkbox("I confirm this deletion.", key="confirm_booking_delete")
        if st.button("🗑️ Delete Booking", disabled=not confirm_delete):
            try:
                api_client.delete_booking(selected_booking["booking_id"])
                st.success("Booking deleted successfully.")
                st.rerun()
            except api_client.APIError as exc:
                st.error(f"Could not delete booking: {_friendly_error(exc)}")

    _render_booking_services(bookings)


def _render_booking_services(bookings: list[dict]):
    st.subheader("🛎️ Services for Booking")
    if not bookings:
        st.info("Create or select a booking to manage services.")
        return
    booking_options = {f"Booking #{booking['booking_id']} · {booking['customer_name']}": booking["booking_id"] for booking in bookings}
    selected_booking_label = st.selectbox("Booking", list(booking_options), key="service_booking_select")
    booking_id = booking_options[selected_booking_label]
    try:
        services = api_client.get_services()
        booking_services = api_client.get_booking_services(booking_id)
    except api_client.APIError as exc:
        st.error(f"Unable to load booking services: {_friendly_error(exc)}")
        return
    active_services = [service for service in services if service.get("service_status") == "Active"]
    if active_services:
        service_options = {f"{service['service_name']} · ₹{service['price']:,.2f}": service["service_id"] for service in active_services}
        with st.form("booking_service_form"):
            selected_service = st.selectbox("Service", list(service_options))
            quantity = st.number_input("Quantity", min_value=1, value=1, step=1)
            if st.form_submit_button("Add Service"):
                try:
                    api_client.add_booking_service(booking_id, {"service_id": service_options[selected_service], "quantity": quantity})
                    st.success("Service added to booking.")
                    st.rerun()
                except api_client.APIError as exc:
                    st.error(f"Could not add service: {_friendly_error(exc)}")
    elif services:
        st.info("All services are currently inactive. This service is currently unavailable.")
    else:
        st.info("No services available. Add a service first.")
    if not booking_services:
        st.info("No services have been added to this booking.")
        return
    st.dataframe(booking_services, column_config={"service_name": "Service Name", "price": st.column_config.NumberColumn("Price", format="₹%.2f"), "quantity": "Quantity", "total": st.column_config.NumberColumn("Total", format="₹%.2f")}, hide_index=True, width="stretch")
    total_service_charges = sum(service["total"] for service in booking_services)
    st.metric("Total Service Charges", f"₹{total_service_charges:,.2f}")
    service_row = st.selectbox("Select service to update or delete", booking_services, format_func=lambda row: f"{row['service_name']} · quantity {row['quantity']}", key="booking_service_row")
    update_quantity = st.number_input("Updated Quantity", min_value=1, value=int(service_row["quantity"]), step=1)
    update_column, delete_column = st.columns(2)
    if update_column.button("Update Quantity"):
        try:
            api_client.update_booking_service(service_row["booking_service_id"], {"service_id": service_row["service_id"], "quantity": update_quantity})
            st.success("Service quantity updated.")
            st.rerun()
        except api_client.APIError as exc:
            st.error(f"Could not update service: {_friendly_error(exc)}")
    if delete_column.button("Delete Service"):
        try:
            api_client.delete_booking_service(service_row["booking_service_id"])
            st.success("Service removed from booking.")
            st.rerun()
        except api_client.APIError as exc:
            st.error(f"Could not delete service: {_friendly_error(exc)}")