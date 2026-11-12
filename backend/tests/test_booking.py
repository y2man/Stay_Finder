"""Run against a real PostgreSQL: DATABASE_URL=... pytest (after `alembic upgrade head`)."""
from datetime import date, timedelta
from fastapi.testclient import TestClient
from app.main import app
from app.seed import run

c = TestClient(app)

def token(email):
    c.post("/api/v1/auth/register", json={"email": email, "password": "password123", "full_name": "T"})
    return {"Authorization": "Bearer " + c.post("/api/v1/auth/login", json={"email": email, "password": "password123"}).json()["access_token"]}

def test_overlap_blocked():
    run()
    pid = c.get("/api/v1/properties").json()["items"][0]["id"]
    a, b = token("a@t.dev"), token("b@t.dev")
    ci = date.today() + timedelta(days=30)
    body = {"property_id": pid, "check_in": str(ci), "check_out": str(ci + timedelta(days=3)), "guests": 1}
    assert c.post("/api/v1/bookings", json=body, headers=a).status_code == 201
    assert c.post("/api/v1/bookings", json=body, headers=b).status_code == 409
