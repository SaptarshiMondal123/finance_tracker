# 💰 Finance Tracker API

A clean, role-based financial records management backend built with **FastAPI**, **SQLAlchemy**, and **SQLite**.

---

## 🚀 Tech Stack

| Layer        | Technology                          |
|--------------|--------------------------------------|
| Framework    | FastAPI                              |
| Database     | SQLite via SQLAlchemy ORM            |
| Auth         | JWT (via `python-jose` + `passlib`)  |
| Validation   | Pydantic v2                          |
| Testing      | Pytest + HTTPX TestClient            |
| Docs         | Auto-generated Swagger UI at `/docs` |

---

## 🌍 Live API Documentation

[https://finance-tracker-olzz.onrender.com/docs]

---

## 📁 Project Structure

```
finance_tracker/
├── main.py                    # App entry point, router registration
├── database.py                # SQLAlchemy engine, session, base
├── models.py                  # ORM models: User, Transaction
├── schemas.py                 # Pydantic request/response schemas
├── auth.py                    # JWT creation, password hashing
├── dependencies.py            # Auth middleware, role-based guards
├── routers/
│   ├── auth.py                # /auth/register, /auth/login
│   ├── transactions.py        # Full CRUD + filtering + export
│   ├── summary.py             # /summary — analytics endpoint
│   └── users.py               # /users — admin user management
├── services/
│   ├── transaction_service.py # Business logic for transactions
│   └── summary_service.py     # Analytics and aggregation logic
├── tests/
│   └── test_transactions.py   # Full test suite (25+ test cases)
└── requirements.txt
```

---

## ⚙️ Setup & Run

### 1. Clone and install dependencies

```bash
git clone https://github.com/SaptarshiMondal123/finance_tracker.git
cd finance_tracker
pip install -r requirements.txt
```

### 2. Start the server

```bash
uvicorn main:app --reload
```

### 3. Open API docs

Visit **http://localhost:8000/docs** — the interactive Swagger UI.

---

## 🔑 Authentication Flow

1. **Register** a user:
   ```
   POST /auth/register
   { "username": "alice", "email": "alice@example.com", "password": "secret123", "role": "admin" }
   ```

2. **Login** to get a token:
   ```
   POST /auth/login
   form-data: username=alice, password=secret123
   ```

3. **Authorize** in Swagger UI: click **Authorize** → paste `Bearer <token>`

---

## 👥 Role-Based Access Control

| Endpoint                    | viewer | analyst | admin |
|-----------------------------|--------|---------|-------|
| View own transactions       | ✅     | ✅      | ✅    |
| Filter transactions         | ✅     | ✅      | ✅    |
| View financial summary      | ❌     | ✅      | ✅    |
| Export CSV / JSON           | ❌     | ✅      | ✅    |
| Create transactions         | ❌     | ❌      | ✅    |
| Update / Delete             | ❌     | ❌      | ✅    |
| Manage users                | ❌     | ❌      | ✅    |

---

## 📡 API Endpoints

### Auth
| Method | Path             | Description              |
|--------|------------------|--------------------------|
| POST   | /auth/register   | Register a new user      |
| POST   | /auth/login      | Login and receive JWT    |

### Transactions
| Method | Path                        | Description                         |
|--------|-----------------------------|-------------------------------------|
| POST   | /transactions/              | Create transaction (admin)          |
| GET    | /transactions/              | List with filters + pagination      |
| GET    | /transactions/{id}          | Get single transaction              |
| PATCH  | /transactions/{id}          | Update transaction (admin)          |
| DELETE | /transactions/{id}          | Delete transaction (admin)          |
| GET    | /transactions/export/csv    | Export as CSV (analyst+)            |
| GET    | /transactions/export/json   | Export as JSON (analyst+)           |

### Summary
| Method | Path      | Description                               |
|--------|-----------|-------------------------------------------|
| GET    | /summary/ | Full financial analytics (analyst+)       |

### Users
| Method | Path          | Description                  |
|--------|---------------|------------------------------|
| GET    | /users/       | List all users (admin)       |
| DELETE | /users/{id}   | Delete a user (admin)        |

---

## 🔍 Filtering & Pagination

`GET /transactions/` supports the following query parameters:

| Parameter    | Type   | Example               |
|--------------|--------|-----------------------|
| `tx_type`    | string | `income` or `expense` |
| `category`   | string | `Salary` (partial)    |
| `start_date` | date   | `2026-04-01`          |
| `end_date`   | date   | `2026-12-31`          |
| `skip`       | int    | `0`                   |
| `limit`      | int    | `20` (max 100)        |

---

## 📊 Summary Response

`GET /summary/` returns:

```json
{
  "total_income": 50000.0,
  "total_expenses": 18500.0,
  "current_balance": 31500.0,
  "category_breakdown": [
    { "category": "Salary", "total": 50000.0 },
    { "category": "Rent", "total": 12000.0 }
  ],
  "monthly_summaries": [
    { "year": 2024, "month": 3, "income": 20000.0, "expenses": 7000.0, "balance": 13000.0 }
  ],
  "recent_transactions": [ ... ]
}
```

---

## 🧪 Running Tests

```bash
pytest tests/ -v
```

Tests cover:
- User registration and login
- Duplicate user rejection
- Password validation
- Role-based access (403 checks)
- Full CRUD on transactions
- Filter and pagination
- Summary access control
- CSV and JSON export

---

## 🔐 Security Considerations

- **Authentication:** JWT tokens expire in 60 minutes (configurable; refresh strategies can be added in production).
- **Password Safety:** Passwords are securely hashed using bcrypt.
- **Authorization:** Role-based access is strictly enforced via FastAPI dependency injection at the route level.

---

## 🚀 Future Improvements (Product Roadmap)

While this project is fully functional for its current scope, the following features are planned for a production-scale release:

- **Strict Role Escalation:** Restrict role assignment during registration and implement admin-only approval workflows.
- **Rate Limiting:** Add request throttling to prevent brute-force attacks on auth endpoints.
- **Audit Trails:** Transition from hard deletes to soft deletes to maintain strict financial audit logs.
- **Database Scaling:** Migrate from SQLite to PostgreSQL to handle high-concurrency writes.
- **Advanced Auth:** Add refresh tokens and centralized session management.

---

## 📝 Assumptions Made

1. **Data Ownership:** Transactions are strictly owned by users. A `viewer` or `analyst` can only access their own records, while an `admin` has global access.
2. **Database Scope:** SQLite was chosen for ease of evaluation and local testing. The ORM structure allows for an instant swap to PostgreSQL by simply updating the `DATABASE_URL` in `database.py`.

---

## 🌱 Sample Seed Data (Quick Test)

```bash
# 1. Register admin
curl -X POST http://localhost:8000/auth/register \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","email":"admin@test.com","password":"admin123","role":"admin"}'

# 2. Login
curl -X POST http://localhost:8000/auth/login \
  -F "username=admin" -F "password=admin123"

# 3. Add a transaction (use token from step 2)
curl -X POST http://localhost:8000/transactions/ \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{"amount":50000,"type":"income","category":"Salary","date":"2024-03-01"}'
```
