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

- JWT tokens expire in 60 minutes (configurable for production)
- Passwords are hashed using bcrypt
- Role-based access enforced via dependency injection

---

## ⚠️ Known Limitations & Edge Cases

- Role assignment is open during registration (should be restricted in production)
- No rate limiting → potential vulnerability to brute-force attacks
- Hard deletes instead of soft deletes
- SQLite may not scale under high concurrency

---

## 📝 Assumptions Made

1. **Transactions are owned by users** — a viewer can only see their own; admins see all.
2. **Role is set at registration** — in production this would be admin-assigned only.
3. **JWT expiry is 60 minutes** — configurable in `auth.py`.
4. **SQLite is sufficient** for this scope; swapping to PostgreSQL requires only changing `DATABASE_URL` in `database.py`.
5. **Soft delete not implemented** — deletions are hard deletes for simplicity.

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
