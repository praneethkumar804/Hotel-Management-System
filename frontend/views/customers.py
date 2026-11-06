import re

import streamlit as st

from frontend import api_client


EMAIL_PATTERN = re.compile(r"^[^\s@]+@[^\s@]+\.[^\s@]+$")
GENDER_OPTIONS = ["Female", "Male", "Non-binary", "Other", "Prefer not to say"]


def _validate_customer(name: str, age: int, phone: str, email: str, address: str) -> str | None:
    if not name.strip():
        return "Name cannot be empty."
    if age < 1 or age > 120:
        return "Age must be between 1 and 120."
    if not phone.strip():
        return "Phone cannot be empty."
    if not EMAIL_PATTERN.fullmatch(email.strip()):
        return "Enter a valid email address."
    if not address.strip():
        return "Address cannot be empty."
    return None


def _customer_payload(name: str, age: int, gender: str, phone: str, email: str, address: str) -> dict:
    return {"name": name.strip(), "age": age, "gender": gender, "phone": phone.strip(), "email": email.strip(), "address": address.strip()}


def _customer_form(customer: dict | None, form_key: str, submit_label: str):
    values = customer or {}
    with st.form(form_key):
        first_column, second_column = st.columns(2)
        with first_column:
            name = st.text_input("Name", value=values.get("name", ""))
            age = st.number_input("Age", min_value=1, max_value=120, value=int(values.get("age", 25)), step=1)
            gender = st.selectbox("Gender", GENDER_OPTIONS, index=GENDER_OPTIONS.index(values["gender"]) if values.get("gender") in GENDER_OPTIONS else len(GENDER_OPTIONS) - 1)
        with second_column:
            phone = st.text_input("Phone", value=values.get("phone", ""))
            email = st.text_input("Email", value=values.get("email", ""))
            address = st.text_area("Address", value=values.get("address", ""), height=100)
        submitted = st.form_submit_button(submit_label, type="primary")
    return submitted, _customer_payload(name, age, gender, phone, email, address)


def _load_customers(query: str) -> list[dict] | None:
    try:
        return api_client.search_customers(query) if query else api_client.get_customers()
    except api_client.APIError as exc:
        st.error(f"Unable to load customers: {exc}")
        return None


def render():
    st.title("👥 Customer Management")
    search_query = st.text_input("Search customers", placeholder="Search by name, phone, or email", help="Search is handled by the FastAPI customer search endpoint.")
    customers = _load_customers(search_query)
    if customers is None:
        return

    total_column, recent_column, refresh_column = st.columns([1, 1, 1])
    total_column.metric("Total Customers", len(customers))
    recent_column.metric("Recently Added", min(len(customers), 5))
    if refresh_column.button("↻ Refresh", width="stretch"):
        st.rerun()

    st.subheader("Add Customer")
    submitted, payload = _customer_form(None, "add_customer_form", "Add Customer")
    if submitted:
        validation_error = _validate_customer(payload["name"], payload["age"], payload["phone"], payload["email"], payload["address"])
        if validation_error:
            st.warning(validation_error)
        else:
            try:
                api_client.create_customer(payload)
                st.success("Customer added successfully.")
                st.rerun()
            except api_client.APIError as exc:
                st.error(f"Could not add customer: {exc}")

    st.subheader("Customer List")
    if not customers:
        st.info("No customers found. Add a customer or try a different search.")
        return
    table_columns = ["customer_id", "name", "age", "gender", "phone", "email", "address"]
    st.dataframe(
        [{column: customer.get(column, "") for column in table_columns} for customer in customers],
        column_config={"customer_id": st.column_config.NumberColumn("Customer ID"), "name": "Name", "age": st.column_config.NumberColumn("Age"), "gender": "Gender", "phone": "Phone", "email": "Email", "address": "Address"},
        hide_index=True,
        width="stretch",
    )

    customer_options = {f"{customer['name']} · ID {customer['customer_id']}": customer for customer in customers}
    edit_label = st.selectbox("Select a customer to edit", ["Choose a customer"] + list(customer_options))
    if edit_label != "Choose a customer":
        selected_customer = customer_options[edit_label]
        st.subheader(f"Edit Customer · ID {selected_customer['customer_id']}")
        submitted, payload = _customer_form(selected_customer, "edit_customer_form", "Save Changes")
        if submitted:
            validation_error = _validate_customer(payload["name"], payload["age"], payload["phone"], payload["email"], payload["address"])
            if validation_error:
                st.warning(validation_error)
            else:
                try:
                    api_client.update_customer(selected_customer["customer_id"], payload)
                    st.success("Customer updated successfully.")
                    st.rerun()
                except api_client.APIError as exc:
                    st.error(f"Could not update customer: {exc}")

    st.subheader("Delete Customer")
    delete_label = st.selectbox("Select a customer to delete", ["Choose a customer"] + list(customer_options), key="delete_customer_select")
    confirm_delete = st.checkbox("I confirm that I want to delete this customer.")
    if st.button("Delete Customer", type="secondary", disabled=delete_label == "Choose a customer" or not confirm_delete):
        selected_customer = customer_options[delete_label]
        try:
            api_client.delete_customer(selected_customer["customer_id"])
            st.success("Customer deleted successfully.")
            st.rerun()
        except api_client.APIError as exc:
            st.error(f"Could not delete customer: {exc}")