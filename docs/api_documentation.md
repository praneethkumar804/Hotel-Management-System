# API Documentation

The FastAPI Swagger UI is available at `/docs` while the backend runs. All JSON bodies are validated by Pydantic.

| Area | Methods and paths |
|---|---|
| Auth | `POST /api/auth/login` |
| Dashboard | `GET /api/dashboard/stats` |
| Customers | `GET/POST /api/customers`, `GET/PUT/DELETE /api/customers/{id}` |
| Rooms | `GET/POST /api/rooms`, `GET/PUT/DELETE /api/rooms/{id}`, `GET /api/rooms/available` |
| Bookings | `GET/POST /api/bookings`, `GET/PUT/DELETE /api/bookings/{id}`, `GET /api/bookings/filter` |
| Payments | `GET/POST /api/payments`, `GET/PUT/DELETE /api/payments/{id}` |
| Services | `GET/POST /api/services`, `GET/PUT/DELETE /api/services/{id}` |
| Booking services | `GET/POST /api/bookings/{id}/services`, `PUT/DELETE /api/booking-services/{id}` |
| Reports | `GET /api/reports/revenue`, `/monthly-revenue`, `/most-booked-room`, `/customer-booking-history/{id}`, `/customer-payment-history/{id}` |

Errors use `400` for invalid related data, `401` for invalid login, `404` for missing records, `409` for duplicates or unavailable rooms, and `422` for Pydantic validation failures.