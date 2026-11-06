# 🏨 Nakshatra Hotel Management System

A full-stack hotel operations management application built using **Python, FastAPI, Streamlit, and SQLite**. The system provides a centralized platform to manage hotel operations, including customers, rooms, bookings, payments, additional services, and reports.

## 🚀 Features

- **Authentication:** User login and authentication.
- **Dashboard:** Hotel statistics and key performance indicators (KPIs).
- **Customer Management:** Create, view, update, and delete customer records.
- **Room Management:** Manage room details and availability.
- **Booking Management:** Create and manage hotel reservations.
- **Payment Management:** Track and manage customer payments.
- **Service Management:** Manage additional hotel services.
- **Booking Services:** Connect additional services with bookings.
- **Room Availability:** Check room availability before reservations.
- **Search and Filters:** Easily find customers, rooms, and bookings.
- **Revenue Reports:** View hotel revenue and business reports.
- **Customer History:** Access customer booking histories.

## 🛠️ Technology Stack

| Technology | Purpose |
|---|---|
| Python 3.11+ | Programming Language |
| FastAPI | Backend REST API |
| Streamlit | Frontend UI |
| SQLite | Database |
| Uvicorn | API Server |
| Pydantic | Data Validation |
| Requests | API Communication |
| Passlib / bcrypt | Password Hashing |

## 🏗️ Architecture

The application follows a frontend-backend architecture:

**Streamlit Frontend → HTTP/JSON → FastAPI Backend → SQLite Database**

The frontend communicates with the backend through REST APIs. The backend handles business logic, validation, authentication, and database operations.

## 📂 Project Structure

```text
Hotel_Management_System/
│
├── backend/
│   ├── routers/
│   ├── auth.py
│   ├── crud.py
│   ├── database.py
│   ├── main.py
│   ├── models.py
│   └── schemas.py
│
├── frontend/
│   ├── assets/
│   ├── views/
│   ├── api_client.py
│   ├── app.py
│   └── session.py
│
├── database/
├── docs/
├── screenshots/
├── requirements.txt
├── seed_data.py
├── validate_seed_data.py
└── README.md
```

## ⚙️ Installation and Setup

### 1. Clone the repository

```bash
git clone https://github.com/praneethkumar804/Hotel-Management-System.git
cd Hotel-Management-System
```

### 2. Create a virtual environment

```bash
python -m venv venv
```

### 3. Activate the virtual environment

Windows PowerShell:

```powershell
.\venv\Scripts\Activate.ps1
```

### 4. Install dependencies

```bash
pip install -r requirements.txt
```

### 5. Initialize sample data

```bash
python seed_data.py
```

### 6. Start the FastAPI backend

Open the first terminal:

```bash
uvicorn backend.main:app --reload
```

### 7. Start the Streamlit frontend

Open a second terminal:

```bash
streamlit run frontend/app.py
```

## 🌐 Application URLs

- **Frontend:** http://localhost:8501
- **Backend API:** http://127.0.0.1:8000
- **Swagger API Documentation:** http://127.0.0.1:8000/docs

## 🗄️ Database

The application uses SQLite for data storage.

Main database tables:

- Users
- Customers
- Rooms
- Bookings
- Payments
- Services
- Booking_Services

Database relationship documentation and diagrams are available in the `docs/` directory.

## 📸 Screenshots

Application screenshots are available in the `screenshots/` directory.

## 🎯 Project Objective

The objective of this project is to simplify hotel administration by digitizing daily hotel operations, reducing manual work, improving data organization, and providing an efficient reservation and management experience.

## 🔮 Future Enhancements

- Role-based access control.
- Invoice and receipt generation.
- Advanced room booking calendar.
- Automated testing.
- Cloud deployment.
- Enhanced security and session management.

## 👨‍💻 Developer

**Praneeth Kumar**

GitHub: [@praneethkumar804](https://github.com/praneethkumar804)

---

⭐ If you find this project useful, consider giving it a star!