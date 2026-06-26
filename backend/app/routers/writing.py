"""HTTP routes for writing prompts and self-graded essays."""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import Essay, WritingPrompt
from ..schemas import EssayIn, EssayOut, WritingPromptOut, WritingPromptSummary

router = APIRouter(prefix="/api/writing", tags=["writing"])


@router.get("/prompts", response_model=list[WritingPromptSummary])
def list_prompts(db: Session = Depends(get_db)) -> list[WritingPromptSummary]:
    """All essay prompts with how many essays have been written for each."""
    rows = db.execute(
        select(WritingPrompt, func.count(Essay.id))
        .outerjoin(Essay, Essay.prompt_id == WritingPrompt.id)
        .group_by(WritingPrompt.id)
        .order_by(WritingPrompt.id)
    ).all()
    return [
        WritingPromptSummary(
            id=prompt.id,
            task_type=prompt.task_type,
            prompt_text=prompt.prompt_text,
            suggested_minutes=prompt.suggested_minutes,
            essay_count=essay_count,
        )
        for prompt, essay_count in rows
    ]


@router.get("/prompts/{prompt_id}", response_model=WritingPromptOut)
def get_prompt(prompt_id: int, db: Session = Depends(get_db)) -> WritingPrompt:
    """One prompt including its model answer (client reveals it after writing)."""
    prompt = db.get(WritingPrompt, prompt_id)
    if prompt is None:
        raise HTTPException(status_code=404, detail="Prompt not found")
    return prompt


@router.post("/essays", response_model=EssayOut)
def submit_essay(payload: EssayIn, db: Session = Depends(get_db)) -> Essay:
    """Save an essay together with the user's self-grade (0-6 scale)."""
    if db.get(WritingPrompt, payload.prompt_id) is None:
        raise HTTPException(status_code=404, detail="Prompt not found")

    essay = Essay(
        prompt_id=payload.prompt_id,
        essay_text=payload.essay_text,
        self_grade=payload.self_grade,
        elapsed_seconds=payload.elapsed_seconds,
    )
    db.add(essay)
    db.commit()
    db.refresh(essay)
    return essay


@router.get("/essays", response_model=list[EssayOut])
def list_essays(
    prompt_id: int | None = None, db: Session = Depends(get_db)
) -> list[Essay]:
    """Essay history, optionally filtered to one prompt."""
    query = select(Essay).order_by(Essay.created_at.desc())
    if prompt_id is not None:
        query = query.where(Essay.prompt_id == prompt_id)
    return list(db.scalars(query))
