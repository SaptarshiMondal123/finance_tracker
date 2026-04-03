import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from database import Base, get_db
from main import app

# ── Test database setup (in-memory SQLite) ────────────────────────────────────
TEST_DATABASE_URL = "sqlite:///./test_finance.db"
engine = create_engine(TEST_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db
Base.metadata.create_all(bind=engine)

client = TestClient(app)


# ── Helpers ───────────────────────────────────────────────────────────────────
def register_and_login(username: str, role: str = "admin") -> str:
    client.post("/auth/register", json={
        "username": username,
        "email": f"{username}@test.com",
        "password": "testpass123",
        "role": role
    })
    response = client.post("/auth/login", data={
        "username": username,
        "password": "testpass123"
    })
    return response.json()["access_token"]


def auth_headers(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


# ── Auth Tests ────────────────────────────────────────────────────────────────
class TestAuth:
    def test_register_success(self):
        r = client.post("/auth/register", json={
            "username": "newuser1",
            "email": "newuser1@test.com",
            "password": "securepass",
            "role": "viewer"
        })
        assert r.status_code == 201
        assert r.json()["username"] == "newuser1"
        assert r.json()["role"] == "viewer"

    def test_register_duplicate_username(self):
        client.post("/auth/register", json={
            "username": "dupuser",
            "email": "dup1@test.com",
            "password": "pass123"
        })
        r = client.post("/auth/register", json={
            "username": "dupuser",
            "email": "dup2@test.com",
            "password": "pass123"
        })
        assert r.status_code == 400

    def test_login_success(self):
        client.post("/auth/register", json={
            "username": "logintest",
            "email": "logintest@test.com",
            "password": "pass1234"
        })
        r = client.post("/auth/login", data={
            "username": "logintest",
            "password": "pass1234"
        })
        assert r.status_code == 200
        assert "access_token" in r.json()

    def test_login_wrong_password(self):
        client.post("/auth/register", json={
            "username": "wrongpass",
            "email": "wrongpass@test.com",
            "password": "correct123"
        })
        r = client.post("/auth/login", data={
            "username": "wrongpass",
            "password": "wrongpassword"
        })
        assert r.status_code == 401

    def test_short_password_rejected(self):
        r = client.post("/auth/register", json={
            "username": "shortpw",
            "email": "shortpw@test.com",
            "password": "abc"
        })
        assert r.status_code == 422


# ── Transaction Tests ─────────────────────────────────────────────────────────
class TestTransactions:
    def setup_method(self):
        self.admin_token = register_and_login("txadmin", "admin")
        self.viewer_token = register_and_login("txviewer", "viewer")

    def test_create_transaction_as_admin(self):
        r = client.post("/transactions/", json={
            "amount": 5000.0,
            "type": "income",
            "category": "Salary",
            "date": "2024-03-01",
            "notes": "March salary"
        }, headers=auth_headers(self.admin_token))
        assert r.status_code == 201
        assert r.json()["amount"] == 5000.0
        assert r.json()["category"] == "Salary"

    def test_create_transaction_as_viewer_forbidden(self):
        r = client.post("/transactions/", json={
            "amount": 100.0,
            "type": "expense",
            "category": "Food",
            "date": "2024-03-05"
        }, headers=auth_headers(self.viewer_token))
        assert r.status_code == 403

    def test_negative_amount_rejected(self):
        r = client.post("/transactions/", json={
            "amount": -500.0,
            "type": "expense",
            "category": "Bills",
            "date": "2024-03-10"
        }, headers=auth_headers(self.admin_token))
        assert r.status_code == 422

    def test_list_transactions(self):
        r = client.get("/transactions/", headers=auth_headers(self.viewer_token))
        assert r.status_code == 200
        assert isinstance(r.json(), list)

    def test_filter_by_type(self):
        r = client.get("/transactions/?tx_type=income", headers=auth_headers(self.admin_token))
        assert r.status_code == 200
        for tx in r.json():
            assert tx["type"] == "income"

    def test_filter_by_date_range(self):
        r = client.get(
            "/transactions/?start_date=2024-01-01&end_date=2024-12-31",
            headers=auth_headers(self.admin_token)
        )
        assert r.status_code == 200

    def test_pagination(self):
        r = client.get("/transactions/?skip=0&limit=5", headers=auth_headers(self.admin_token))
        assert r.status_code == 200
        assert len(r.json()) <= 5

    def test_unauthorized_access(self):
        r = client.get("/transactions/")
        assert r.status_code == 401

    def test_update_transaction(self):
        create_r = client.post("/transactions/", json={
            "amount": 200.0,
            "type": "expense",
            "category": "Transport",
            "date": "2024-04-01"
        }, headers=auth_headers(self.admin_token))
        tx_id = create_r.json()["id"]

        update_r = client.patch(f"/transactions/{tx_id}", json={
            "amount": 250.0,
            "notes": "Updated amount"
        }, headers=auth_headers(self.admin_token))
        assert update_r.status_code == 200
        assert update_r.json()["amount"] == 250.0

    def test_delete_transaction(self):
        create_r = client.post("/transactions/", json={
            "amount": 99.0,
            "type": "expense",
            "category": "Misc",
            "date": "2024-05-01"
        }, headers=auth_headers(self.admin_token))
        tx_id = create_r.json()["id"]

        delete_r = client.delete(f"/transactions/{tx_id}", headers=auth_headers(self.admin_token))
        assert delete_r.status_code == 204

        get_r = client.get(f"/transactions/{tx_id}", headers=auth_headers(self.admin_token))
        assert get_r.status_code == 404


# ── Summary Tests ─────────────────────────────────────────────────────────────
class TestSummary:
    def setup_method(self):
        self.analyst_token = register_and_login("summaryanalyst", "analyst")
        self.viewer_token = register_and_login("summaryviewer2", "viewer")

    def test_summary_accessible_by_analyst(self):
        r = client.get("/summary/", headers=auth_headers(self.analyst_token))
        assert r.status_code == 200
        data = r.json()
        assert "total_income" in data
        assert "total_expenses" in data
        assert "current_balance" in data
        assert "category_breakdown" in data
        assert "monthly_summaries" in data
        assert "recent_transactions" in data

    def test_summary_forbidden_for_viewer(self):
        r = client.get("/summary/", headers=auth_headers(self.viewer_token))
        assert r.status_code == 403


# ── Export Tests ──────────────────────────────────────────────────────────────
class TestExport:
    def setup_method(self):
        self.analyst_token = register_and_login("exportanalyst", "analyst")
        self.viewer_token = register_and_login("exportviewer", "viewer")

    def test_csv_export_analyst(self):
        r = client.get("/transactions/export/csv", headers=auth_headers(self.analyst_token))
        assert r.status_code == 200
        assert "text/csv" in r.headers["content-type"]

    def test_json_export_analyst(self):
        r = client.get("/transactions/export/json", headers=auth_headers(self.analyst_token))
        assert r.status_code == 200
        assert isinstance(r.json(), list)

    def test_csv_export_viewer_forbidden(self):
        r = client.get("/transactions/export/csv", headers=auth_headers(self.viewer_token))
        assert r.status_code == 403
