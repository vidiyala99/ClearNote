import uuid
from datetime import UTC, date, datetime, timedelta

import jwt
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.db.models.user import User
from app.db.models.visit import Visit

TEST_JWT_SECRET = "test-secret-key-with-32-characters"


def _create_mock_token(payload: dict) -> str:
    return jwt.encode(payload, TEST_JWT_SECRET, algorithm="HS256")


def test_create_visit_unauthorized(client: TestClient):
    """Wait for unauthorized status if token is missing."""
    response = client.get("/api/v1/visits") # Assuming there might be a GET or testing POST
    # We only have POST /visits
    response = client.post("/api/v1/visits", json={})
    assert response.status_code == 401


def test_create_visit_success(client: TestClient, db: Session):
    """Test successful creation of visit."""
    # Create test user
    user = User(
        id=uuid.uuid4(),
        email="doctor@example.com",
        clerk_user_id="clerk_doc_123",
        preferred_language="en"
    )
    db.add(user)
    db.commit()

    token = _create_mock_token({"sub": "clerk_doc_123", "email": "doctor@example.com"})

    payload = {
        "title": "Patient Consultation",
        "visit_date": str(date.today()),
        "doctor_name": "Dr. Smith",
        "consent_at": (datetime.now(UTC) - timedelta(minutes=5)).isoformat().replace("+00:00", "Z")
    }

    response = client.post(
        "/api/v1/visits",
        json=payload,
        headers={"Authorization": f"Bearer {token}"}
    )

    assert response.status_code == 200
    data = response.json()
    assert "visit_id" in data

    # Verify visit in DB
    visit_id = data["visit_id"]
    db_visit = db.query(Visit).filter(Visit.id == visit_id).first()
    assert db_visit is not None
    assert db_visit.title == "Patient Consultation"
    assert db_visit.user_id == user.id
