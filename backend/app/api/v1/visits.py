import uuid
from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session

from app.db.models.user import User
from app.db.models.visit import Visit
from app.db.session import get_db
from app.schemas.visit import VisitCreate

router = APIRouter()


@router.post("/visits", response_model=dict)
def create_visit(request: Request, visit_data: VisitCreate, db: Session = Depends(get_db)):
    """
    Creates a new visit with status='pending'.
    Returns the created visit_id.
    """
    clerk_id = getattr(request.state, "clerk_user_id", None)
    if not clerk_id:
        raise HTTPException(
            status_code=401, detail={"error": {"code": "UNAUTHORIZED"}}
        )

    # Lookup user from DB, since user_id FK is required
    user = db.query(User).filter(User.clerk_user_id == clerk_id).first()
    if not user:
        raise HTTPException(
            status_code=401, detail={"error": {"code": "UNAUTHORIZED"}}
        )

    # Create visit
    visit = Visit(
        id=uuid.uuid4(),
        user_id=user.id,
        title=visit_data.title,
        visit_date=visit_data.visit_date,
        doctor_name=visit_data.doctor_name,
        consent_at=visit_data.consent_at
    )
    db.add(visit)
    db.commit()
    db.refresh(visit)

    return {"visit_id": visit.id}
