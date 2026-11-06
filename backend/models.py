"""Database row models are represented by sqlite3.Row objects.

This module provides shared table metadata for the raw-SQL implementation.
"""

TABLES = (
    "users",
    "customers",
    "rooms",
    "bookings",
    "payments",
    "services",
    "booking_services",
)