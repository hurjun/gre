"""HTTP routes for serving the next adaptive question."""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import Subgroup
from ..schemas import NextQuestionOut, QuestionOut
from ..services import adaptive

router = APIRouter(prefix="/api/questions", tags=["questions"])


@router.get("/next", response_model=NextQuestionOut)
def get_next_question(
    subgroup: Subgroup,
    exclude: int | None = None,
    db: Session = Depends(get_db),
) -> NextQuestionOut:
    """Serve a random unsolved question at the subgroup's current level.

    Falls back to easier levels (then harder) when the current level has no
    unsolved questions left; returns `question: null` with `exhausted: true`
    once the subgroup is fully solved. ``exclude`` is the question just
    answered, so it is not served again immediately when alternatives exist.
    """
    picked = adaptive.pick_next_question(db, subgroup.value, exclude_id=exclude)
    db.commit()  # persist progress row created on first visit
    question = QuestionOut.model_validate(picked.question) if picked.question else None
    return NextQuestionOut(
        question=question,
        current_level=picked.current_level,
        max_level=picked.max_level,
        remaining_at_level=picked.remaining_at_level,
        exhausted=picked.exhausted,
    )
