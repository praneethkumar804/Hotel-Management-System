# Hotel Management System Project Audit

Date: 2026-09-06

## Scope

Audited the existing FastAPI, Streamlit, SQLite, Pydantic, Requests, and raw SQL implementation without rebuilding the project or changing the database schema.

## Issues Found and Fixed

- Added the dedicated `GET /api/customers/search` endpoint required by the project contract.
- Added `search_customers()` to the shared API client and updated the Customers page to use it.
- Added API-client handling for successful responses containing invalid JSON.
- Removed the unused `passlib[bcrypt]` dependency. Passwords continue to use the installed `bcrypt` package.
- Added ISO date validation for report date filters with HTTP 400 responses.
- Confirmed booking-service duplicate additions merge quantity rather than creating duplicate rows.
- Confirmed inactive services cannot be newly added to bookings.
- Confirmed dependency-protected service deletion returns HTTP 409.
- Preserved the intentional `frontend/views` layout so Streamlit does not auto-discover duplicate pages.

## Database Audit

Verified `database/hotel.db` contains Users, Customers, Rooms, Bookings, Payments, Services, and Booking_Services. Primary keys, foreign keys, `NOT NULL` fields, unique room numbers, and `PRAGMA foreign_keys = ON` were verified. No production/sample records were removed.

An isolated temporary empty database test confirmed zero-safe dashboard values and empty-safe CRUD/report responses.

## Authentication Audit

Verified successful admin login, invalid username, invalid password, empty username, and empty password behavior. Password hashes are stored instead of plaintext, login responses do not expose `password_hash`, and Streamlit logout clears session state. Browser verification confirmed unauthenticated login and logout return behavior.

## API and SQL Audit

Verified OpenAPI contains 30 paths, including authentication, dashboard, all CRUD resources, booking services, filters, and reports. SQL uses parameter placeholders for user-controlled values. Dynamic SQL fragments in reports and room availability are limited to fixed internal column/condition strings; values remain parameterized.

Verified JOIN, COUNT, SUM, COALESCE, GROUP BY, ORDER BY, CASE, LEFT JOIN, WHERE, and SQLite `strftime()` report operations.

## Functional Testing

A temporary-record integration audit passed for:

- Customer create, read, update, delete, search, validation, and missing-record behavior.
- Room create, read, update, delete, duplicate-number handling, maintenance validation, and status behavior.
- Booking create, read, update, delete, missing dependencies, invalid dates, overlap conflicts, non-overlapping dates, maintenance rooms, and checked-in/checked-out room synchronization.
- Payment create, read, update, delete, amount/status validation, booking-customer relationship validation, joined responses, and paid-revenue transitions.
- Service create, read, update, delete, summary, search, filtering, and dependency protection.
- Booking-service create, joined read, duplicate quantity merging, quantity update, inactive-service rejection, total calculation, and delete.
- Dashboard/reports revenue parity and report endpoint coverage.
- Invalid report dates and missing customer history responses.

Temporary records were cleaned up after testing.

## Frontend Testing

A fresh Streamlit process was started on port 8511. Browser verification passed for login, Dashboard, Customers, Rooms, Bookings, Payments, Services, Reports, custom single-sidebar navigation, and Logout. No automatic Streamlit multipage navigation was present. Workspace diagnostics and Python compilation passed.

## Remaining Known Limitations

- Authentication is a simple Streamlit session-state approach suitable for the college-project scope, not token-based multi-user authorization.
- The project does not yet include a committed automated pytest suite; the audit used repeatable live API scripts, isolated database checks, compilation, diagnostics, OpenAPI inspection, and browser verification.
- SQLite schema status fields and business rules are enforced primarily through Pydantic and FastAPI logic rather than database CHECK constraints, preserving the existing schema and sample data.
- Streamlit displays currency symbols in table/metric formatting, while numeric input widgets intentionally use numeric-only formats required by Streamlit.
