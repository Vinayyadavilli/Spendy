# Spend Tracker FastAPI Backend (MySQL)

This is the backend for the Spend Tracker and SMS Money Extractor application.

## 🚀 Quick Start

### 1. Install Dependencies
```bash
cd backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 2. Configure MySQL Database
Edit `.env` or use default MySQL local credentials:
```env
DB_HOST=localhost
DB_PORT=3306
DB_USER=root
DB_PASSWORD=root
DB_NAME=spent_tracker_db
DATABASE_URL=mysql+pymysql://root:root@localhost:3306/spent_tracker_db
```

### 3. Run FastAPI Server
```bash
python3 run.py
```
Or with uvicorn:
```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

## 📚 API Endpoints & Swagger Docs
Open your browser at:
- **Swagger UI**: [http://localhost:8000/docs](http://localhost:8000/docs)
- **ReDoc**: [http://localhost:8000/redoc](http://localhost:8000/redoc)

### Key Endpoints:
- `POST /api/auth/register` - User registration with email, full name, password
- `POST /api/auth/login` - User login returning JWT Bearer token
- `GET /api/auth/me` - Current user profile
- `GET /api/bank-accounts/` - List user's bank accounts & current balances
- `POST /api/bank-accounts/` - Add bank account with name and starting balance
- `PUT /api/bank-accounts/{id}` - Update bank account details
- `DELETE /api/bank-accounts/{id}` - Delete bank account
- `GET /api/transactions/` - List transactions (filter by debit/credit or bank account)
- `POST /api/transactions/` - Add transaction (auto-adjusts bank account balance)
- `GET /api/transactions/analytics` - Computes individual debit and credit breakdowns
- `POST /api/sms/parse` - Extracts money spent/credited details from raw SMS
