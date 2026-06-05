"""Idempotently sync the JSON content bank into the database.

Unlike ``seed`` (which only populates an empty database), ``sync`` upserts:
new questions and writing prompts are inserted, and existing ones have their
mutable fields refreshed — all **without** touching ``attempts`` or
``progress``, so a learner's history survives content updates and additions.

Questions are matched on the natural key ``(subgroup, level, passage,
question_text)`` — the passage is part of the key because distinct reading
questions often share a generic stem (e.g. "The primary purpose of the passage
is to") and differ only in their passage. Writing prompts are matched on
``(task_type, prompt_text)``.

Usage (from ``backend/``)::

    python -m app.seed.sync
"""

import json
import sys

from sqlalchemy import select
from sqlalchemy.orm import Session

from ..database import Base, SessionLocal, engine
from ..models import Question, WritingPrompt
from .validate import DATA_DIR, validate


def sync_questions(db: Session) -> tuple[int, int]:
    existing = {
        (q.subgroup, q.level, q.passage, q.question_text): q
        for q in db.scalars(select(Question))
    }
    inserted = updated = 0
    for path in sorted(DATA_DIR.glob("*_level_*.json")):
        bucket = json.loads(path.read_text(encoding="utf-8"))
        group, subgroup, level = bucket["group"], bucket["subgroup"], bucket["level"]
        for record in bucket["questions"]:
            key = (subgroup, level, record.get("passage"), record["question_text"])
            question = existing.get(key)
            if question is None:
                db.add(
                    Question(
                        group=group,
                        subgroup=subgroup,
                        level=level,
                        question_type=record["question_type"],
                        select_count=record["select_count"],
                        passage=record.get("passage"),
                        question_text=record["question_text"],
                        choices=record["choices"],
                        answer=record["answer"],
                        explanation_ko=record["explanation_ko"],
                    )
                )
                inserted += 1
            else:
                changed = (
                    question.choices != record["choices"]
                    or question.answer != record["answer"]
                    or question.explanation_ko != record["explanation_ko"]
                    or question.question_type != record["question_type"]
                    or question.select_count != record["select_count"]
                    or question.passage != record.get("passage")
                    or question.group != group
                )
                if changed:
                    question.group = group
                    question.question_type = record["question_type"]
                    question.select_count = record["select_count"]
                    question.passage = record.get("passage")
                    question.choices = record["choices"]
                    question.answer = record["answer"]
                    question.explanation_ko = record["explanation_ko"]
                    updated += 1
    return inserted, updated


def sync_writing_prompts(db: Session) -> tuple[int, int]:
    path = DATA_DIR / "writing_prompts.json"
    if not path.exists():
        return 0, 0
    existing = {
        (p.task_type, p.prompt_text): p for p in db.scalars(select(WritingPrompt))
    }
    inserted = updated = 0
    for record in json.loads(path.read_text(encoding="utf-8"))["prompts"]:
        key = (record["task_type"], record["prompt_text"])
        prompt = existing.get(key)
        if prompt is None:
            db.add(
                WritingPrompt(
                    task_type=record["task_type"],
                    prompt_text=record["prompt_text"],
                    model_answer=record["model_answer"],
                    suggested_minutes=record.get("suggested_minutes", 30),
                )
            )
            inserted += 1
        elif (
            prompt.model_answer != record["model_answer"]
            or prompt.suggested_minutes != record.get("suggested_minutes", 30)
        ):
            prompt.model_answer = record["model_answer"]
            prompt.suggested_minutes = record.get("suggested_minutes", 30)
            updated += 1
    return inserted, updated


def main() -> int:
    problems = validate()
    if problems:
        print(f"Refusing to sync: {len(problems)} validation problem(s):")
        for problem in problems:
            print(f"  - {problem}")
        return 1

    Base.metadata.create_all(bind=engine)
    with SessionLocal() as db:
        q_ins, q_upd = sync_questions(db)
        p_ins, p_upd = sync_writing_prompts(db)
        db.commit()

    print(
        f"Questions: +{q_ins} new, {q_upd} updated. "
        f"Writing prompts: +{p_ins} new, {p_upd} updated."
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
