import sqlite3

from fastapi import APIRouter, HTTPException

from backend.crud import row_as_dict, rows_as_dicts
from backend.database import get_connection
from backend.schemas import BookingCreate, BookingServiceCreate

router = APIRouter(prefix="/bookings", tags=["Bookings"])
BOOKING_SELECT = """
    SELECT b.booking_id, b.customer_id, c.name AS customer_name, b.room_id,
           r.room_number, r.room_type, b.check_in_date, b.check_out_date,
           b.number_of_guests, b.booking_status
    FROM bookings b JOIN customers c ON c.customer_id = b.customer_id
    JOIN rooms r ON r.room_id = b.room_id
"""


def _booking_row(connection, booking_id: int):
    return connection.execute(BOOKING_SELECT + " WHERE b.booking_id = ?", (booking_id,)).fetchone()


def _sync_room_status(connection, room_id: int):
    """Keep physical occupancy aligned with checked-in bookings without touching maintenance rooms."""
    checked_in = connection.execute(
        "SELECT 1 FROM bookings WHERE room_id = ? AND booking_status = 'Checked-In' LIMIT 1",
        (room_id,),
    ).fetchone()
    if checked_in:
        connection.execute("UPDATE rooms SET room_status = 'Occupied' WHERE room_id = ? AND room_status != 'Maintenance'", (room_id,))
    else:
        connection.execute("UPDATE rooms SET room_status = 'Available' WHERE room_id = ? AND room_status != 'Maintenance'", (room_id,))


def _check_booking_dependencies(connection, payload: BookingCreate, current_id: int | None = None):
    if connection.execute("SELECT 1 FROM customers WHERE customer_id = ?", (payload.customer_id,)).fetchone() is None:
        raise HTTPException(status_code=404, detail="Customer not found")
    room = connection.execute("SELECT room_status FROM rooms WHERE room_id = ?", (payload.room_id,)).fetchone()
    if room is None:
        raise HTTPException(status_code=404, detail="Room not found")
    if room["room_status"] == "Maintenance":
        raise HTTPException(status_code=409, detail="This room is currently under maintenance")
    if room["room_status"] == "Occupied" and current_id is None:
        raise HTTPException(status_code=409, detail="This room is currently occupied")
    parameters = [payload.room_id, payload.check_out_date.isoformat(), payload.check_in_date.isoformat()]
    sql = "SELECT booking_id FROM bookings WHERE room_id = ? AND booking_status NOT IN ('Cancelled', 'Checked-Out') AND check_in_date < ? AND check_out_date > ?"
    if current_id is not None:
        sql += " AND booking_id != ?"
        parameters.append(current_id)
    if connection.execute(sql, parameters).fetchone() is not None:
        raise HTTPException(status_code=409, detail="Room is unavailable for the selected dates")


@router.get("")
def list_bookings():
    connection = get_connection()
    try:
        return rows_as_dicts(connection.execute(BOOKING_SELECT + " ORDER BY b.booking_id DESC").fetchall())
    finally:
        connection.close()


@router.get("/filter")
def filter_bookings(booking_status: str | None = None, customer_id: int | None = None, room_id: int | None = None, check_in_date: str | None = None, check_out_date: str | None = None):
    connection = get_connection()
    try:
        conditions = []
        parameters = []
        for column, value in (("b.booking_status", booking_status), ("b.customer_id", customer_id), ("b.room_id", room_id), ("b.check_in_date", check_in_date), ("b.check_out_date", check_out_date)):
            if value is not None:
                conditions.append(f"{column} = ?")
                parameters.append(value)
        sql = BOOKING_SELECT
        if conditions:
            sql += " WHERE " + " AND ".join(conditions)
        sql += " ORDER BY b.booking_id DESC"
        return rows_as_dicts(connection.execute(sql, parameters).fetchall())
    finally:
        connection.close()


@router.get("/{booking_id}")
def get_booking(booking_id: int):
    connection = get_connection()
    try:
        row = _booking_row(connection, booking_id)
        if row is None:
            raise HTTPException(status_code=404, detail="Booking not found")
        return row_as_dict(row)
    finally:
        connection.close()


