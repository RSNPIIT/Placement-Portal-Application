# 🎓 Placement Portal Application (V2)

A full-stack web application designed to streamline the campus placement process.  
This platform connects **Students**, **Companies**, and **Administrators** with features like job management, application tracking, asynchronous processing, caching, and report generation.

---

## 🚀 Core Features

### 👨‍🎓 Student
- Secure JWT-based login
- Role-protected dashboard
- Browse and apply for jobs
- Track application status
- Export application data (CSV)
- Download placement reports (PDF)

### 🏢 Company
- Company registration (admin approval required)
- Post and manage job listings
- View applicants
- Generate placement reports (PDF)
- Download reports from dashboard

### 🛠️ Admin
- Approve company registrations
- Monitor system activity
- Manage users and roles

---

## ⚡ Advanced Features

### 📬 Email Reminder System
- Automated interview reminders
- Implemented using **Celery + Celery Beat**
- Emails sent via **Flask-Mail (SMTP Gmail)**

### 📊 Report Generation (PDF)
- Placement analytics report
- Includes:
  - Total applications
  - Shortlisted candidates
  - Selected/rejected counts
- Generated using **ReportLab**
- Downloadable from dashboards

### 📁 CSV Export
- Students can export application history
- Generated asynchronously using Celery

### ⚡ Redis Caching
- Optimizes API performance
- Cached endpoints:
  - Job listings
  - Student data
  - Company data
- Cache expiry implemented
- Cache invalidation on updates

### 🔄 Asynchronous Processing
Handled using **Celery + Redis**:
- Email reminders
- CSV export
- Report generation

---

## 🔐 Authentication & Authorization
- Password hashing using `werkzeug.security`
- JWT authentication (`flask-jwt-extended`)
- Role-based access:
  - `student`
  - `company`
  - `admin`

---

## 🧰 Tech Stack

### Backend
- Python 3
- Flask
- Flask-SQLAlchemy
- Flask-JWT-Extended
- Flask-CORS
- Flask-Mail
- Flask-Caching
- Celery
- Redis
- ReportLab
- SQLite

### Frontend
- Vue 3
- Vite
- Axios

---

## 🏗️ Project Structure

Placement_Portal_Application_V2/
├── backend/
│   ├── app.py
│   ├── celery_worker.py
│   ├── reports/         (ignored)
│   ├── exports/         (ignored)
│   └── instance/
├── frontend/
│   ├── src/
│   ├── package.json
│   └── vite.config.js
├── requirements.txt
├── README.md
└── .gitignore


---

## ⚙️ Backend Setup

### 1️⃣ Create Virtual Environment
```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 2️⃣ Run Flask Server
```bash
cd backend
python3 app.py
```

### 3️⃣ Start Redis
```bash
redis-server
```

### 4️⃣ Start Celery Worker
```bash
celery -A celery_worker worker --loglevel=info --pool=solo
```

### 5️⃣ Start Celery Beat
```bash
celery -A celery_worker beat --loglevel=info
```

---

## ⚙️ Frontend Setup
```bash
cd frontend
npm install
npm run dev
```

---

## 📊 Key Functionalities Demonstration

- **Login as Company**
  - Generate and download placement report

- **Login as Student**
  - Apply for jobs
  - Export CSV
  - Download report

- **System automatically:**
  - Sends interview reminders
  - Caches frequently used APIs
  - Generates reports

---

## 🚀 Conclusion

This project demonstrates:
- Full-stack development
- Asynchronous task handling
- API optimization using caching
- Real-world system design
