"""Adaptive question selection and leveling.

Rules:
- Each subgroup starts at level 1 and moves within [MIN_LEVEL, MAX_LEVEL].
- A correct answer moves the level up; an incorrect answer moves it down.
- A question answered correctly ("solved") is never served again; questions
  answered incorrectly stay in rotation.
- If the current level has no unsolved questions left, the nearest level that
  does is served instead (lower level preferred on ties), so practice never
  stalls before the whole subgroup is exhausted.
"""

import random
from dataclasses import dataclass

from sqlalchemy import Select, func, select
from sqlalchemy.orm import Session

from ..config import MAX_LEVEL, MIN_LEVEL, level_bounds
from ..models import Attempt, Question, SubgroupProgress


def get_or_create_progress(db: Session, subgroup: str) -> SubgroupProgress:
    progress = db.get(SubgroupProgress, subgroup)
    if progress is None:
        min_level, _ = level_bounds(subgroup)
        progress = SubgroupProgress(subgroup=subgroup, current_level=min_level)
        db.add(progress)
        db.flush()
    return progress


def level_sequence(
    current_level: int, min_level: int = MIN_LEVEL, max_level: int = MAX_LEVEL
) -> list[int]:
    """Levels to search for the next question, in priority order.

    The current level comes first, then *easier* levels (descending), and only
    then *harder* levels (ascending). This guarantees that when the current
    level is exhausted we fall back to an easier question before a harder one —
    so a wrong answer (which lowers the level) never leads to a harder question.
    """
    current_level = max(min_level, min(max_level, current_level))
    easier = list(
        range(current_level, min_level - 1, -1)
    )  # current, current-1, ... min
    harder = list(range(current_level + 1, max_level + 1))  # current+1, ... max
    return easier + harder


def _solved_ids() -> Select:
    """Subquery of question ids that have at least one correct attempt."""
    return select(Attempt.question_id).where(Attempt.correct.is_(True))


def _unsolved_ids_at_level(db: Session, subgroup: str, level: int) -> list[int]:
    return list(
        db.scalars(
            select(Question.id).where(
                Question.subgroup == subgroup,
                Question.level == level,
                Question.id.not_in(_solved_ids()),
            )
        )
    )


@dataclass
class NextQuestion:
    question: Question | None
    current_level: int
    max_level: int
    remaining_at_level: int
    exhausted: bool


def pick_next_question(
    db: Session, subgroup: str, exclude_id: int | None = None
) -> NextQuestion:
    """Pick a random unsolved question, preferring the current level.

    ``exclude_id`` (typically the question just answered) is skipped so a missed
    question never reappears back-to-back — unless it is the only one left at
    that level, in which case it is served rather than stalling.
    """
    progress = get_or_create_progress(db, subgroup)
    min_level, max_level = level_bounds(subgroup)
    for level in level_sequence(progress.current_level, min_level, max_level):
        candidate_ids = _unsolved_ids_at_level(db, subgroup, level)
        if exclude_id is not None and len(candidate_ids) > 1:
            candidate_ids = [qid for qid in candidate_ids if qid != exclude_id]
        if candidate_ids:
            question = db.get(Question, random.choice(candidate_ids))
            return NextQuestion(
                question=question,
                current_level=progress.current_level,
                max_level=max_level,
                remaining_at_level=len(candidate_ids),
                exhausted=False,
            )
    return NextQuestion(
        question=None,
        current_level=progress.current_level,
        max_level=max_level,
        remaining_at_level=0,
        exhausted=True,
    )


@dataclass
class GradedAnswer:
    correct: bool
    correct_answer: list[int]
    explanation_ko: str
    previous_level: int
    new_level: int


def grade_answer(
    db: Session, question: Question, selected: list[int], elapsed_seconds: int
) -> GradedAnswer:
    """Grade a submission, record the attempt, and adjust the level."""
    correct = sorted(selected) == sorted(question.answer)

    progress = get_or_create_progress(db, question.subgroup)
    min_level, max_level = level_bounds(question.subgroup)
    previous_level = progress.current_level
    if correct:
        progress.current_level = min(max_level, previous_level + 1)
    else:
        progress.current_level = max(min_level, previous_level - 1)

    db.add(
        Attempt(
            question_id=question.id,
            selected=selected,
            correct=correct,
            elapsed_seconds=elapsed_seconds,
        )
    )
    db.commit()

    return GradedAnswer(
        correct=correct,
        correct_answer=list(question.answer),
        explanation_ko=question.explanation_ko,
        previous_level=previous_level,
        new_level=progress.current_level,
    )


def subgroup_stats(db: Session, subgroup: str) -> tuple[int, int]:
    """Return (solved, total) question counts for a subgroup."""
    total = db.scalar(
        select(func.count()).select_from(Question).where(Question.subgroup == subgroup)
    )
    solved = db.scalar(
        select(func.count(func.distinct(Attempt.question_id)))
        .select_from(Attempt)
        .join(Question, Question.id == Attempt.question_id)
        .where(Question.subgroup == subgroup, Attempt.correct.is_(True))
    )
    return int(solved or 0), int(total or 0)
