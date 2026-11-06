# Hotel Management System

A project hotel operations application with a Streamlit frontend, FastAPI HTTP backend, and SQLite database. Streamlit never accesses SQLite directly.

## Features

Authentication, customer/room/booking/payment/service CRUD, booking-service relationships, room availability checks, dashboard KPIs, search and filters, revenue reports, and customer histories.

## Stack and architecture

Python 3.11+, FastAPI, Uvicorn, Pydantic, raw parameterized `sqlite3`, Streamlit, Requests, and passlib/bcrypt. The flow is `Streamlit -> HTTP/JSON -> FastAPI -> SQLite`.

## Setup

```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt
python seed_data.py
```

The database is created automatically at `database/hotel.db` when FastAPI starts. Run the applications in separate terminals:

```powershell
uvicorn backend.main:app --reload
streamlit run frontend/app.py
```

Open `http://127.0.0.1:8000/docs` for Swagger and `http://localhost:8501` for Streamlit. Demo login: `admin` / `admin123`.

## Database

Tables are Users, Customers, Rooms, Bookings, Payments, Services, and Booking_Services. Customers and rooms connect to bookings; bookings connect to payments and services through the junction table. See [docs/er_diagram.md](docs/er_diagram.md).

The project demonstrates parameterized INSERT, SELECT, UPDATE, DELETE, JOIN, COUNT, SUM, GROUP BY, ORDER BY, LIKE, COALESCE, foreign keys, validation, and friendly HTTP errors. Full endpoint details are in [docs/api_documentation.md](docs/api_documentation.md).

## Future improvements

JWT or server-side sessions, role-based staff accounts, invoice generation, richer room calendar views, automated tests, and deployment configuration.