# School Equipment Lending Portal

This repository contains a full-stack web application for managing school equipment loans.

- **Backend**: Flask (Python) with SQLite
- **Frontend**: React (React Router v6), using a dev server proxy to the Flask API
- **Roles**: student, staff, admin
- **Admin credentials (seeded)**:
  - Email: [REDACTED_EMAIL_ADDRESS_1]
  - Password: admin

## Quick Start

### 1) Backend
```bash
cd backend
python -m venv venv
# Windows: venv\Scripts\activate
# macOS/Linux:
source venv/bin/activate
pip install -r requirements.txt
python app.py
```
This starts Flask at http://127.0.0.1:5000 and creates the SQLite DB if not present.

### 2) Frontend
```bash
cd frontend
npm install
npm start
```
This starts React at http://localhost:3000 and proxies API calls to http://127.0.0.1:5000.

> If the proxy doesn’t work in your environment, update `frontend/package.json` → `"proxy"` to your backend URL.

## Demo Video (Silent Walkthrough)
A silent walkthrough script is provided in `DemoScripts/DEMO_STEPS.md`. Record the screen following those steps and upload the video to Google Drive as per your submission instructions.


## Phase 1 (Manual) Notes
- Passwords are stored in plaintext for simplicity (as a baseline implementation).
- All core features implemented:
  - Authentication (token-based simulation)
  - Equipment CRUD (admin)
  - Borrowing workflow (request, approve/reject, return)
  - Request history & basic analytics

See `API_DOCUMENTATION.md`, `architecture_diagram.png`, and `db_schema_diagram.png` for details.


## Docker Quickstart

```bash
docker compose up --build
# Frontend: http://localhost:3000
# Backend API: http://localhost:5000
```

To stop containers:

```bash
docker compose down
```
