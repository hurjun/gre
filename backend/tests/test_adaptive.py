"""Unit tests for the adaptive leveling service."""

from app.services import adaptive


def test_level_sequence_orders_by_distance_with_lower_preferred():
    assert adaptive.level_sequence(3) == [3, 2, 4, 1, 5]
    assert adaptive.level_sequence(1) == [1, 2, 3, 4, 5]
    assert adaptive.level_sequence(5) == [5, 4, 3, 2, 1]


def test_level_sequence_respects_custom_bounds():
    assert adaptive.level_sequence(7, 1, 10) == [7, 6, 8, 5, 9, 4, 10, 3, 2, 1]
    assert adaptive.level_sequence(1, 1, 10)[0] == 1
    assert max(adaptive.level_sequence(10, 1, 10)) == 10


def test_pick_prefers_current_level(db, make_question):
    make_question(level=1, question_text="level one")
    make_question(level=2, question_text="level two")

    picked = adaptive.pick_next_question(db, "se_tc")

    assert picked.question is not None
    assert picked.question.level == 1
    assert picked.current_level == 1
    assert picked.remaining_at_level == 1
    assert not picked.exhausted


def test_pick_falls_back_to_nearest_level_with_unsolved(db, make_question):
    # nothing at level 1; nearest available is level 2 (not level 4)
    make_question(level=2, question_text="level two")
    make_question(level=4, question_text="level four")

    picked = adaptive.pick_next_question(db, "se_tc")

    assert picked.question.level == 2


def test_pick_exhausted_when_all_solved(db, make_question):
    question = make_question(level=1)
    adaptive.grade_answer(db, question, list(question.answer), elapsed_seconds=10)

    picked = adaptive.pick_next_question(db, "se_tc")

    assert picked.question is None
    assert picked.exhausted
    assert picked.remaining_at_level == 0


def test_correct_answer_levels_up(db, make_question):
    question = make_question(level=1)

    graded = adaptive.grade_answer(db, question, list(question.answer), elapsed_seconds=5)

    assert graded.correct
    assert graded.previous_level == 1
    assert graded.new_level == 2


def test_level_caps_at_max(db, make_question):
    progress = adaptive.get_or_create_progress(db, "se_tc")
    progress.current_level = 5
    question = make_question(level=5)

    graded = adaptive.grade_answer(db, question, list(question.answer), elapsed_seconds=5)

    assert graded.correct
    assert graded.new_level == 5


def test_incorrect_answer_levels_down_and_floors_at_min(db, make_question):
    question = make_question(level=1, answer=(0,))

    graded = adaptive.grade_answer(db, question, [1], elapsed_seconds=5)

    assert not graded.correct
    assert graded.previous_level == 1
    assert graded.new_level == 1  # already at the floor


def test_multi_answer_graded_order_independent(db, make_question):
    question = make_question(answer=(1, 4), n_choices=6)

    graded = adaptive.grade_answer(db, question, [4, 1], elapsed_seconds=5)

    assert graded.correct


def test_partial_multi_answer_is_incorrect(db, make_question):
    question = make_question(answer=(1, 4), n_choices=6)

    graded = adaptive.grade_answer(db, question, [1], elapsed_seconds=5)

    assert not graded.correct


def test_incorrect_question_stays_in_rotation(db, make_question):
    question = make_question(level=1, answer=(0,))
    adaptive.grade_answer(db, question, [1], elapsed_seconds=5)

    picked = adaptive.pick_next_question(db, "se_tc")

    assert picked.question is not None
    assert picked.question.id == question.id


def test_solved_question_never_served_again(db, make_question):
    solved = make_question(level=1, question_text="solved")
    other = make_question(level=1, question_text="other")
    adaptive.grade_answer(db, solved, list(solved.answer), elapsed_seconds=5)

    for _ in range(10):  # selection is random; any draw must avoid the solved one
        picked = adaptive.pick_next_question(db, "se_tc")
        assert picked.question.id == other.id


def test_progress_is_per_subgroup(db, make_question):
    verbal = make_question(subgroup="se_tc", level=1)
    quant = make_question(subgroup="quant", group="math", level=1)

    adaptive.grade_answer(db, verbal, list(verbal.answer), elapsed_seconds=5)
    adaptive.grade_answer(db, quant, [1], elapsed_seconds=5)  # wrong on purpose

    assert adaptive.get_or_create_progress(db, "se_tc").current_level == 2
    assert adaptive.get_or_create_progress(db, "quant").current_level == 1


def test_vocabulary_uses_ten_level_ladder(db, make_question):
    # vocabulary climbs to 10, not 5
    progress = adaptive.get_or_create_progress(db, "vocabulary")
    progress.current_level = 5
    question = make_question(subgroup="vocabulary", group="vocabulary", level=6)

    graded = adaptive.grade_answer(db, question, list(question.answer), elapsed_seconds=5)

    assert graded.new_level == 6  # would have capped at 5 under the old bounds


def test_vocabulary_caps_at_ten(db, make_question):
    progress = adaptive.get_or_create_progress(db, "vocabulary")
    progress.current_level = 10
    question = make_question(subgroup="vocabulary", group="vocabulary", level=10)

    graded = adaptive.grade_answer(db, question, list(question.answer), elapsed_seconds=5)

    assert graded.new_level == 10


def test_pick_reports_max_level_per_subgroup(db, make_question):
    make_question(subgroup="vocabulary", group="vocabulary", level=1)
    make_question(subgroup="se_tc", level=1)

    assert adaptive.pick_next_question(db, "vocabulary").max_level == 10
    assert adaptive.pick_next_question(db, "se_tc").max_level == 5


def test_subgroup_stats_counts_distinct_solved(db, make_question):
    question = make_question(level=1)
    make_question(level=2)
    # two correct attempts on the same question must count once
    adaptive.grade_answer(db, question, list(question.answer), elapsed_seconds=5)
    adaptive.grade_answer(db, question, list(question.answer), elapsed_seconds=5)

    solved, total = adaptive.subgroup_stats(db, "se_tc")

    assert (solved, total) == (1, 2)