@router.post("", status_code=201)
def create_booking(payload: BookingCreate):
    connection = get_connection()
    try:
        _check_booking_dependencies(connection, payload)
        cursor = connection.execute(
            "INSERT INTO bookings (customer_id, room_id, check_in_date, check_out_date, number_of_guests, booking_status) VALUES (?, ?, ?, ?, ?, ?)",
            (payload.customer_id, payload.room_id, payload.check_in_date.isoformat(), payload.check_out_date.isoformat(), payload.number_of_guests, payload.booking_status),
        )
        _sync_room_status(connection, payload.room_id)
        connection.commit()
        return row_as_dict(_booking_row(connection, cursor.lastrowid))
    finally:
        connection.close()


@router.put("/{booking_id}")
def update_booking(booking_id: int, payload: BookingCreate):
    connection = get_connection()
    try:
        existing = _booking_row(connection, booking_id)
        if existing is None:
            raise HTTPException(status_code=404, detail="Booking not found")
        _check_booking_dependencies(connection, payload, booking_id)
        connection.execute(
            "UPDATE bookings SET customer_id = ?, room_id = ?, check_in_date = ?, check_out_date = ?, number_of_guests = ?, booking_status = ? WHERE booking_id = ?",
            (payload.customer_id, payload.room_id, payload.check_in_date.isoformat(), payload.check_out_date.isoformat(), payload.number_of_guests, payload.booking_status, booking_id),
        )
        if existing["room_id"] != payload.room_id:
            _sync_room_status(connection, existing["room_id"])
        _sync_room_status(connection, payload.room_id)
        connection.commit()
        return row_as_dict(_booking_row(connection, booking_id))
    finally:
        connection.close()


@router.delete("/{booking_id}")
def delete_booking(booking_id: int):
    connection = get_connection()
    try:
        booking = connection.execute("SELECT room_id FROM bookings WHERE booking_id = ?", (booking_id,)).fetchone()
        cursor = connection.execute("DELETE FROM bookings WHERE booking_id = ?", (booking_id,))
        if cursor.rowcount == 0:
            raise HTTPException(status_code=404, detail="Booking not found")
        _sync_room_status(connection, booking["room_id"])
        connection.commit()
        return {"message": "Booking deleted"}
    except sqlite3.IntegrityError:
        raise HTTPException(status_code=400, detail="Booking is referenced by a payment or service")
    finally:
        connection.close()


@router.get("/{booking_id}/services")
def list_booking_services(booking_id: int):
    connection = get_connection()
    try:
        rows = connection.execute(
            "SELECT bs.booking_service_id, bs.booking_id, bs.service_id, s.service_name, s.price, bs.quantity, s.price * bs.quantity AS total FROM booking_services bs JOIN services s ON s.service_id = bs.service_id WHERE bs.booking_id = ? ORDER BY bs.booking_service_id",
            (booking_id,),
        ).fetchall()
        return rows_as_dicts(rows)
    finally:
        connection.close()


@router.post("/{booking_id}/services", status_code=201)
def add_booking_service(booking_id: int, payload: BookingServiceCreate):
    connection = get_connection()
    try:
        if connection.execute("SELECT 1 FROM bookings WHERE booking_id = ?", (booking_id,)).fetchone() is None:
            raise HTTPException(status_code=404, detail="Booking not found")
        service = connection.execute("SELECT service_id, service_name, price, service_status FROM services WHERE service_id = ?", (payload.service_id,)).fetchone()
        if service is None:
            raise HTTPException(status_code=404, detail="Service not found")
        if service["service_status"] != "Active":
            raise HTTPException(status_code=409, detail="This service is currently unavailable")
        existing = connection.execute("SELECT booking_service_id FROM booking_services WHERE booking_id = ? AND service_id = ?", (booking_id, payload.service_id)).fetchone()
        if existing:
            connection.execute("UPDATE booking_services SET quantity = quantity + ? WHERE booking_service_id = ?", (payload.quantity, existing["booking_service_id"]))
            booking_service_id = existing["booking_service_id"]
        else:
            cursor = connection.execute("INSERT INTO booking_services (booking_id, service_id, quantity) VALUES (?, ?, ?)", (booking_id, payload.service_id, payload.quantity))
            booking_service_id = cursor.lastrowid
        connection.commit()
        row = connection.execute("SELECT bs.booking_service_id, bs.booking_id, bs.service_id, s.service_name, s.price, bs.quantity, s.price * bs.quantity AS total FROM booking_services bs JOIN services s ON s.service_id = bs.service_id WHERE bs.booking_service_id = ?", (booking_service_id,)).fetchone()
        return row_as_dict(row)
    finally:
        connection.close()


