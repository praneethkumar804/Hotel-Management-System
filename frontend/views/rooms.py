import streamlit as st

from frontend import api_client


ROOM_TYPES = ["Single", "Double", "Deluxe", "Suite"]
ROOM_STATUSES = ["Available", "Occupied", "Maintenance"]
STATUS_INDICATORS = {"Available": "🟢 Available", "Occupied": "🔴 Occupied", "Maintenance": "🟡 Maintenance"}


def _validate_room(room_number: str, price: float) -> str | None:
    if not room_number.strip():
        return "Room number cannot be empty."
    if price <= 0:
        return "Price per night must be greater than 0."
    return None


def _room_payload(room_number: str, room_type: str, price: float, status: str) -> dict:
    return {
        "room_number": room_number.strip(),
        "room_type": room_type,
        "price_per_night": price,
        "room_status": status,
    }


def _room_form(room: dict | None, form_key: str, submit_label: str):
    values = room or {}
    with st.form(form_key):
        first_column, second_column = st.columns(2)
        with first_column:
            room_number = st.text_input("Room Number", value=values.get("room_number", ""))
            room_type = st.selectbox(
                "Room Type",
                ROOM_TYPES,
                index=ROOM_TYPES.index(values["room_type"]) if values.get("room_type") in ROOM_TYPES else 0,
            )
        with second_column:
            price = st.number_input(
                "Price Per Night",
                min_value=0.01,
                value=float(values.get("price_per_night", 100.0)),
                step=0.01,
                format="%.2f",
            )
            status = st.selectbox(
                "Room Status",
                ROOM_STATUSES,
                index=ROOM_STATUSES.index(values["room_status"]) if values.get("room_status") in ROOM_STATUSES else 0,
            )
        submitted = st.form_submit_button(submit_label, type="primary")
    return submitted, _room_payload(room_number, room_type, price, status)


def _load_rooms() -> list[dict] | None:
    try:
        return api_client.get_rooms()
    except api_client.APIError as exc:
        st.error(f"Unable to load rooms: {exc}")
        return None


def render():
    st.title("🛏️ Room Management")

    rooms = _load_rooms()
    if rooms is None:
        return
    try:
        stats = api_client.get_dashboard_stats()
    except api_client.APIError as exc:
        st.error(f"Unable to load room summary: {exc}")
        return

    with st.container():
        metrics = [
            ("Total Rooms", stats["total_rooms"]),
            ("Available Rooms", stats["available_rooms"]),
            ("Occupied Rooms", stats["occupied_rooms"]),
            ("Maintenance Rooms", stats["maintenance_rooms"]),
        ]
        columns = st.columns(4)
        for column, (label, value) in zip(columns, metrics):
            column.metric(label, value)

    st.subheader("➕ Add Room")
    submitted, payload = _room_form(None, "add_room_form", "➕ Add Room")
    if submitted:
        validation_error = _validate_room(payload["room_number"], payload["price_per_night"])
        if validation_error:
            st.warning(validation_error)
        else:
            try:
                api_client.create_room(payload)
                st.success("Room added successfully.")
                st.rerun()
            except api_client.APIError as exc:
                st.error(f"Could not add room: {exc}")

    st.subheader("🔎 Search & Filter Rooms")
    search_column, type_column, status_column, refresh_column = st.columns([2, 1, 1, 1])
    search_number = search_column.text_input("Search Room Number")
    selected_type = type_column.selectbox("Room Type", ["All"] + ROOM_TYPES)
    selected_status = status_column.selectbox("Room Status", ["All"] + ROOM_STATUSES)
    if refresh_column.button("↻ Refresh", width="stretch"):
        st.rerun()

    filtered_rooms = [
        room for room in rooms
        if (not search_number.strip() or search_number.strip().lower() in room["room_number"].lower())
        and (selected_type == "All" or room["room_type"] == selected_type)
        and (selected_status == "All" or room["room_status"] == selected_status)
    ]

    st.subheader("📋 Room List")
    if not filtered_rooms:
        st.info("No rooms match the current search and filters.")
        return
    table_rows = [
        {
            "room_id": room["room_id"],
            "room_number": room["room_number"],
            "room_type": room["room_type"],
            "price_per_night": room["price_per_night"],
            "room_status": STATUS_INDICATORS.get(room["room_status"], room["room_status"]),
        }
        for room in filtered_rooms
    ]
    st.dataframe(
        table_rows,
        column_config={
            "room_id": st.column_config.NumberColumn("Room ID"),
            "room_number": "Room Number",
            "room_type": "Room Type",
            "price_per_night": st.column_config.NumberColumn("Price Per Night", format="₹%.2f"),
            "room_status": "Room Status",
        },
        hide_index=True,
        width="stretch",
    )

    room_options = {f"Room {room['room_number']} · ID {room['room_id']}": room for room in filtered_rooms}
    st.subheader("✏️ Edit Room")
    edit_label = st.selectbox("Select a room to edit", ["Choose a room"] + list(room_options), key="edit_room_select")
    if edit_label != "Choose a room":
        selected_room = room_options[edit_label]
        submitted, update_payload = _room_form(selected_room, "edit_room_form", "✏️ Update Room")
        if submitted:
            validation_error = _validate_room(update_payload["room_number"], update_payload["price_per_night"])
            if validation_error:
                st.warning(validation_error)
            else:
                try:
                    api_client.update_room(selected_room["room_id"], update_payload)
                    st.success("Room updated successfully.")
                    st.rerun()
                except api_client.APIError as exc:
                    st.error(f"Could not update room: {exc}")

    st.subheader("🗑️ Delete Room")
    delete_label = st.selectbox("Select a room to delete", ["Choose a room"] + list(room_options), key="delete_room_select")
    if delete_label != "Choose a room":
        selected_room = room_options[delete_label]
        st.warning(f"Are you sure you want to delete Room {selected_room['room_number']}?")
        confirm_delete = st.checkbox("I confirm this deletion.", key="confirm_room_delete")
        if st.button("🗑️ Delete", disabled=not confirm_delete):
            try:
                api_client.delete_room(selected_room["room_id"])
                st.success("Room deleted successfully.")
                st.rerun()
            except api_client.APIError as exc:
                st.error(f"Could not delete room. It may be linked to a booking: {exc}")