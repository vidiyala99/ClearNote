import uuid

import jwt
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.db.models.user import User


def _create_mock_token(payload: dict) -> str:
    """Create an unverified RS256 token that test/dev auth middleware can decode."""
    return jwt.encode(payload, "secret", algorithm="HS256")


def test_users_me_unauthorized(client: TestClient):
    """Missing Authorization header returns 401."""
    response = client.get("/api/v1/users/me")
    assert response.status_code == 401
    assert response.json() == {"error": {"code": "UNAUTHORIZED"}}


def test_users_me_invalid_token(client: TestClient):
    """Invalid token returns 401."""
    response = client.get("/api/v1/users/me", headers={"Authorization": "Bearer not-a-jwt"})
    assert response.status_code == 401
    assert response.json() == {"error": {"code": "UNAUTHORIZED"}}


def test_users_me_creates_user_if_missing(client: TestClient, db: Session):
    """Creating a new user with valid token."""
    clerk_id = f"user_test_{uuid.uuid4().hex[:8]}"
    email = f"test_{clerk_id}@example.com"
    token = _create_mock_token({"sub": clerk_id, "email": email})

    # Verify user does NOT exist
    assert db.query(User).filter(User.clerk_user_id == clerk_id).first() is None

    response = client.get("/api/v1/users/me", headers={"Authorization": f"Bearer {token}"})

    assert response.status_code == 200
    data = response.json()
    assert data["clerk_user_id"] == clerk_id
    assert data["email"] == email

    # Verify DB entry exists
    db_user = db.query(User).filter(User.clerk_user_id == clerk_id).first()
    assert db_user is not None
    assert db_user.email == email


def test_users_me_updates_email_on_conflict(client: TestClient, db: Session):
    """Valid token with updated email updates existing user."""
    clerk_id = f"user_test_{uuid.uuid4().hex[:8]}"
    old_email = f"old_{clerk_id}@example.com"
    new_email = f"new_{clerk_id}@example.com"

    # Create user beforehand
    user = User(id=uuid.uuid4(), clerk_user_id=clerk_id, email=old_email, preferred_language="en")
    db.add(user)
    db.commit()

    token = _create_mock_token({"sub": clerk_id, "email": new_email})

    response = client.get("/api/v1/users/me", headers={"Authorization": f"Bearer {token}"})

    assert response.status_code == 200
    data = response.json()
    assert data["email"] == new_email

    # Verify DB updated
    db.refresh(user)
    assert user.email == new_email
