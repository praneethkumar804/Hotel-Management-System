import sqlite3

from fastapi import APIRouter, HTTPException

from backend.crud import row_as_dict, rows_as_dicts
from backend.database import get_connection
from backend.schemas import ServiceCreate

router = APIRouter(prefix="/services", tags=["Services"])


@router.get("")
def list_services(service_status: str | None = None, query: str | None = None):
    connection = get_connection()
    try:
        conditions = []
        parameters = []
        if service_status:
            conditions.append("service_status = ?")
            parameters.append(service_status)
        if query:
            conditions.append("service_name LIKE ?")
            parameters.append(f"%{query}%")
        sql = "SELECT * FROM services"
        if conditions:
            sql += " WHERE " + " AND ".join(conditions)
        return rows_as_dicts(connection.execute(sql + " ORDER BY service_name", parameters).fetchall())
    finally:
        connection.close()


@router.get("/summary")
def service_summary():
    connection = get_connection()
    try:
        row = connection.execute("SELECT COUNT(*) AS total_services, COALESCE(SUM(CASE WHEN service_status = ? THEN 1 ELSE 0 END), 0) AS active_services, COALESCE(SUM(CASE WHEN service_status = ? THEN 1 ELSE 0 END), 0) AS inactive_services FROM services", ("Active", "Inactive")).fetchone()
        return dict(row)
    finally:
        connection.close()


@router.get("/{service_id}")
def get_service(service_id: int):
    connection = get_connection()
    try:
        row = connection.execute("SELECT * FROM services WHERE service_id = ?", (service_id,)).fetchone()
        if row is None:
            raise HTTPException(status_code=404, detail="Service not found")
        return row_as_dict(row)
    finally:
        connection.close()


@router.post("", status_code=201)
def create_service(payload: ServiceCreate):
    connection = get_connection()
    try:
        cursor = connection.execute("INSERT INTO services (service_name, price, description, service_status) VALUES (?, ?, ?, ?)", (payload.service_name, payload.price, payload.description, payload.service_status))
        connection.commit()
        return get_service(cursor.lastrowid)
    finally:
        connection.close()


@router.put("/{service_id}")
def update_service(service_id: int, payload: ServiceCreate):
    connection = get_connection()
    try:
        cursor = connection.execute("UPDATE services SET service_name = ?, price = ?, description = ?, service_status = ? WHERE service_id = ?", (payload.service_name, payload.price, payload.description, payload.service_status, service_id))
        if cursor.rowcount == 0:
            raise HTTPException(status_code=404, detail="Service not found")
        connection.commit()
        return row_as_dict(connection.execute("SELECT * FROM services WHERE service_id = ?", (service_id,)).fetchone())
    finally:
        connection.close()


@router.delete("/{service_id}")
def delete_service(service_id: int):
    connection = get_connection()
    try:
        cursor = connection.execute("DELETE FROM services WHERE service_id = ?", (service_id,))
        if cursor.rowcount == 0:
            raise HTTPException(status_code=404, detail="Service not found")
        connection.commit()
        return {"message": "Service deleted"}
    except sqlite3.IntegrityError:
        raise HTTPException(status_code=409, detail="This service cannot be deleted because it is associated with existing bookings")
    finally:
        connection.close()