"""Validate the JSON seed files without touching the database.

Used in CI (and runnable locally with ``python -m app.seed.validate``) to catch
malformed questions or writing prompts before they ever reach MySQL. Exits
non-zero and prints every problem found.
"""

import json
import sys
from pathlib import Path

from ..config import level_bounds
from ..models import Group, QuestionType, Subgroup, TaskType

DATA_DIR = Path(__file__).parent / "data"

VALID_GROUPS = {g.value for g in Group}
VALID_SUBGROUPS = {s.value for s in Subgroup}
VALID_QTYPES = {t.value for t in QuestionType}
VALID_TASKTYPES = {t.value for t in TaskType}


def _has_korean(text: str) -> bool:
    return any("가" <= char <= "힣" for char in text)


def _check_question(record: dict, source: str, errors: list[str]) -> None:
    def err(msg: str) -> None:
        errors.append(f"{source}: {msg}")

    choices = record.get("choices")
    answer = record.get("answer")
    if not isinstance(choices, list) or len(choices) < 2:
        err("needs at least 2 choices")
        return
    if not isinstance(answer, list) or not answer:
        err("empty or missing answer")
        return
    if record.get("question_type") not in VALID_QTYPES:
        err(f"unknown question_type {record.get('question_type')!r}")
    if any(not isinstance(i, int) or i < 0 or i >= len(choices) for i in answer):
        err(f"answer indices {answer} out of range for {len(choices)} choices")
    if len(set(answer)) != len(answer):
        err("duplicate answer indices")
    if record.get("select_count") != len(answer):
        err(f"select_count {record.get('select_count')} != len(answer) {len(answer)}")
    if (record.get("question_type") == QuestionType.MULTI.value) != (len(answer) > 1):
        err("question_type does not match answer count")
    if not str(record.get("question_text", "")).strip():
        err("empty question_text")
    if not _has_korean(str(record.get("explanation_ko", ""))):
        err("explanation_ko contains no Korean text")


def validate() -> list[str]:
    errors: list[str] = []

    buckets = sorted(DATA_DIR.glob("*_level_*.json"))
    if not buckets:
        errors.append(f"no question files found in {DATA_DIR}")

    for path in buckets:
        try:
            bucket = json.loads(path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, UnicodeDecodeError) as exc:
            errors.append(f"{path.name}: invalid JSON ({exc})")
            continue
        if bucket.get("group") not in VALID_GROUPS:
            errors.append(f"{path.name}: unknown group {bucket.get('group')!r}")
        subgroup = bucket.get("subgroup")
        if subgroup not in VALID_SUBGROUPS:
            errors.append(f"{path.name}: unknown subgroup {subgroup!r}")
        else:
            low, high = level_bounds(subgroup)
            if bucket.get("level") not in range(low, high + 1):
                errors.append(
                    f"{path.name}: level {bucket.get('level')!r} out of range "
                    f"[{low}, {high}] for subgroup {subgroup!r}"
                )
        questions = bucket.get("questions", [])
        if not questions:
            errors.append(f"{path.name}: no questions")
        for index, record in enumerate(questions):
            _check_question(record, f"{path.name}#{index}", errors)

    prompts_path = DATA_DIR / "writing_prompts.json"
    if prompts_path.exists():
        try:
            prompts = json.loads(prompts_path.read_text(encoding="utf-8")).get(
                "prompts", []
            )
        except (json.JSONDecodeError, UnicodeDecodeError) as exc:
            errors.append(f"{prompts_path.name}: invalid JSON ({exc})")
            prompts = []
        for index, record in enumerate(prompts):
            source = f"{prompts_path.name}#{index}"
            if record.get("task_type") not in VALID_TASKTYPES:
                errors.append(
                    f"{source}: unknown task_type {record.get('task_type')!r}"
                )
            if not str(record.get("prompt_text", "")).strip():
                errors.append(f"{source}: empty prompt_text")
            if not str(record.get("model_answer", "")).strip():
                errors.append(f"{source}: empty model_answer")

    return errors


def main() -> int:
    errors = validate()
    if errors:
        print(f"Seed validation failed with {len(errors)} problem(s):")
        for problem in errors:
            print(f"  - {problem}")
        return 1
    print("Seed data is valid.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
