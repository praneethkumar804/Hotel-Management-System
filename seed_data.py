from datetime import date, timedelta
import random

from backend.database import get_connection, initialize_database


SEED = 20260906
START_DATE = date(2025, 1, 1)
END_DATE = date(2026, 12, 31)
CURRENT_DATE = date(2026, 9, 6)

FIRST_NAMES = ["Aarav", "Ananya", "Arjun", "Diya", "Ishaan", "Kavya", "Manish", "Meera", "Nikhil", "Pooja", "Rahul", "Riya", "Sanjay", "Shreya", "Vikram", "Aditi", "Aditya", "Lakshmi", "Neha", "Varun"]
LAST_NAMES = ["Kumar", "Sharma", "Patel", "Iyer", "Reddy", "Nair", "Menon", "Verma", "Das", "Rao", "Pillai", "Joshi", "Gupta", "Singh", "Bose"]
CITIES = ["Chennai, Tamil Nadu", "Bengaluru, Karnataka", "Mumbai, Maharashtra", "Pune, Maharashtra", "Hyderabad, Telangana", "Kochi, Kerala", "Delhi, India", "Jaipur, Rajasthan"]
ROOM_TYPES = [("Single", 2000), ("Double", 3000), ("Deluxe", 4300), ("Suite", 6500)]
SERVICES = [("Room Service", 500, "In-room dining"), ("Laundry", 300, "Laundry and pressing"), ("Food", 800, "Restaurant order"), ("Spa", 1500, "Wellness treatment"), ("Airport Pickup", 1200, "Airport transfer")]
ACTIVE_STATUSES = {"Confirmed", "Checked-In"}


def _booking_overlaps(ranges, room_id, check_in, check_out):
    return any(old_in < check_out and old_out > check_in for old_in, old_out in ranges[room_id])


def _generate_bookings(rng, customers, rooms):
    ranges = {room_id: [] for room_id in rooms}
    bookings = []
    attempts = 0
    while len(bookings) < 250 and attempts < 10000:
        attempts += 1
        room_id = rooms[len(bookings) % len(rooms)]
        check_in = START_DATE + timedelta(days=rng.randrange((END_DATE - START_DATE).days - 7))
        nights = rng.randint(1, 7)
        check_out = check_in + timedelta(days=nights)
        if check_out > END_DATE:
            continue
        if check_in < CURRENT_DATE:
            status = rng.choices(["Checked-Out", "Cancelled", "Checked-In"], [78, 17, 5])[0]
        else:
            status = rng.choices(["Confirmed", "Cancelled"], [92, 8])[0]
        if status in ACTIVE_STATUSES and _booking_overlaps(ranges, room_id, check_in, check_out):
            continue
        if status in ACTIVE_STATUSES:
            ranges[room_id].append((check_in, check_out))
        bookings.append((rng.choice(customers), room_id, check_in, check_out, rng.randint(1, 4), status))
    if len(bookings) != 250:
        raise RuntimeError("Could not generate 250 valid non-overlapping bookings")
    return bookings


def seed():
    initialize_database()
    rng = random.Random(SEED)
    connection = get_connection()
    try:
        connection.execute("BEGIN")
        connection.execute("DELETE FROM booking_services")
        connection.execute("DELETE FROM payments")
        connection.execute("DELETE FROM bookings")
        connection.execute("DELETE FROM services")
        connection.execute("DELETE FROM rooms")
        connection.execute("DELETE FROM customers")

        customers = []
        for index in range(150):
            name = f"{FIRST_NAMES[index % len(FIRST_NAMES)]} {LAST_NAMES[(index * 3) % len(LAST_NAMES)]}"
            email = f"{name.lower().replace(' ', '.')}{index + 1}@example.com"
            phone = f"900000{index + 1000:04d}"
            cursor = connection.execute("INSERT INTO customers (name, age, gender, phone, email, address) VALUES (?, ?, ?, ?, ?, ?)", (name, rng.randint(18, 70), rng.choice(["Female", "Male", "Other"]), phone, email, CITIES[index % len(CITIES)]))
            customers.append(cursor.lastrowid)

        rooms = []
        for index in range(30):
            room_type, base_price = ROOM_TYPES[index % len(ROOM_TYPES)]
            room_number = f"{(index // 10 + 1) * 100 + index % 10 + 1}"
            price = base_price + rng.randrange(-200, 301, 100)
            status = rng.choices(["Available", "Occupied", "Maintenance"], [23, 5, 2])[0]
            cursor = connection.execute("INSERT INTO rooms (room_number, room_type, price_per_night, room_status) VALUES (?, ?, ?, ?)", (room_number, room_type, price, status))
            rooms.append(cursor.lastrowid)

        service_ids = []
        for name, price, description in SERVICES:
            cursor = connection.execute("INSERT INTO services (service_name, price, description, service_status) VALUES (?, ?, ?, ?)", (name, price, description, "Active"))
            service_ids.append(cursor.lastrowid)

        bookings = _generate_bookings(rng, customers, rooms)
        booking_ids = []
        booking_details = []
        for customer_id, room_id, check_in, check_out, guests, status in bookings:
            cursor = connection.execute("INSERT INTO bookings (customer_id, room_id, check_in_date, check_out_date, number_of_guests, booking_status) VALUES (?, ?, ?, ?, ?, ?)", (customer_id, room_id, check_in.isoformat(), check_out.isoformat(), guests, status))
            booking_ids.append(cursor.lastrowid)
            price = connection.execute("SELECT price_per_night FROM rooms WHERE room_id = ?", (room_id,)).fetchone()[0]
            booking_details.append((cursor.lastrowid, customer_id, check_in, check_out, price))

        for booking_id, customer_id, check_in, check_out, room_price in rng.sample(booking_details, 180):
            nights = (check_out - check_in).days
            payment_date = check_in + timedelta(days=rng.randrange(nights))
            amount = round(room_price * nights * rng.uniform(0.45, 1.05), 2)
            status = rng.choices(["Paid", "Pending", "Failed"], [75, 15, 10])[0]
            connection.execute("INSERT INTO payments (booking_id, customer_id, amount, payment_method, payment_date, payment_status) VALUES (?, ?, ?, ?, ?, ?)", (booking_id, customer_id, amount, rng.choice(["Cash", "UPI", "Card", "Net Banking"]), payment_date.isoformat(), status))

        selected_pairs = set()
        for booking_id in rng.sample(booking_ids, 125):
            service_id = rng.choice(service_ids)
            if (booking_id, service_id) in selected_pairs:
                continue
            selected_pairs.add((booking_id, service_id))
            connection.execute("INSERT INTO booking_services (booking_id, service_id, quantity) VALUES (?, ?, ?)", (booking_id, service_id, rng.randint(1, 5)))

        connection.commit()
    except Exception:
        connection.rollback()
        raise
    finally:
        connection.close()


if __name__ == "__main__":
    seed()
    print("Sample data reset and regenerated successfully.")
