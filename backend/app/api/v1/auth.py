import uuid

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.orm import Session

from app.db.models.user import User
from app.db.session import get_db
from app.schemas.user import UserOut

router = APIRouter()


@router.get("/users/me", response_model=UserOut)
def get_me(request: Request, db: Session = Depends(get_db)):
    """
    Get current user details. Performs an idempotent upsert of the user
    based on the clerk_user_id provided by the middleware.
    """
    clerk_id = getattr(request.state, "clerk_user_id", None)
    email = getattr(request.state, "email", None)

    if not clerk_id:
        raise HTTPException(
            status_code=401, detail={"error": {"code": "UNAUTHORIZED"}}
        )

    # Use a fallback email if it is somehow missing from JWT claims,
    # as email is NOT NULL in the users table.
    if not email:
        email = f"{clerk_id}@clerk.user"

    stmt = insert(User).values(
        id=uuid.uuid4(),
        clerk_user_id=clerk_id,
        email=email,
        preferred_language="en",
    ).on_conflict_do_update(
        index_elements=[User.clerk_user_id],
        set_={"email": email}
    ).returning(User)

    try:
        result = db.execute(stmt)
        db.commit()
        user = result.scalar_one()
        return user
    except Exception as exc:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(exc))
