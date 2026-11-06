from datetime import date

from fastapi import APIRouter, HTTPException

from backend.crud import rows_as_dicts
from backend.database import get_connection

router = APIRouter(prefix="/reports", tags=["Reports"])


def _date_conditions(start_date: str | None, end_date: str | None):
    for value in (start_date, end_date):
        if value:
            try:
                date.fromisoformat(value)
            except ValueError as exc:
                raise HTTPException(status_code=400, detail="Report dates must use YYYY-MM-DD format.") from exc
    if start_date and end_date and start_date > end_date:
        raise HTTPException(status_code=400, detail="Start date must be before or equal to end date.")
    conditions = []
    parameters = []
    if start_date:
        conditions.append("payment_date >= ?")
        parameters.append(start_date)
    if end_date:
        conditions.append("payment_date <= ?")
        parameters.append(end_date)
    return (" AND " + " AND ".join(conditions)) if conditions else "", parameters


@router.get("/revenue")
def revenue_report(start_date: str | None = None, end_date: str | None = None):
    connection = get_connection()
    try:
        date_sql, date_parameters = _date_conditions(start_date, end_date)
        row = connection.execute(f"SELECT COALESCE(SUM(CASE WHEN payment_status = ? THEN amount ELSE 0 END), 0) AS total_revenue, COALESCE(SUM(CASE WHEN payment_status = ? THEN 1 ELSE 0 END), 0) AS paid_payments, COALESCE(SUM(CASE WHEN payment_status = ? THEN 1 ELSE 0 END), 0) AS pending_payments, COALESCE(SUM(CASE WHEN payment_status = ? THEN 1 ELSE 0 END), 0) AS failed_payments, COALESCE(SUM(CASE WHEN payment_status = ? THEN amount ELSE 0 END), 0) AS pending_amount, COALESCE(SUM(CASE WHEN payment_status = ? THEN amount ELSE 0 END), 0) AS failed_amount, COALESCE(SUM(amount), 0) AS total_payment_amount FROM payments WHERE 1 = 1{date_sql}", ("Paid", "Paid", "Pending", "Failed", "Pending", "Failed", *date_parameters)).fetchone()
        result = dict(row)
        result["paid_payments"] = result["paid_payments"] or 0
        result["pending_payments"] = result["pending_payments"] or 0
        result["failed_payments"] = result["failed_payments"] or 0
        result["paid_transactions"] = result["paid_payments"]
        return result
    finally:
        connection.close()


@router.get("/monthly-revenue")
def monthly_revenue(start_date: str | None = None, end_date: str | None = None):
    connection = get_connection()
    try:
        date_sql, date_parameters = _date_conditions(start_date, end_date)
        rows = connection.execute(f"SELECT strftime('%Y-%m', payment_date) AS month, COALESCE(SUM(amount), 0) AS revenue FROM payments WHERE payment_status = ?{date_sql} GROUP BY strftime('%Y-%m', payment_date) ORDER BY month", ("Paid", *date_parameters)).fetchall()
        return rows_as_dicts(rows)
    finally:
        connection.close()


@router.get("/most-booked-room")
def most_booked_room():
    connection = get_connection()
    try:
        row = connection.execute("SELECT r.room_id, r.room_number, r.room_type, COUNT(b.booking_id) AS booking_count FROM rooms r JOIN bookings b ON b.room_id = r.room_id WHERE b.booking_status != ? GROUP BY r.room_id, r.room_number, r.room_type ORDER BY booking_count DESC, r.room_number LIMIT 1", ("Cancelled",)).fetchone()
        return dict(row) if row else {}
    finally:
        connection.close()


@router.get("/customer-booking-history/{customer_id}")
def customer_booking_history(customer_id: int):
    connection = get_connection()
    try:
        if connection.execute("SELECT 1 FROM customers WHERE customer_id = ?", (customer_id,)).fetchone() is None:
            raise HTTPException(status_code=404, detail="Customer not found")
        rows = connection.execute("SELECT b.booking_id, c.name AS customer_name, r.room_number, r.room_type, b.check_in_date, b.check_out_date, b.number_of_guests, b.booking_status FROM bookings b JOIN customers c ON c.customer_id = b.customer_id JOIN rooms r ON r.room_id = b.room_id WHERE b.customer_id = ? ORDER BY b.check_in_date DESC", (customer_id,)).fetchall()
        return rows_as_dicts(rows)
    finally:
        connection.close()


@router.get("/customer-payment-history/{customer_id}")
def customer_payment_history(customer_id: int):
    connection = get_connection()
    try:
        if connection.execute("SELECT 1 FROM customers WHERE customer_id = ?", (customer_id,)).fetchone() is None:
            raise HTTPException(status_code=404, detail="Customer not found")
        rows = connection.execute("SELECT p.payment_id, p.booking_id, c.name AS customer_name, p.amount, p.payment_method, p.payment_date, p.payment_status FROM payments p JOIN customers c ON c.customer_id = p.customer_id JOIN bookings b ON b.booking_id = p.booking_id WHERE p.customer_id = ? ORDER BY p.payment_date DESC", (customer_id,)).fetchall()
        return rows_as_dicts(rows)
    finally:
        connection.close()


@router.get("/room-booking-summary")
def room_booking_summary():
    connection = get_connection()
    try:
        rows = connection.execute("SELECT r.room_id, r.room_number, r.room_type, COUNT(CASE WHEN b.booking_status != ? THEN b.booking_id END) AS booking_count FROM rooms r LEFT JOIN bookings b ON b.room_id = r.room_id GROUP BY r.room_id, r.room_number, r.room_type ORDER BY booking_count DESC, r.room_number", ("Cancelled",)).fetchall()
        return rows_as_dicts(rows)
    finally:
        connection.close()


@router.get("/customer-summary")
def customer_summary():
    connection = get_connection()
    try:
        rows = connection.execute("SELECT c.customer_id, c.name AS customer_name, COUNT(DISTINCT b.booking_id) AS booking_count, COALESCE((SELECT SUM(p.amount) FROM payments p WHERE p.customer_id = c.customer_id AND p.payment_status = ?), 0) AS total_paid_amount FROM customers c LEFT JOIN bookings b ON b.customer_id = c.customer_id GROUP BY c.customer_id, c.name ORDER BY total_paid_amount DESC, c.name", ("Paid",)).fetchall()
        return rows_as_dicts(rows)
    finally:
        connection.close()


@router.get("/payment-status-summary")
def payment_status_summary():
    connection = get_connection()
    try:
        rows = connection.execute("SELECT payment_status, COUNT(*) AS count, COALESCE(SUM(amount), 0) AS total_amount FROM payments GROUP BY payment_status ORDER BY payment_status").fetchall()
        return rows_as_dicts(rows)
    finally:
        connection.close()


@router.get("/booking-status-summary")
def booking_status_summary():
    connection = get_connection()
    try:
        rows = connection.execute("SELECT booking_status, COUNT(*) AS count FROM bookings GROUP BY booking_status ORDER BY booking_status").fetchall()
        return rows_as_dicts(rows)
    finally:
        connection.close()