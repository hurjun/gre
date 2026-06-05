"""Seed the database from the JSON files in ``app/seed/data``.

Question files are named ``<subgroup>_level_<n>.json`` and look like::

    {
      "group": "verbal",
      "subgroup": "se_tc",
      "level": 1,
      "questions": [
        {
          "question_type": "single" | "multi",
          "select_count": 1,
          "passage": null,
          "question_text": "...",
          "choices": ["..."],
          "answer": [0],
          "explanation_ko": "..."
        }
      ]
    }

Writing prompts live in ``writing_prompts.json``. Every record is validated
before anything is inserted, so a malformed file aborts the whole seed.

Usage (from ``backend/``)::

    python -m app.seed.seed            # seed only if the database is empty
    python -m app.seed.seed --force    # drop and recreate all tables first
"""

import argparse
import json
import sys
from pathlib import Path

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from ..database import Base, SessionLocal, engine
from ..models import Group, Question, QuestionType, Subgroup, TaskType, WritingPrompt

DATA_DIR = Path(__file__).parent / "data"


def _has_korean(text: str) -> bool:
    return any("가" <= char <= "힣" for char in text)


def _validate_question(record: dict, source: str) -> None:
    choices = record["choices"]
    answer = record["answer"]
    errors = []
    if record["question_type"] not in {t.value for t in QuestionType}:
        errors.append(f"unknown question_type {record['question_type']!r}")
    if len(choices) < 2:
        errors.append("needs at least 2 choices")
    if not answer:
        errors.append("empty answer")
    if any(not isinstance(i, int) or i < 0 or i >= len(choices) for i in answer):
        errors.append(f"answer indices {answer} out of range for {len(choices)} choices")
    if len(set(answer)) != len(answer):
        errors.append("duplicate answer indices")
    if record["select_count"] != len(answer):
        errors.append(f"select_count {record['select_count']} != len(answer) {len(answer)}")
    if (record["question_type"] == QuestionType.MULTI.value) != (len(answer) > 1):
        errors.append("question_type does not match answer count")
    if not record["question_text"].strip():
        errors.append("empty question_text")
    if not _has_korean(record["explanation_ko"]):
        errors.append("explanation_ko contains no Korean text")
    if errors:
        raise ValueError(f"{source}: {'; '.join(errors)}")


def load_questions(db: Session) -> int:
    count = 0
    for path in sorted(DATA_DIR.glob("*_level_*.json")):
        bucket = json.loads(path.read_text(encoding="utf-8"))
        group, subgroup, level = bucket["group"], bucket["subgroup"], bucket["level"]
        if group not in {g.value for g in Group}:
            raise ValueError(f"{path.name}: unknown group {group!r}")
        if subgroup not in {s.value for s in Subgroup}:
            raise ValueError(f"{path.name}: unknown subgroup {subgroup!r}")
        if not 1 <= level <= 5:
            raise ValueError(f"{path.name}: level {level} out of range")
        for index, record in enumerate(bucket["questions"]):
            _validate_question(record, f"{path.name}#{index}")
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
            count += 1
    return count


def load_writing_prompts(db: Session) -> int:
    path = DATA_DIR / "writing_prompts.json"
    if not path.exists():
        return 0
    prompts = json.loads(path.read_text(encoding="utf-8"))["prompts"]
    for index, record in enumerate(prompts):
        if record["task_type"] not in {t.value for t in TaskType}:
            raise ValueError(f"{path.name}#{index}: unknown task_type {record['task_type']!r}")
        if not record["prompt_text"].strip() or not record["model_answer"].strip():
            raise ValueError(f"{path.name}#{index}: empty prompt_text or model_answer")
        db.add(
            WritingPrompt(
                task_type=record["task_type"],
                prompt_text=record["prompt_text"],
                model_answer=record["model_answer"],
                suggested_minutes=record.get("suggested_minutes", 30),
            )
        )
    return len(prompts)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--force",
        action="store_true",
        help="drop and recreate all tables (erases attempts and essays) before seeding",
    )
    args = parser.parse_args()

    if args.force:
        Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)

    with SessionLocal() as db:
        existing = db.scalar(select(func.count()).select_from(Question)) or 0
        if existing:
            print(f"Database already has {existing} questions; use --force to reseed.")
            return 1
        questions = load_questions(db)
        prompts = load_writing_prompts(db)
        db.commit()

    print(f"Seeded {questions} questions and {prompts} writing prompts.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
