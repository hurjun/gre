"""Tests for the idempotent content sync.

These run against the real JSON content bank (the same files CI validates),
verifying that sync inserts content, refreshes changed fields, is idempotent,
and never disturbs a learner's attempts.
"""

from app.models import Attempt, Question, WritingPrompt
from app.seed import sync
from app.services import adaptive


def test_sync_populates_an_empty_database(db):
    inserted, updated = sync.sync_questions(db)
    db.commit()

    assert inserted > 0
    assert updated == 0
    assert db.query(Question).count() == inserted


def test_sync_is_idempotent(db):
    sync.sync_questions(db)
    db.commit()
    count_after_first = db.query(Question).count()

    inserted, updated = sync.sync_questions(db)
    db.commit()

    assert inserted == 0
    assert updated == 0
    assert db.query(Question).count() == count_after_first


def test_sync_refreshes_changed_fields_without_reinserting(db):
    sync.sync_questions(db)
    db.commit()
    victim = db.query(Question).first()
    original_text = victim.question_text
    victim.explanation_ko = "stale"
    db.commit()

    inserted, updated = sync.sync_questions(db)
    db.commit()

    assert inserted == 0
    assert updated == 1
    refreshed = db.query(Question).filter_by(question_text=original_text).one()
    assert refreshed.explanation_ko != "stale"


def test_sync_preserves_attempts(db):
    sync.sync_questions(db)
    db.commit()
    question = db.query(Question).first()
    adaptive.grade_answer(db, question, list(question.answer), elapsed_seconds=5)
    assert db.query(Attempt).count() == 1

    sync.sync_questions(db)
    db.commit()

    # the attempt and its question survive a re-sync, and the question keeps its id
    assert db.query(Attempt).count() == 1
    assert db.get(Question, question.id) is not None


def test_sync_writing_prompts_inserts_then_is_idempotent(db):
    inserted, updated = sync.sync_writing_prompts(db)
    db.commit()
    assert inserted > 0
    assert updated == 0
    assert db.query(WritingPrompt).count() == inserted

    again_inserted, again_updated = sync.sync_writing_prompts(db)
    db.commit()
    assert (again_inserted, again_updated) == (0, 0)


def test_sync_writing_prompts_refreshes_a_changed_model_answer(db):
    sync.sync_writing_prompts(db)
    db.commit()
    victim = db.query(WritingPrompt).first()
    original_text = victim.prompt_text
    victim.model_answer = "stale"
    db.commit()

    inserted, updated = sync.sync_writing_prompts(db)
    db.commit()

    assert inserted == 0
    assert updated == 1
    refreshed = db.query(WritingPrompt).filter_by(prompt_text=original_text).one()
    assert refreshed.model_answer != "stale"
