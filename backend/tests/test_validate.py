"""Tests for the database-free seed validator that gates content in CI.

The validator is what stops a malformed question or prompt from ever reaching
the database, so its rules are worth pinning down directly.
"""

from app.seed import validate


def _good_question() -> dict:
    return {
        "question_type": "single",
        "select_count": 1,
        "passage": None,
        "question_text": "Pick the nearest synonym.",
        "choices": ["a", "b", "c", "d", "e"],
        "answer": [0],
        "explanation_ko": "정답은 a 입니다.",
    }


def _errors_for(record: dict) -> list[str]:
    errors: list[str] = []
    validate._check_question(record, "src", errors)
    return errors


def test_has_korean_detects_hangul():
    assert validate._has_korean("정답입니다")
    assert not validate._has_korean("answer only, no hangul")


def test_real_content_bank_is_valid():
    # The bundled JSON bank (the same files CI checks) must validate cleanly.
    assert validate.validate() == []


def test_a_well_formed_question_produces_no_errors():
    assert _errors_for(_good_question()) == []


def test_answer_index_out_of_range_is_flagged():
    assert any(
        "out of range" in e for e in _errors_for(_good_question() | {"answer": [9]})
    )


def test_select_count_must_match_answer_length():
    assert any(
        "select_count" in e for e in _errors_for(_good_question() | {"select_count": 2})
    )


def test_multi_type_requires_multiple_answers():
    # question_type "multi" but a single answer index is contradictory
    record = _good_question() | {"question_type": "multi"}
    assert any("does not match answer count" in e for e in _errors_for(record))


def test_duplicate_answer_indices_are_flagged():
    record = _good_question() | {
        "answer": [0, 0],
        "select_count": 2,
        "question_type": "multi",
    }
    assert any("duplicate" in e for e in _errors_for(record))


def test_missing_korean_explanation_is_flagged():
    record = _good_question() | {"explanation_ko": "no hangul here"}
    assert any("Korean" in e for e in _errors_for(record))


def test_too_few_choices_is_flagged():
    assert any(
        "at least 2 choices" in e
        for e in _errors_for(_good_question() | {"choices": ["x"]})
    )


def test_empty_question_text_is_flagged():
    assert any(
        "empty question_text" in e
        for e in _errors_for(_good_question() | {"question_text": "  "})
    )
