"""API tests covering the question, answer, progress, and writing endpoints."""

from app.models import WritingPrompt


def test_next_question_hides_answer_key(client, make_question):
    make_question(level=1)

    body = client.get("/api/questions/next", params={"subgroup": "se_tc"}).json()

    assert body["question"] is not None
    assert "answer" not in body["question"]
    assert "explanation_ko" not in body["question"]


def test_next_question_rejects_unknown_subgroup(client):
    response = client.get("/api/questions/next", params={"subgroup": "nope"})

    assert response.status_code == 422


def test_next_question_exhausted_on_empty_bank(client):
    body = client.get("/api/questions/next", params={"subgroup": "quant"}).json()

    assert body["question"] is None
    assert body["exhausted"] is True


def test_submit_unknown_question_returns_404(client):
    response = client.post("/api/answers", json={"question_id": 999, "selected": [0]})

    assert response.status_code == 404


def test_submit_out_of_range_choice_returns_422(client, make_question):
    question = make_question(n_choices=5)

    response = client.post(
        "/api/answers", json={"question_id": question.id, "selected": [5]}
    )

    assert response.status_code == 422


def test_wrong_answer_returns_korean_explanation_and_level(client, make_question):
    question = make_question(
        level=1, answer=(0,), explanation_ko="정답은 첫 번째입니다."
    )

    body = client.post(
        "/api/answers",
        json={"question_id": question.id, "selected": [2], "elapsed_seconds": 42},
    ).json()

    assert body["correct"] is False
    assert body["correct_answer"] == [0]
    assert body["explanation_ko"] == "정답은 첫 번째입니다."
    assert body["previous_level"] == 1
    assert body["new_level"] == 1


def test_correct_answer_levels_up(client, make_question):
    question = make_question(level=1)

    body = client.post(
        "/api/answers", json={"question_id": question.id, "selected": [0]}
    ).json()

    assert body["correct"] is True
    assert body["new_level"] == 2


def test_progress_reports_all_subgroups(client, make_question):
    question = make_question(subgroup="quant", group="math")
    client.post("/api/answers", json={"question_id": question.id, "selected": [0]})

    body = client.get("/api/progress").json()
    by_subgroup = {entry["subgroup"]: entry for entry in body["subgroups"]}

    assert set(by_subgroup) == {"se_tc", "reading_reasoning", "quant", "vocabulary"}
    assert by_subgroup["quant"] == {
        "subgroup": "quant",
        "current_level": 2,
        "max_level": 5,
        "solved": 1,
        "total": 1,
    }
    assert by_subgroup["vocabulary"]["max_level"] == 10


def _add_prompt(db) -> WritingPrompt:
    prompt = WritingPrompt(
        task_type="issue",
        prompt_text="Discuss the statement.",
        model_answer="A model essay.",
        suggested_minutes=30,
    )
    db.add(prompt)
    db.commit()
    return prompt


def test_writing_prompt_listing_and_detail(client, db):
    prompt = _add_prompt(db)

    summaries = client.get("/api/writing/prompts").json()
    assert len(summaries) == 1
    assert summaries[0]["essay_count"] == 0

    detail = client.get(f"/api/writing/prompts/{prompt.id}").json()
    assert detail["model_answer"] == "A model essay."


def test_writing_prompt_not_found(client):
    assert client.get("/api/writing/prompts/999").status_code == 404


def test_essay_submission_and_history(client, db):
    prompt = _add_prompt(db)

    body = client.post(
        "/api/writing/essays",
        json={
            "prompt_id": prompt.id,
            "essay_text": "My essay.",
            "self_grade": 4.5,
            "elapsed_seconds": 1500,
        },
    ).json()
    assert body["self_grade"] == 4.5

    essays = client.get("/api/writing/essays", params={"prompt_id": prompt.id}).json()
    assert len(essays) == 1

    summaries = client.get("/api/writing/prompts").json()
    assert summaries[0]["essay_count"] == 1


def test_essay_rejects_unknown_prompt(client):
    response = client.post(
        "/api/writing/essays",
        json={"prompt_id": 999, "essay_text": "x", "self_grade": 3},
    )

    assert response.status_code == 404


def test_essay_rejects_out_of_scale_grade(client, db):
    prompt = _add_prompt(db)

    response = client.post(
        "/api/writing/essays",
        json={"prompt_id": prompt.id, "essay_text": "x", "self_grade": 6.5},
    )

    assert response.status_code == 422
