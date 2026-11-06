import streamlit as st

from frontend import api_client


SERVICE_STATUSES = ["Active", "Inactive"]


def _validate_service(name: str, price: float) -> str | None:
    if not name.strip():
        return "Service name cannot be empty."
    if price <= 0:
        return "Service price must be greater than 0."
    return None


def _service_form(service: dict | None, form_key: str, submit_label: str):
    values = service or {}
    with st.form(form_key):
        first_column, second_column = st.columns(2)
        with first_column:
            name = st.text_input("Service Name", value=values.get("service_name", ""))
            price = st.number_input("Price", min_value=0.01, value=float(values.get("price", 25.0)), step=0.01, format="%.2f")
        with second_column:
            description = st.text_area("Description", value=values.get("description") or "", height=100)
            status = st.selectbox("Service Status", SERVICE_STATUSES, index=SERVICE_STATUSES.index(values["service_status"]) if values.get("service_status") in SERVICE_STATUSES else 0)
        submitted = st.form_submit_button(submit_label, type="primary")
    return submitted, {"service_name": name.strip(), "price": price, "description": description.strip(), "service_status": status}


def _load_summary():
    try:
        return api_client.get_service_summary()
    except api_client.APIError as exc:
        st.error(f"Unable to load service summary: {exc}")
        return None


def render():
    st.title("🛎️ Hotel Services Management")
    summary = _load_summary()
    if summary is None:
        return
    with st.container():
        columns = st.columns(3)
        for column, (label, key) in zip(columns, [("Total Services", "total_services"), ("Active Services", "active_services"), ("Inactive Services", "inactive_services")]):
            column.metric(label, summary[key])

    st.subheader("➕ Add New Service")
    submitted, payload = _service_form(None, "add_service_form", "➕ Add Service")
    if submitted:
        validation_error = _validate_service(payload["service_name"], payload["price"])
        if validation_error:
            st.warning(validation_error)
        else:
            try:
                api_client.create_service(payload)
                st.success("Service added successfully.")
                st.rerun()
            except api_client.APIError as exc:
                st.error(f"Could not add service: {exc}")

    st.subheader("🔎 Search Services")
    search_column, status_column, refresh_column = st.columns([2, 1, 1])
    query = search_column.text_input("Search by service name")
    selected_status = status_column.selectbox("Service Status", ["All"] + SERVICE_STATUSES)
    if refresh_column.button("↻ Refresh", width="stretch"):
        st.rerun()
    try:
        services = api_client.filter_services(query=query or None, service_status=None if selected_status == "All" else selected_status)
    except api_client.APIError as exc:
        st.error(f"Unable to load services: {exc}")
        return

    st.subheader("📋 Services")
    if not services:
        st.info("No services match the current search and filter.")
        return
    st.dataframe(
        [{"service_id": service["service_id"], "service_name": service["service_name"], "price": service["price"], "description": service.get("description") or "", "service_status": service["service_status"]} for service in services],
        column_config={"service_id": "Service ID", "service_name": "Service Name", "price": st.column_config.NumberColumn("Price", format="₹%.2f"), "description": "Description", "service_status": "Service Status"},
        hide_index=True,
        width="stretch",
    )

    service_options = {f"{service['service_name']} · ID {service['service_id']}": service for service in services}
    st.subheader("✏️ Edit Service")
    edit_label = st.selectbox("Select a service to edit", ["Choose a service"] + list(service_options), key="edit_service_select")
    if edit_label != "Choose a service":
        selected_service = service_options[edit_label]
        submitted, update_payload = _service_form(selected_service, "edit_service_form", "✏️ Update Service")
        if submitted:
            validation_error = _validate_service(update_payload["service_name"], update_payload["price"])
            if validation_error:
                st.warning(validation_error)
            else:
                try:
                    api_client.update_service(selected_service["service_id"], update_payload)
                    st.success("Service updated successfully.")
                    st.rerun()
                except api_client.APIError as exc:
                    st.error(f"Could not update service: {exc}")

    st.subheader("🗑️ Delete Service")
    delete_label = st.selectbox("Select a service to delete", ["Choose a service"] + list(service_options), key="delete_service_select")
    if delete_label != "Choose a service":
        selected_service = service_options[delete_label]
        st.warning(f"Are you sure you want to delete {selected_service['service_name']}?")
        confirm_delete = st.checkbox("I confirm this deletion.", key="confirm_service_delete")
        if st.button("🗑️ Delete Service", disabled=not confirm_delete):
            try:
                api_client.delete_service(selected_service["service_id"])
                st.success("Service deleted successfully.")
                st.rerun()
            except api_client.APIError as exc:
                st.error(f"This service cannot be deleted because it is associated with existing bookings. {exc}")