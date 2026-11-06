import sqlite3

from fastapi import APIRouter, HTTPException

from backend.crud import row_as_dict, rows_as_dicts
from backend.database import get_connection
from backend.schemas import CustomerCreate

router = APIRouter(prefix="/customers", tags=["Customers"])


@router.get("")
def list_customers(query: str | None = None):
    connection = get_connection()
    try:
        if query:
            value = f"%{query}%"
            rows = connection.execute(
                "SELECT * FROM customers WHERE name LIKE ? OR phone LIKE ? OR email LIKE ? ORDER BY customer_id DESC",
                (value, value, value),
            ).fetchall()
        else:
            rows = connection.execute("SELECT * FROM customers ORDER BY customer_id DESC").fetchall()
        return rows_as_dicts(rows)
    finally:
        connection.close()


@router.get("/search")
def search_customers(query: str = ""):
    return list_customers(query=query)


@router.get("/{customer_id}")
def get_customer(customer_id: int):
    connection = get_connection()
    try:
        row = connection.execute("SELECT * FROM customers WHERE customer_id = ?", (customer_id,)).fetchone()
        if row is None:
            raise HTTPException(status_code=404, detail="Customer not found")
        return row_as_dict(row)
    finally:
        connection.close()


@router.post("", status_code=201)
def create_customer(payload: CustomerCreate):
    connection = get_connection()
    try:
        cursor = connection.execute(
            "INSERT INTO customers (name, age, gender, phone, email, address) VALUES (?, ?, ?, ?, ?, ?)",
            (payload.name, payload.age, payload.gender, payload.phone, payload.email, payload.address),
        )
        connection.commit()
        return get_customer(cursor.lastrowid)
    finally:
        connection.close()


def _update_customer(customer_id: int, payload: CustomerCreate):
    connection = get_connection()
    try:
        cursor = connection.execute(
            "UPDATE customers SET name = ?, age = ?, gender = ?, phone = ?, email = ?, address = ? WHERE customer_id = ?",
            (payload.name, payload.age, payload.gender, payload.phone, payload.email, payload.address, customer_id),
        )
        if cursor.rowcount == 0:
            raise HTTPException(status_code=404, detail="Customer not found")
        connection.commit()
        row = connection.execute("SELECT * FROM customers WHERE customer_id = ?", (customer_id,)).fetchone()
        return row_as_dict(row)
    finally:
        connection.close()


@router.put("/{customer_id}")
def update_customer(customer_id: int, payload: CustomerCreate):
    return _update_customer(customer_id, payload)


@router.delete("/{customer_id}")
def delete_customer(customer_id: int):
    connection = get_connection()
    try:
        cursor = connection.execute("DELETE FROM customers WHERE customer_id = ?", (customer_id,))
        if cursor.rowcount == 0:
            raise HTTPException(status_code=404, detail="Customer not found")
        connection.commit()
        return {"message": "Customer deleted"}
    except sqlite3.IntegrityError:
        raise HTTPException(status_code=400, detail="Customer is referenced by an existing booking")
    finally:
        connection.close()