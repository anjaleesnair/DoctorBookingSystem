# 🏥 Doctor Booking System

A Django + DRF backend with role-based access, dynamic slot generation, and concurrency-safe booking.

---

## 🚀 Setup Instructions

### 1. Create & Activate Virtual Environment
```bash
python3 -m venv venv
source venv/bin/activate
```

### 2. Install Dependencies
```bash
pip install -r requirements.txt
```

### 3. Run Migrations
```bash
python manage.py migrate
```

### 4. Create Superadmin User
```bash
python manage.py shell -c "
from accounts.models import User
User.objects.create_superuser(username='admin', password='admin123', role='superadmin')
"
```

### 5. Run Server
```bash
python manage.py runserver
```

---

## 🗂️ Project Structure

```
Doctor_booking_system/
├── accounts/               # Custom User model + Auth
│   ├── models.py
│   ├── serializers.py
│   ├── views.py
│   ├── urls.py
│   └── permissions.py
├── booking/                # Core booking logic
│   ├── models.py
│   ├── serializers.py
│   ├── views.py
│   ├── urls.py
│   └── utils.py            # Dynamic slot generation
├── superadmin_dashboard/   # Template-based dashboard
│   ├── views.py
│   └── urls.py
├── templates/superadmin/   # HTML templates
├── doctor_booking/         # Project config
│   ├── settings.py
│   └── urls.py
├── manage.py
└── requirements.txt
```

---

## 🌐 API Endpoints

### Auth
| Method | URL | Description |
|--------|-----|-------------|
| POST | `/api/auth/register/` | Register user |
| POST | `/api/auth/login/` | Login → get JWT tokens |
| POST | `/api/auth/token/refresh/` | Refresh access token |

### Superadmin (JWT required, role=superadmin)
| Method | URL | Description |
|--------|-----|-------------|
| GET/POST | `/api/admin/doctors/` | List / Create doctors |
| GET/PUT/DELETE | `/api/admin/doctors/<id>/` | Doctor detail |
| GET | `/api/admin/doctors/<id>/slots/?date=YYYY-MM-DD` | View doctor slots |
| GET | `/api/admin/leaves/` | All leave requests |
| POST | `/api/admin/leaves/<id>/action/` | Approve / Reject leave |

### Doctor (JWT required, role=doctor)
| Method | URL | Description |
|--------|-----|-------------|
| GET/POST | `/api/doctor/leaves/` | View / Create leave request |
| GET | `/api/doctor/appointments/` | View own appointments |

### Customer (JWT required, role=customer)
| Method | URL | Description |
|--------|-----|-------------|
| GET | `/api/doctors/` | List all active doctors |
| GET | `/api/doctors/<id>/slots/?date=YYYY-MM-DD` | View available slots |
| POST | `/api/appointments/book/` | Book an appointment |
| GET | `/api/appointments/` | View my appointments |

### Superadmin Dashboard (Template)
| URL | Description |
|-----|-------------|
| `/superadmin/login/` | Login page |
| `/superadmin/dashboard/` | Dashboard overview |
| `/superadmin/doctors/` | Manage doctors |
| `/superadmin/leaves/` | Approve/Reject leaves |

---

## 🔐 Authentication

All API endpoints require JWT Bearer token:
```
Authorization: Bearer <access_token>
```

---

## 📌 Book Appointment — Request Body
```json
{
  "doctor_id": 1,
  "date": "2025-01-15",
  "start_time": "09:00"
}
```

## 📌 Leave Request — Request Body
```json
{
  "date": "2025-01-20",
  "reason": "Personal emergency"
}
```

## 📌 Leave Approve/Reject — Request Body
```json
{
  "action": "reject",
  "rejection_reason": "Too many leaves this month"
}
```

---

## ⚙️ Key Design Decisions

- **Slots are NOT stored in DB** — generated dynamically per request
- **Race conditions** prevented using `select_for_update()` inside `transaction.atomic()`
- **Approved leaves** automatically block all slots for that date
- **Class-Based Views** used throughout (API + Templates)
- **No Django Admin** — custom superadmin dashboard with templates
