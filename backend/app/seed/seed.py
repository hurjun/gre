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

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from ..database import Base, SessionLocal, engine
from ..models import Question, WritingPrompt
from .validate import DATA_DIR, validate


def load_questions(db: Session) -> int:
    count = 0
    for path in sorted(DATA_DIR.glob("*_level_*.json")):
        bucket = json.loads(path.read_text(encoding="utf-8"))
        group, subgroup, level = bucket["group"], bucket["subgroup"], bucket["level"]
        for record in bucket["questions"]:
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
    for record in prompts:
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

    problems = validate()
    if problems:
        print(f"Refusing to seed: {len(problems)} validation problem(s):")
        for problem in problems:
            print(f"  - {problem}")
        return 1

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
