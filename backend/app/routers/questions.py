from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import Subgroup
from ..schemas import NextQuestionOut
from ..services import adaptive

router = APIRouter(prefix="/api/questions", tags=["questions"])


@router.get("/next", response_model=NextQuestionOut)
def get_next_question(subgroup: Subgroup, db: Session = Depends(get_db)) -> NextQuestionOut:
    """Serve a random unsolved question at the subgroup's current level.

    Falls back to the nearest level with unsolved questions; returns
    `question: null` with `exhausted: true` once the subgroup is fully solved.
    """
    picked = adaptive.pick_next_question(db, subgroup.value)
    db.commit()  # persist progress row created on first visit
    return NextQuestionOut(
        question=picked.question,
        current_level=picked.current_level,
        max_level=picked.max_level,
        remaining_at_level=picked.remaining_at_level,
        exhausted=picked.exhausted,
    )
