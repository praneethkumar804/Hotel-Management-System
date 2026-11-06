# Entity Relationship Diagram

```mermaid
erDiagram
    USERS { int user_id PK; string username; string password_hash }
    CUSTOMERS { int customer_id PK; string name; int age; string gender; string phone; string email; string address }
    ROOMS { int room_id PK; string room_number; string room_type; float price_per_night; string room_status }
    BOOKINGS { int booking_id PK; int customer_id FK; int room_id FK; date check_in_date; date check_out_date; int number_of_guests; string booking_status }
    PAYMENTS { int payment_id PK; int booking_id FK; int customer_id FK; float amount; string payment_method; date payment_date; string payment_status }
    SERVICES { int service_id PK; string service_name; float price; string description; string service_status }
    BOOKING_SERVICES { int booking_service_id PK; int booking_id FK; int service_id FK; int quantity }
    CUSTOMERS ||--o{ BOOKINGS : makes
    ROOMS ||--o{ BOOKINGS : hosts
    BOOKINGS ||--o{ PAYMENTS : has
    CUSTOMERS ||--o{ PAYMENTS : makes
    BOOKINGS ||--o{ BOOKING_SERVICES : includes
    SERVICES ||--o{ BOOKING_SERVICES : offers
```