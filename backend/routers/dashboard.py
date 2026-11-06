from fastapi import APIRouter

from backend.database import get_connection

router = APIRouter(prefix="/dashboard", tags=["Dashboard"])


@router.get("/stats")
def dashboard_stats():
    connection = get_connection()
    try:
        counts = connection.execute("SELECT (SELECT COUNT(*) FROM customers) AS total_customers, (SELECT COUNT(*) FROM rooms) AS total_rooms, (SELECT COUNT(*) FROM bookings) AS total_bookings, (SELECT COUNT(*) FROM bookings WHERE booking_status = 'Confirmed') AS confirmed_bookings, (SELECT COUNT(*) FROM bookings WHERE booking_status = 'Checked-In') AS checked_in_bookings, (SELECT COUNT(*) FROM bookings WHERE booking_status = 'Checked-Out') AS checked_out_bookings, (SELECT COUNT(*) FROM bookings WHERE booking_status = 'Cancelled') AS cancelled_bookings, (SELECT COALESCE(SUM(amount), 0) FROM payments WHERE payment_status = 'Paid') AS total_revenue, (SELECT COUNT(*) FROM rooms WHERE room_status = 'Available') AS available_rooms, (SELECT COUNT(*) FROM rooms WHERE room_status = 'Occupied') AS occupied_rooms, (SELECT COUNT(*) FROM rooms WHERE room_status = 'Maintenance') AS maintenance_rooms, (SELECT COUNT(*) FROM payments WHERE payment_status = 'Pending') AS pending_payments").fetchone()
        return dict(counts)
    finally:
        connection.close()