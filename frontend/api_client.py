import requests


BASE_URL = "http://127.0.0.1:8000/api"


class APIError(Exception):
    pass


def request(method: str, path: str, **kwargs):
    try:
        response = requests.request(method, f"{BASE_URL}{path}", timeout=10, **kwargs)
        if not response.ok:
            try:
                message = response.json().get("detail", response.text)
            except ValueError:
                message = response.text or "API request failed"
            raise APIError(f"{response.status_code}: {message}")
        try:
            return response.json()
        except ValueError as exc:
            raise APIError("The backend returned an invalid response.") from exc
    except requests.RequestException as exc:
        raise APIError("Cannot connect to the backend. Start FastAPI first.") from exc


def login(username, password): return request("POST", "/auth/login", json={"username": username, "password": password})
def get_dashboard_stats(): return request("GET", "/dashboard/stats")
def get_customers(query=None): return request("GET", "/customers", params={"query": query} if query else {})
def search_customers(query): return request("GET", "/customers/search", params={"query": query})
def create_customer(data): return request("POST", "/customers", json=data)
def update_customer(identifier, data): return request("PUT", f"/customers/{identifier}", json=data)
def delete_customer(identifier): return request("DELETE", f"/customers/{identifier}")
def get_rooms(): return request("GET", "/rooms")
def get_available_rooms(**params): return request("GET", "/rooms/available", params=params)
def create_room(data): return request("POST", "/rooms", json=data)
def update_room(identifier, data): return request("PUT", f"/rooms/{identifier}", json=data)
def delete_room(identifier): return request("DELETE", f"/rooms/{identifier}")
def get_bookings(): return request("GET", "/bookings")
def filter_bookings(**params): return request("GET", "/bookings/filter", params={k: v for k, v in params.items() if v is not None})
def create_booking(data): return request("POST", "/bookings", json=data)
def update_booking(identifier, data): return request("PUT", f"/bookings/{identifier}", json=data)
def delete_booking(identifier): return request("DELETE", f"/bookings/{identifier}")
def get_booking_services(identifier): return request("GET", f"/bookings/{identifier}/services")
def add_booking_service(identifier, data): return request("POST", f"/bookings/{identifier}/services", json=data)
def update_booking_service(identifier, data): return request("PUT", f"/booking-services/{identifier}", json=data)
def delete_booking_service(identifier): return request("DELETE", f"/booking-services/{identifier}")
def get_payments(status=None): return request("GET", "/payments", params={"payment_status": status} if status else {})
def create_payment(data): return request("POST", "/payments", json=data)
def update_payment(identifier, data): return request("PUT", f"/payments/{identifier}", json=data)
def delete_payment(identifier): return request("DELETE", f"/payments/{identifier}")
def get_payment(identifier): return request("GET", f"/payments/{identifier}")
def get_payment_summary(): return request("GET", "/payments/summary")
def filter_payments(**params): return request("GET", "/payments/filter", params={k: v for k, v in params.items() if v is not None})
def get_services(): return request("GET", "/services")
def get_service(identifier): return request("GET", f"/services/{identifier}")
def get_service_summary(): return request("GET", "/services/summary")
def filter_services(**params): return request("GET", "/services", params={k: v for k, v in params.items() if v is not None})
def create_service(data): return request("POST", "/services", json=data)
def update_service(identifier, data): return request("PUT", f"/services/{identifier}", json=data)
def delete_service(identifier): return request("DELETE", f"/services/{identifier}")
def get_revenue(): return request("GET", "/reports/revenue")
def get_revenue_report(start_date=None, end_date=None): return request("GET", "/reports/revenue", params={"start_date": start_date, "end_date": end_date} if start_date or end_date else {})
def get_monthly_revenue(start_date=None, end_date=None): return request("GET", "/reports/monthly-revenue", params={"start_date": start_date, "end_date": end_date} if start_date or end_date else {})
def get_most_booked_room(): return request("GET", "/reports/most-booked-room")
def get_room_booking_summary(): return request("GET", "/reports/room-booking-summary")
def get_customer_booking_history(identifier): return request("GET", f"/reports/customer-booking-history/{identifier}")
def get_customer_payment_history(identifier): return request("GET", f"/reports/customer-payment-history/{identifier}")
def get_customer_summary(): return request("GET", "/reports/customer-summary")
def get_payment_status_summary(): return request("GET", "/reports/payment-status-summary")
def get_booking_status_summary(): return request("GET", "/reports/booking-status-summary")