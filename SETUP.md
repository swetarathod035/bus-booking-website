# AnandBus — Setup & Run Guide

## Prerequisites
- Python 3.10+
- PostgreSQL 14+ (pgAdmin 4 recommended)
- Git

## 1. Clone & Activate Virtual Environment

```powershell
cd d:\anandbus
.\venv\Scripts\activate
```

## 2. Configure Environment Variables

Edit `.env` file with your actual credentials:

```
DB_NAME=anandbus_db
DB_USER=postgres
DB_PASSWORD=your_postgres_password
DB_HOST=localhost
DB_PORT=5432

EMAIL_HOST_USER=your_gmail@gmail.com
EMAIL_HOST_PASSWORD=your_gmail_app_password

RAZORPAY_KEY_ID=rzp_test_XXXXXXXXXXXXXXXX
RAZORPAY_KEY_SECRET=XXXXXXXXXXXXXXXXXXXXXXXX
```

## 3. Create PostgreSQL Database

Open pgAdmin 4 (or psql) and run:

```sql
CREATE DATABASE anandbus_db;
```

## 4. Run Migrations

```powershell
.\venv\Scripts\python manage.py migrate
```

## 5. Seed Sample Data

```powershell
.\venv\Scripts\python manage.py seed_data
```

This creates:
- 20 Anand bus stops with GPS coordinates
- 5 routes with intermediate stops
- 3 buses + 2 drivers
- 77 schedules (11 daily templates × 7 days)
- 3 demo users

## 6. Collect Static Files

```powershell
.\venv\Scripts\python manage.py collectstatic --noinput
```

## 7. Start Development Server

```powershell
.\venv\Scripts\python manage.py runserver
```

Open: **http://127.0.0.1:8000**

---

## Demo Login Credentials

| Role        | Username     | Password       | URL                                    |
|-------------|--------------|----------------|----------------------------------------|
| Super Admin | admin        | Admin@123      | http://127.0.0.1:8000/buses/admin/     |
| Conductor   | conductor1   | Conductor@123  | http://127.0.0.1:8000/conductor/       |
| Passenger   | passenger1   | Passenger@123  | http://127.0.0.1:8000/bookings/dashboard/ |
| Django Admin| admin        | Admin@123      | http://127.0.0.1:8000/django-admin/    |

---

## Key URLs

```
/                           → Home Page (search, carousel, stops)
/search/                    → Bus Search Results
/accounts/login/            → Login
/accounts/register/         → Passenger Registration
/bookings/dashboard/        → Passenger Dashboard
/bookings/seats/<id>/       → Seat Selection
/bookings/pay/<uuid>/       → Payment Page
/buses/admin/               → SuperAdmin Dashboard (Chart.js analytics)
/buses/admin/buses/         → Fleet Management
/buses/admin/routes/        → Route Management
/buses/admin/schedules/     → Schedule Management
/buses/admin/users/         → User Management
/buses/admin/revenue/       → Revenue Reports
/buses/admin/export/bookings/ → Export to Excel
/conductor/                 → Conductor Portal
/conductor/trip/<id>/       → Trip Detail & Seat Control
/conductor/verify/          → QR Ticket Verification
/tracking/live/<id>/        → Live Bus Tracking (Leaflet.js)
/django-admin/              → Built-in Django Admin
```

---

## Architecture

```
anandbus/
├── accounts/          # CustomUser model, RBAC decorators, auth views
├── buses/             # Bus/Driver models, SuperAdmin dashboard, analytics
├── routes/            # Route/Stop/Schedule models, search, home page
├── bookings/          # Seat selection, booking engine, PDF tickets, payment
├── conductor/         # Conductor portal, trip status, offline tickets
├── tracking/          # Leaflet.js live tracking, simulated GPS
├── templates/         # All HTML templates (Bootstrap 5, FontAwesome 6)
├── static/            # CSS (main.css), JS (main.js)
├── media/             # Uploaded files (tickets, QR codes, avatars)
└── anandbus/          # Django settings, URLs, context processors
```

## Razorpay Test Mode

Use test cards from https://razorpay.com/docs/payments/payments/test-card-upi-details/

Example test card: `4111 1111 1111 1111` · CVV: `123` · Expiry: any future date

## Gmail SMTP Setup

1. Enable 2-Factor Authentication on your Gmail account
2. Go to Google Account → Security → App Passwords
3. Generate an app password for "Mail"
4. Use that 16-character password in `EMAIL_HOST_PASSWORD`

## wkhtmltopdf (Optional Alternative PDF)

If you prefer wkhtmltopdf over ReportLab:
```powershell
pip install pdfkit
# Download wkhtmltopdf from https://wkhtmltopdf.org/downloads.html
```
ReportLab is already configured and works out of the box.
