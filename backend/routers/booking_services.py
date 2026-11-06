from fastapi import APIRouter, HTTPException

from backend.crud import row_as_dict
from backend.database import get_connection
from backend.schemas import BookingServiceCreate

router = APIRouter(prefix="/booking-services", tags=["Booking Services"])


@router.put("/{booking_service_id}")
def update_booking_service(booking_service_id: int, payload: BookingServiceCreate):
    connection = get_connection()
    try:
        service = connection.execute("SELECT service_status FROM services WHERE service_id = ?", (payload.service_id,)).fetchone()
        if service is None:
            raise HTTPException(status_code=404, detail="Service not found")
        if service["service_status"] != "Active":
            raise HTTPException(status_code=409, detail="This service is currently unavailable")
        cursor = connection.execute("UPDATE booking_services SET service_id = ?, quantity = ? WHERE booking_service_id = ?", (payload.service_id, payload.quantity, booking_service_id))
        if cursor.rowcount == 0:
            raise HTTPException(status_code=404, detail="Booking service not found")
        connection.commit()
        row = connection.execute("SELECT bs.booking_service_id, bs.booking_id, bs.service_id, s.service_name, s.price, bs.quantity, s.price * bs.quantity AS total FROM booking_services bs JOIN services s ON s.service_id = bs.service_id WHERE bs.booking_service_id = ?", (booking_service_id,)).fetchone()
        return row_as_dict(row)
    finally:
        connection.close()


@router.delete("/{booking_service_id}")
def delete_booking_service(booking_service_id: int):
    connection = get_connection()
    try:
        cursor = connection.execute("DELETE FROM booking_services WHERE booking_service_id = ?", (booking_service_id,))
        if cursor.rowcount == 0:
            raise HTTPException(status_code=404, detail="Booking service not found")
        connection.commit()
        return {"message": "Booking service deleted"}
    finally:
        connection.close()