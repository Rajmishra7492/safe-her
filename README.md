# SafeHer - Complete AI-based Women Safety Web Application

Complete full-stack college major project using Flask, MongoDB, OpenCV, and multi-page responsive frontend.

## Tech Stack
- Frontend: HTML, CSS, JavaScript
- Backend: Python Flask (REST APIs)
- Database: MongoDB
- AI Module: OpenCV + rule-based risk scoring

## Folder Structure

frontend/
- index.html (Landing page)
- login.html
- register.html
- dashboard.html
- sos.html
- contacts.html
- report.html
- alerts.html
- admin.html
- css/style.css
- js/common.js

backend/
- app.py
- config.py
- requirements.txt
- .env.example
- models/db.py
- routes/auth_routes.py
- routes/main_routes.py
- utils/auth.py
- utils/risk_detection.py

## Required Pages Implemented
1. Landing Page (Home)
2. Login Page
3. Register Page
4. User Dashboard
5. SOS Page
6. Emergency Contacts Page (Add/Delete)
7. Incident Reporting + AI Detection Page
8. Alerts History Page
9. Admin Panel

## REST APIs
- `POST /register`
- `POST /login`
- `GET /dashboard`
- `POST /sos`
- `GET /contacts`
- `POST /contacts`
- `DELETE /contacts/<contact_id>`
- `POST /report`
- `GET /alerts`
- `GET /admin`

Compatibility aliases also available:
- `/add-contact`, `/report-incident`, `/get-alerts`, `/admin/analytics`

## Security
- bcrypt password hashing
- JWT authentication middleware on protected APIs
- basic input validation

## MongoDB Collections
- `users`
- `contacts`
- `alerts`
- `incidents`

## AI Detection Logic
When user uploads an image in incident report:
- detects faces using OpenCV Haar Cascade
- calculates brightness using grayscale intensity
- adds risk for low light + face count + night time
- generates risk score
- auto creates alert if risk is above threshold

## Step-by-step Run Instructions

### 1) Install prerequisites
- Python 3.9+
- MongoDB Community Server

### 2) Start MongoDB
Ensure MongoDB runs at `mongodb://localhost:27017`.

### 3) Backend setup
```bash
cd backend
python -m venv venv
source venv/Scripts/activate
pip install -r requirements.txt
cp .env.example .env
python app.py
```
Backend URL: `http://127.0.0.1:5000`

### 4) Frontend setup
```bash
cd frontend
python -m http.server 5500
```
Frontend URL: `http://127.0.0.1:5500`

### 5) Use the application
1. Open landing page and register/login.
2. Dashboard gives navigation to all features.
3. SOS page sends live-location emergency alert.
4. Contacts page adds/deletes emergency contacts.
5. Report page submits incident with image and AI risk.
6. Alerts page shows alert history.
7. Admin page shows users, alerts, incidents (admin users only).

## Admin Access
Set a user as admin directly in MongoDB:
```js
db.users.updateOne({ email: "your_email@example.com" }, { $set: { is_admin: true } })
```
