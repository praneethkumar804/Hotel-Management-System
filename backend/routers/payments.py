import sqlite3

from fastapi import APIRouter, HTTPException

from backend.crud import row_as_dict, rows_as_dicts
from backend.database import get_connection
from backend.schemas import PaymentCreate

router = APIRouter(prefix="/payments", tags=["Payments"])
PAYMENT_SELECT = "SELECT p.payment_id, p.booking_id, p.customer_id, c.name AS customer_name, b.room_id, r.room_number, r.room_type, p.amount, p.payment_method, p.payment_date, p.payment_status FROM payments p JOIN customers c ON c.customer_id = p.customer_id JOIN bookings b ON b.booking_id = p.booking_id JOIN rooms r ON r.room_id = b.room_id"


@router.get("")
def list_payments(payment_status: str | None = None):
    connection = get_connection()
    try:
        sql, params = PAYMENT_SELECT, []
        if payment_status:
            sql += " WHERE p.payment_status = ?"
            params.append(payment_status)
        return rows_as_dicts(connection.execute(sql + " ORDER BY p.payment_id DESC", params).fetchall())
    finally:
        connection.close()

@router.get("/summary")
def payment_summary():
    connection = get_connection()
    try:
        row = connection.execute("SELECT COUNT(*) AS total_payments, SUM(CASE WHEN payment_status = ? THEN 1 ELSE 0 END) AS paid_payments, SUM(CASE WHEN payment_status = ? THEN 1 ELSE 0 END) AS pending_payments, SUM(CASE WHEN payment_status = ? THEN 1 ELSE 0 END) AS failed_payments, COALESCE(SUM(CASE WHEN payment_status = ? THEN amount ELSE 0 END), 0) AS total_paid_revenue FROM payments", ("Paid", "Pending", "Failed", "Paid")).fetchone()
        return dict(row)
    finally:
        connection.close()

@router.get("/filter")
def filter_payments(payment_status: str | None = None, payment_method: str | None = None, customer_id: int | None = None, booking_id: int | None = None, payment_date: str | None = None):
    connection = get_connection()
    try:
        conditions = []
        parameters = []
        for column, value in (("p.payment_status", payment_status), ("p.payment_method", payment_method), ("p.customer_id", customer_id), ("p.booking_id", booking_id), ("p.payment_date", payment_date)):
            if value is not None:
                conditions.append(f"{column} = ?")
                parameters.append(value)
        sql = PAYMENT_SELECT
        if conditions:
            sql += " WHERE " + " AND ".join(conditions)
        return rows_as_dicts(connection.execute(sql + " ORDER BY p.payment_id DESC", parameters).fetchall())
    finally:
        connection.close()


@router.get("/{payment_id}")
def get_payment(payment_id: int):
    connection = get_connection()
    try:
        row = connection.execute(PAYMENT_SELECT + " WHERE p.payment_id = ?", (payment_id,)).fetchone()
        if row is None:
            raise HTTPException(status_code=404, detail="Payment not found")
        return row_as_dict(row)
    finally:
        connection.close()


def _validate_payment(connection, payload: PaymentCreate):
    if connection.execute("SELECT 1 FROM bookings WHERE booking_id = ?", (payload.booking_id,)).fetchone() is None:
        raise HTTPException(status_code=404, detail="Booking not found")
    if connection.execute("SELECT 1 FROM customers WHERE customer_id = ?", (payload.customer_id,)).fetchone() is None:
        raise HTTPException(status_code=404, detail="Customer not found")
    relationship = connection.execute("SELECT 1 FROM bookings WHERE booking_id = ? AND customer_id = ?", (payload.booking_id, payload.customer_id)).fetchone()
    if relationship is None:
        raise HTTPException(status_code=409, detail="Selected customer does not belong to this booking")


@router.post("", status_code=201)
def create_payment(payload: PaymentCreate):
    connection = get_connection()
    try:
        _validate_payment(connection, payload)
        cursor = connection.execute("INSERT INTO payments (booking_id, customer_id, amount, payment_method, payment_date, payment_status) VALUES (?, ?, ?, ?, ?, ?)", (payload.booking_id, payload.customer_id, payload.amount, payload.payment_method, payload.payment_date.isoformat(), payload.payment_status))
        connection.commit()
        return get_payment(cursor.lastrowid)
    finally:
        connection.close()


@router.put("/{payment_id}")
def update_payment(payment_id: int, payload: PaymentCreate):
    connection = get_connection()
    try:
        _validate_payment(connection, payload)
        cursor = connection.execute("UPDATE payments SET booking_id = ?, customer_id = ?, amount = ?, payment_method = ?, payment_date = ?, payment_status = ? WHERE payment_id = ?", (payload.booking_id, payload.customer_id, payload.amount, payload.payment_method, payload.payment_date.isoformat(), payload.payment_status, payment_id))
        if cursor.rowcount == 0:
            raise HTTPException(status_code=404, detail="Payment not found")
        connection.commit()
        return row_as_dict(connection.execute(PAYMENT_SELECT + " WHERE p.payment_id = ?", (payment_id,)).fetchone())
    finally:
        connection.close()


@router.delete("/{payment_id}")
def delete_payment(payment_id: int):
    connection = get_connection()
    try:
        cursor = connection.execute("DELETE FROM payments WHERE payment_id = ?", (payment_id,))
        if cursor.rowcount == 0:
            raise HTTPException(status_code=404, detail="Payment not found")
        connection.commit()
        return {"message": "Payment deleted"}
    finally:
        connection.close()