from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import Question
from ..schemas import AnswerIn, AnswerOut
from ..services import adaptive

router = APIRouter(prefix="/api/answers", tags=["answers"])


@router.post("", response_model=AnswerOut)
def submit_answer(payload: AnswerIn, db: Session = Depends(get_db)) -> AnswerOut:
    """Grade a submission, record the attempt, and move the level up or down."""
    question = db.get(Question, payload.question_id)
    if question is None:
        raise HTTPException(status_code=404, detail="Question not found")

    if any(i < 0 or i >= len(question.choices) for i in payload.selected):
        raise HTTPException(status_code=422, detail="Selected choice index out of range")

    graded = adaptive.grade_answer(db, question, payload.selected, payload.elapsed_seconds)
    return AnswerOut(
        correct=graded.correct,
        correct_answer=graded.correct_answer,
        explanation_ko=graded.explanation_ko,
        previous_level=graded.previous_level,
        new_level=graded.new_level,
    )
