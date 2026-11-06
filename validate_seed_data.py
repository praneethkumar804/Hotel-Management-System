from datetime import date

from backend.database import get_connection


START_DATE = date(2025, 1, 1)
END_DATE = date(2026, 12, 31)
TABLES = ("customers", "rooms", "bookings", "payments", "services", "booking_services")


def validate():
    connection = get_connection()
    errors = []
    try:
        counts = {table: connection.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0] for table in TABLES}
        bookings = connection.execute("SELECT booking_id, customer_id, room_id, check_in_date, check_out_date, booking_status FROM bookings").fetchall()
        payments = connection.execute("SELECT p.payment_id, p.booking_id, p.customer_id, p.payment_date, p.amount, b.customer_id AS booking_customer_id FROM payments p LEFT JOIN bookings b ON b.booking_id = p.booking_id").fetchall()
        overlaps = connection.execute("SELECT a.booking_id FROM bookings a JOIN bookings b ON a.room_id = b.room_id AND a.booking_id < b.booking_id WHERE a.booking_status IN ('Confirmed', 'Checked-In') AND b.booking_status IN ('Confirmed', 'Checked-In') AND a.check_in_date < b.check_out_date AND a.check_out_date > b.check_in_date").fetchall()
        checks = {
            "customer_count": counts["customers"] >= 100,
            "room_count": counts["rooms"] >= 30,
            "booking_count": counts["bookings"] >= 200,
            "payment_count": 150 <= counts["payments"] <= 200,
            "service_count": counts["services"] == 5,
            "booking_service_count": 100 <= counts["booking_services"] <= 150,
            "booking_dates": all(START_DATE <= date.fromisoformat(row["check_in_date"]) <= END_DATE and START_DATE <= date.fromisoformat(row["check_out_date"]) <= END_DATE and row["check_out_date"] > row["check_in_date"] for row in bookings),
            "payment_dates": all(START_DATE <= date.fromisoformat(row["payment_date"]) <= END_DATE for row in payments),
            "no_active_overlaps": not overlaps,
            "booking_customers": connection.execute("SELECT COUNT(*) FROM bookings b LEFT JOIN customers c ON c.customer_id = b.customer_id WHERE c.customer_id IS NULL").fetchone()[0] == 0,
            "booking_rooms": connection.execute("SELECT COUNT(*) FROM bookings b LEFT JOIN rooms r ON r.room_id = b.room_id WHERE r.room_id IS NULL").fetchone()[0] == 0,
            "payment_bookings": connection.execute("SELECT COUNT(*) FROM payments p LEFT JOIN bookings b ON b.booking_id = p.booking_id WHERE b.booking_id IS NULL").fetchone()[0] == 0,
            "payment_customers": connection.execute("SELECT COUNT(*) FROM payments p LEFT JOIN customers c ON c.customer_id = p.customer_id WHERE c.customer_id IS NULL").fetchone()[0] == 0,
            "payment_customer_match": all(row["customer_id"] == row["booking_customer_id"] for row in payments),
            "booking_service_bookings": connection.execute("SELECT COUNT(*) FROM booking_services bs LEFT JOIN bookings b ON b.booking_id = bs.booking_id WHERE b.booking_id IS NULL").fetchone()[0] == 0,
            "booking_service_services": connection.execute("SELECT COUNT(*) FROM booking_services bs LEFT JOIN services s ON s.service_id = bs.service_id WHERE s.service_id IS NULL").fetchone()[0] == 0,
            "unique_rooms": connection.execute("SELECT COUNT(*) = COUNT(DISTINCT room_number) FROM rooms").fetchone()[0] == 1,
            "unique_emails": connection.execute("SELECT COUNT(*) = COUNT(DISTINCT email) FROM customers").fetchone()[0] == 1,
            "unique_phones": connection.execute("SELECT COUNT(*) = COUNT(DISTINCT phone) FROM customers").fetchone()[0] == 1,
            "positive_payments": connection.execute("SELECT COUNT(*) FROM payments WHERE amount <= 0").fetchone()[0] == 0,
            "positive_services": connection.execute("SELECT COUNT(*) FROM services WHERE price <= 0").fetchone()[0] == 0,
            "positive_quantities": connection.execute("SELECT COUNT(*) FROM booking_services WHERE quantity <= 0").fetchone()[0] == 0,
        }
        errors.extend(name for name, passed in checks.items() if not passed)
        booking_range = connection.execute("SELECT MIN(check_in_date), MAX(check_out_date) FROM bookings").fetchone()
        payment_range = connection.execute("SELECT MIN(payment_date), MAX(payment_date) FROM payments").fetchone()
        labels = [("Customers", "customer_count"), ("Rooms", "room_count"), ("Bookings", "booking_count"), ("Payments", "payment_count"), ("Services", "service_count"), ("Booking Services", "booking_service_count")]
        print("================================")
        print("HOTEL DATA VALIDATION")
        print("================================")
        for label, check in labels:
            print(f"{label:20} {counts[label.lower().replace(' ', '_')]:3} {'✓' if checks[check] else '✗'}")
        print(f"Bookings: {booking_range[0]} to {booking_range[1]}")
        print(f"Payments: {payment_range[0]} to {payment_range[1]}")
        for name, passed in checks.items():
            print(f"{name.replace('_', ' ').title():28} {'✓' if passed else '✗'}")
        if errors:
            print("\nDATABASE VALIDATION FAILED")
            raise SystemExit(1)
        print("\nDATABASE VALIDATION PASSED")
        print("================================")
    finally:
        connection.close()


if __name__ == "__main__":
    validate()
