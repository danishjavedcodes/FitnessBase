# FitnessBase — Gym Management System

**Local freelance project for a GYM, built according to requirements provided by the gym owner.**

FitnessBase is a full-featured **gym management web application** for fitness centers, health clubs, and local gyms. It streamlines **member registration**, **attendance tracking**, **membership packages**, **payment processing**, **inventory**, **point-of-sale (POS) sales**, and **staff management** — all from a single Flask-based dashboard backed by **Google Sheets**.

[![Python](https://img.shields.io/badge/Python-3.12+-3776AB?logo=python&logoColor=white)](https://www.python.org/)
[![Flask](https://img.shields.io/badge/Flask-2.3-000000?logo=flask&logoColor=white)](https://flask.palletsprojects.com/)
[![License](https://img.shields.io/badge/License-Private-red)](#)

---

## Table of Contents

- [About This Project](#about-this-project)
- [Key Features](#key-features)
- [Tech Stack](#tech-stack)
- [User Roles](#user-roles)
- [Project Structure](#project-structure)
- [Getting Started](#getting-started)
- [Google Sheets Setup](#google-sheets-setup)
- [Deployment](#deployment)
- [Screens & Modules](#screens--modules)
- [Author](#author)

---

## About This Project

FitnessBase was developed as a **custom freelance solution** for a local gym. Every module — from member onboarding to sales receipts — was shaped by the **gym owner's operational requirements**, not a generic off-the-shelf template.

The system is designed for **small to mid-size fitness businesses** that need affordable, cloud-friendly gym software without a heavy enterprise price tag. Data lives in **Google Sheets**, making it easy for non-technical staff to audit records while the web app handles day-to-day workflows.

---

## Key Features

### Member Management
- Add, edit, and remove gym members
- Track join dates, contact details, and active membership status
- Search and filter member records from the admin dashboard

### Attendance Tracking
- Check-in / check-out for gym members
- Separate staff attendance module for receptionists and trainers
- Date-based attendance history for reporting

### Membership Packages
- Create and manage gym membership plans (duration, price, description)
- Edit or retire packages as offerings change
- Link packages to member payments

### Payments & Receipts
- Record membership payments and mark dues as paid
- Generate printable and downloadable **PDF payment receipts**
- Monthly revenue tracking on the admin dashboard

### Inventory & Sales (POS)
- Manage gym inventory (supplements, merchandise, accessories)
- Process point-of-sale transactions with multiple payment methods
- Support for custom products outside standard inventory
- Sales receipts with print and download options

### Reports & Analytics
- Admin dashboard with revenue charts (last 6 months)
- Member growth trends over time
- Export reports to **Excel** and **PDF**
- Combined revenue from memberships and retail sales

### Staff & Receptionist Management
- Role-based access: **Admin** vs **Staff / Receptionist**
- Add, edit, and remove receptionist accounts
- Password change flow for all users
- Privilege-based navigation per role

---

## Tech Stack

| Layer | Technology |
|-------|------------|
| Backend | [Flask](https://flask.palletsprojects.com/) 2.3 |
| Language | Python 3.12+ |
| Database | [Google Sheets](https://developers.google.com/sheets/api) via `gspread` |
| Data Processing | pandas, numpy |
| Reports | ReportLab (PDF), xlsxwriter / openpyxl (Excel) |
| Frontend | Jinja2 templates, Bootstrap, JavaScript |
| Server | Gunicorn |
| Timezone | Asia/Karachi (configurable) |

---

## User Roles

| Role | Access |
|------|--------|
| **Admin** | Full dashboard, members, packages, payments, inventory, sales, reports, staff management |
| **Staff / Receptionist** | Member operations, attendance, payments, sales — scoped to daily front-desk tasks |

---

## Project Structure

```
FitnessBase/
├── app.py              # Main Flask application & routes
├── routes.py           # Additional route handlers
├── config.py           # App configuration (DB, sessions, security)
├── requirements.txt    # Python dependencies
├── nixpacks.toml       # Deployment config (Gunicorn)
├── templates/          # Jinja2 HTML templates
│   ├── admin/          # Admin dashboard & staff management
│   ├── staff/          # Staff / receptionist views
│   └── ...             # Members, sales, payments, reports, etc.
├── static/             # CSS, JavaScript, assets
└── public/             # Font assets
```

---

## Getting Started

### Prerequisites

- Python **3.12** or higher
- A Google Cloud **service account** with access to your gym spreadsheet
- `pip` or a virtual environment tool

### Installation

1. **Clone the repository**

   ```bash
   git clone https://github.com/danishjavedcodes/FitnessBase.git
   cd FitnessBase
   ```

2. **Create and activate a virtual environment**

   ```bash
   python -m venv venv
   source venv/bin/activate        # macOS / Linux
   # venv\Scripts\activate         # Windows
   ```

3. **Install dependencies**

   ```bash
   pip install -r requirements.txt
   ```

4. **Configure Google Sheets credentials**

   Place your service account JSON at the project root (see [Google Sheets Setup](#google-sheets-setup)) or configure credentials in `app.py` as required for your environment.

5. **Run the development server**

   ```bash
   python app.py
   ```

   Open `http://127.0.0.1:5000` and log in with admin or staff credentials defined in your Google Sheet.

---

## Google Sheets Setup

FitnessBase uses Google Sheets as its data store. Your spreadsheet should include worksheets for:

| Sheet Name | Purpose |
|------------|---------|
| `admin` | Admin login credentials |
| `receptionists` | Staff / receptionist accounts |
| `members` | Gym member records |
| `packages` | Membership plans |
| `payments` | Payment history |
| `attendance` | Member check-in / check-out |
| `sales` | Retail & POS transactions |
| `inventory` | Stock items |

**Steps:**

1. Create a Google Cloud project and enable the **Google Sheets API**.
2. Create a **service account** and download the JSON key file.
3. Share your spreadsheet with the service account email (Editor access).
4. Point the app to your spreadsheet URL in `setup_google_sheets()` inside `app.py`.

> **Note:** Never commit `service-account.json` or `.env` files to version control. They are listed in `.gitignore`.

---

## Deployment

The project includes a `nixpacks.toml` for container-based deployment (e.g. Railway):

```toml
[start]
cmd = "gunicorn app:app"
```

For production:

```bash
gunicorn app:app --bind 0.0.0.0:8000
```

Set environment variables such as `SECRET_KEY` and `DATABASE_URL` as needed via your hosting platform.

---

## Screens & Modules

| Module | Route | Description |
|--------|-------|-------------|
| Login | `/login` | Secure role-based authentication |
| Admin Dashboard | `/admin/dashboard` | Stats, revenue charts, member growth |
| Staff Dashboard | `/staff/dashboard` | Receptionist home view |
| Members | `/view_members` | Browse and manage members |
| Add Member | `/members/add` | Register new gym members |
| Attendance | `/attendance` | Member check-in / check-out |
| Staff Attendance | `/staff/attendance` | Employee attendance |
| Packages | `/packages` | Membership plan CRUD |
| Payments | `/payments` | Record and track payments |
| Inventory | `/inventory` | Stock management |
| Sales | `/sales` | Point-of-sale transactions |
| Reports | `/reports` | Analytics and exportable reports |
| Receptionists | `/admin/receptionists` | Staff account management |

---

## Keywords

Gym management system · fitness center software · membership tracking · gym attendance app · Flask gym app · Google Sheets gym database · gym POS · fitness club admin panel · member payment receipts · gym inventory management · freelance gym software · local gym ERP

---

## Author

**Danish Javed** — [GitHub](https://github.com/danishjavedcodes)

Built as a local freelance project for a gym, tailored to the owner's day-to-day operational requirements.

---

## License

This is a private freelance project. All rights reserved unless otherwise agreed with the client.
