# SmartRide – Full-Stack Bus Pass Automation

A working starter application for the DTIE Smart Bus Pass project.

## Stack
- React + Vite frontend
- FastAPI backend
- SQL Server via SQLAlchemy + pyodbc
- JWT authentication
- QR generation (`qrcode`)
- Browser QR scanning (`html5-qrcode`)

## Features included
- Passenger registration and login
- Unique passenger ID and individual QR token
- QR code displayed as a downloadable image
- Conductor QR scanning and passenger verification
- Boarding/exit stop selection and fare calculation
- Database-backed wallet recharge (demo payment; no real payment gateway)
- Database-backed journey and transaction history
- Admin overview

## 1. Prerequisites
- Python 3.10+
- Node.js 18+
- SQL Server (local or hosted)
- Microsoft ODBC Driver 17 or 18 for SQL Server

Create a database in SQL Server:
```sql
CREATE DATABASE SmartRideDB;
```

## 2. Backend setup
```bash
cd backend
python -m venv venv
```
Windows:
```bash
venv\Scripts\activate
```
Install:
```bash
pip install -r requirements.txt
```
Copy `.env.example` to `.env` and update the SQL Server connection string and secret key.

Example Windows SQL Server Express connection:
```env
DATABASE_URL=mssql+pyodbc://@localhost\\SQLEXPRESS/SmartRideDB?driver=ODBC+Driver+18+for+SQL+Server&trusted_connection=yes&TrustServerCertificate=yes
```
For SQL authentication:
```env
DATABASE_URL=mssql+pyodbc://USERNAME:PASSWORD@localhost:1433/SmartRideDB?driver=ODBC+Driver+18+for+SQL+Server&TrustServerCertificate=yes
```
Use URL-encoded special characters in usernames/passwords.

Create demo conductor and admin:
```bash
python seed_users.py
```
Default demo accounts:
- Admin: `admin@smartride.local` / `Admin@12345`
- Conductor: `conductor@smartride.local` / `Conductor@12345`

Run:
```bash
uvicorn app.main:app --reload
```
API docs: http://127.0.0.1:8000/docs

## 3. Frontend setup
In a second terminal:
```bash
cd frontend
npm install
npm run dev
```
Open the URL printed by Vite (normally http://localhost:5173).

## 4. Demo flow
1. Register two or more passenger accounts.
2. Log in as each passenger and show their individual QR code and balance.
3. Log out and sign in as the conductor.
4. Open QR Scanner and allow camera access. Scan a passenger's QR displayed on another device or browser tab.
5. Select boarding and exit stops and complete the journey.
6. Log in as the passenger again to see the deducted balance and journey history.
7. Log in as admin to view users and transactions.

Camera access requires HTTPS or `localhost`. For a two-device demo, deploy frontend on HTTPS or use a local HTTPS tunnel.

## 5. Important prototype boundaries
- Recharge is a simulated payment that writes a recharge transaction to SQL Server. It does not charge a bank account or UPI account.
- Fare is calculated using the configured stop sequence and per-stop fare in `backend/app/config.py`. Replace this with the transport authority's official route/fare rules before real deployment.
- QR tokens are random, stored in the database as SHA-256 hashes, and can be regenerated. The QR payload is an opaque token, not passenger personal data.
- This is a project prototype, not a production transit payment system. Before deployment add HTTPS, rate limiting, audit logging, backup/recovery, payment gateway integration, device management and stronger operational controls.

## 6. SQL Server note
The application creates its tables on startup using SQLAlchemy. If your SQL Server uses a named instance or a different ODBC driver, update `DATABASE_URL` in `.env`.
