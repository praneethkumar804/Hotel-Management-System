import sqlite3

from fastapi import APIRouter, HTTPException, Query

from backend.crud import row_as_dict, rows_as_dicts
from backend.database import get_connection
from backend.schemas import RoomCreate

router = APIRouter(prefix="/rooms", tags=["Rooms"])


@router.get("")
def list_rooms():
    connection = get_connection()
    try:
        return rows_as_dicts(connection.execute("SELECT * FROM rooms ORDER BY room_number").fetchall())
    finally:
        connection.close()


@router.get("/available")
def available_rooms(room_type: str | None = None, check_in_date: str | None = None, check_out_date: str | None = None):
    connection = get_connection()
    try:
        conditions = ["r.room_status = 'Available'"]
        parameters: list = []
        if room_type:
            conditions.append("r.room_type = ?")
            parameters.append(room_type)
        if check_in_date and check_out_date:
            conditions.append(
                "NOT EXISTS (SELECT 1 FROM bookings b WHERE b.room_id = r.room_id AND b.booking_status NOT IN ('Cancelled', 'Checked-Out') AND b.check_in_date < ? AND b.check_out_date > ?)"
            )
            parameters.extend([check_out_date, check_in_date])
        sql = f"SELECT r.* FROM rooms r WHERE {' AND '.join(conditions)} ORDER BY r.room_number"
        return rows_as_dicts(connection.execute(sql, parameters).fetchall())
    finally:
        connection.close()


@router.get("/{room_id}")
def get_room(room_id: int):
    connection = get_connection()
    try:
        row = connection.execute("SELECT * FROM rooms WHERE room_id = ?", (room_id,)).fetchone()
        if row is None:
            raise HTTPException(status_code=404, detail="Room not found")
        return row_as_dict(row)
    finally:
        connection.close()


@router.post("", status_code=201)
def create_room(payload: RoomCreate):
    connection = get_connection()
    try:
        cursor = connection.execute(
            "INSERT INTO rooms (room_number, room_type, price_per_night, room_status) VALUES (?, ?, ?, ?)",
            tuple(payload.model_dump().values()),
        )
        connection.commit()
        return get_room(cursor.lastrowid)
    except sqlite3.IntegrityError:
        raise HTTPException(status_code=409, detail="Room number already exists")
    finally:
        connection.close()


@router.put("/{room_id}")
def update_room(room_id: int, payload: RoomCreate):
    connection = get_connection()
    try:
        cursor = connection.execute(
            "UPDATE rooms SET room_number = ?, room_type = ?, price_per_night = ?, room_status = ? WHERE room_id = ?",
            (*tuple(payload.model_dump().values()), room_id),
        )
        if cursor.rowcount == 0:
            raise HTTPException(status_code=404, detail="Room not found")
        connection.commit()
        return row_as_dict(connection.execute("SELECT * FROM rooms WHERE room_id = ?", (room_id,)).fetchone())
    except sqlite3.IntegrityError:
        raise HTTPException(status_code=409, detail="Room number already exists")
    finally:
        connection.close()


@router.delete("/{room_id}")
def delete_room(room_id: int):
    connection = get_connection()
    try:
        cursor = connection.execute("DELETE FROM rooms WHERE room_id = ?", (room_id,))
        if cursor.rowcount == 0:
            raise HTTPException(status_code=404, detail="Room not found")
        connection.commit()
        return {"message": "Room deleted"}
    except sqlite3.IntegrityError:
        raise HTTPException(status_code=400, detail="Room is referenced by an existing booking")
    finally:
        connection.close()