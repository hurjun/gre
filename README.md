# GRE Study — Adaptive Practice Platform

A full-stack web application for self-directed GRE preparation. It serves one
question at a time and **adapts to the learner**: answer correctly and the next
question is harder; miss one and the difficulty steps back down, accompanied by
a worked explanation in Korean. Questions you solve are retired so you never see
them twice, while questions you miss return later — turning a static question
bank into a personalized study loop.

<p>
  <img alt="CI" src="https://github.com/hurjun/gre/actions/workflows/ci.yml/badge.svg" />
  <img alt="Python" src="https://img.shields.io/badge/Python-3.13-3776AB?logo=python&logoColor=white" />
  <img alt="FastAPI" src="https://img.shields.io/badge/FastAPI-0.115-009688?logo=fastapi&logoColor=white" />
  <img alt="React" src="https://img.shields.io/badge/React-18-61DAFB?logo=react&logoColor=black" />
  <img alt="MySQL" src="https://img.shields.io/badge/MySQL-8.4-4479A1?logo=mysql&logoColor=white" />
</p>

---

## Contents

- [Why I built this](#why-i-built-this)
- [Features](#features)
- [The adaptive algorithm](#the-adaptive-algorithm)
- [Architecture](#architecture)
- [Tech stack](#tech-stack)
- [Project structure](#project-structure)
- [Getting started](#getting-started)
- [API reference](#api-reference)
- [Data model](#data-model)
- [Testing & CI](#testing--ci)
- [Engineering notes](#engineering-notes)
- [Roadmap](#roadmap)

---

## Why I built this

Commercial GRE apps either drill a fixed list in order or hide their adaptivity
behind a paywall. I wanted a study tool that behaves like a patient tutor —
meeting me exactly at my current level in each question type, explaining my
mistakes in my native language, and never wasting my time on questions I've
already mastered. Building it end to end (database, API, and UI) was also a way
to practice the kind of full-stack engineering I want to do in graduate school.

The bundled content is original and substantial: **490 verbal and quantitative
questions** across five difficulty levels, a **342-word GRE vocabulary Word
Test** spanning ten levels, and six Analytical Writing prompts with model
answers — every item independently re-solved and adversarially verified, with
Korean translations and explanations throughout.

## Features

- **Adaptive difficulty.** Each section tracks its own level; it rises on a
  correct answer and falls on an incorrect one. Verbal and math climb levels
  **1–5**; the vocabulary Word Test climbs **1–10**.
- **Korean explanations on every miss.** When you answer incorrectly, the worked
  solution is shown in Korean (해설) before you move on.
- **Mastery-based retirement.** A question answered correctly is never served
  again; missed questions stay in rotation until you get them.
- **Five practice modes across three adaptive sections + writing.**
  - *Verbal — Sentence Equivalence & Text Completion* (single- and two-answer)
  - *Verbal — Reading Comprehension & Critical Reasoning* (passage-based)
  - *Math — Quantitative Reasoning* (problem-solving and quantitative comparison)
  - *Vocabulary — Word Test* — pick the nearest synonym; difficulty ranges from
    common words (level 1) to rare, esoteric words (level 10).
  - *Analytical Writing* — timed Issue/Argument essays with model answers and a
    0–6 self-grading rubric.
- **Per-question timer** that warns when you exceed the target pace.
- **Progress dashboard** showing each section's level and solved/total counts.

## The adaptive algorithm

The heart of the app is a small, well-tested selection-and-leveling policy
([`backend/app/services/adaptive.py`](backend/app/services/adaptive.py)).

**Selecting the next question.** For a given section the server looks at the
learner's current level and serves a random *unsolved* question from it. If that
level is exhausted, it falls back to the **nearest** level that still has
unsolved questions (preferring the lower one on a tie), so practice never stalls
until the entire section is mastered.

```
level_sequence(current=3)  ->  [3, 2, 4, 1, 5]   # by distance, lower wins ties
```

**Updating the level.** Submissions are graded order-independently (important
for two-answer Sentence Equivalence), the attempt is recorded with its elapsed
time, and the level moves within that section's bounds:

```
correct   ->  level = min(max_level, level + 1)
incorrect ->  level = max(min_level, level - 1)
```

The engine is parameterized by **per-section level bounds** — `(1, 5)` for
verbal and math, `(1, 10)` for the vocabulary Word Test — so one code path
serves both ladders. The bounds live in
[`config.py`](backend/app/config.py).

**Retirement.** "Solved" is derived state, not a flag: a question is excluded
once it has *any* correct attempt, computed with a `NOT IN (SELECT question_id
FROM attempts WHERE correct)` subquery. This keeps the read model honest even if
attempts are added out of band.

## Architecture

```mermaid
flowchart LR
    subgraph Client["React SPA (Vite)"]
        UI["Dashboard · Quiz · Writing"]
        Timer["Timer + Level meter"]
    end
    subgraph Server["FastAPI"]
        R["Routers<br/>questions · answers · progress · writing"]
        S["Adaptive service<br/>select · grade · level"]
    end
    DB[("MySQL<br/>questions · attempts<br/>progress · essays")]
    Seed["Seed JSON<br/>(validated)"]

    UI -->|"/api (fetch)"| R
    R --> S
    S --> DB
    Seed -->|"python -m app.seed.seed"| DB
```

The frontend is a single-page app that talks to the backend exclusively over a
small JSON API under `/api` (proxied by Vite in development). The backend keeps
HTTP concerns in thin routers and all the study logic in a service layer, so the
rules can be unit-tested without a web server or a database server.

## Tech stack

| Layer    | Choice                          | Notes                                            |
| -------- | ------------------------------- | ------------------------------------------------ |
| Frontend | React 18 + Vite, React Router   | SPA, fetch-based API client, no UI framework     |
| Backend  | FastAPI, Pydantic v2            | Typed request/response models, auto OpenAPI docs |
| ORM      | SQLAlchemy 2.0 (typed mappings) | `Mapped[...]` models, JSON columns for choices   |
| Database | MySQL 8.4                       | Runs locally via Docker Compose                  |
| Tooling  | pytest, GitHub Actions          | Logic + API tests, CI on every push/PR           |

## Project structure

```
gre/
├── backend/
│   ├── app/
│   │   ├── main.py              # app entry, CORS, router registration
│   │   ├── config.py            # env-driven settings + per-section level bounds
│   │   ├── database.py          # SQLAlchemy engine/session + Base
│   │   ├── models.py            # ORM models
│   │   ├── schemas.py           # Pydantic schemas (answer key hidden)
│   │   ├── routers/             # questions · answers · progress · writing
│   │   ├── services/adaptive.py # selection + leveling policy
│   │   └── seed/                # JSON question bank + validate/seed scripts
│   ├── tests/                   # pytest suite (SQLite, no server needed)
│   └── requirements*.txt
├── frontend/
│   └── src/
│       ├── pages/               # Home · Quiz · Writing
│       ├── components/          # Timer · LevelMeter · StateMessage
│       ├── hooks/useTimer.js
│       └── api.js               # API client
├── .github/workflows/ci.yml
└── docker-compose.yml           # local MySQL
```

## Getting started

**Prerequisites:** Python 3.13+, Node.js 20+, and Docker (for MySQL).

### 1. Start the database

```bash
docker compose up -d
```

### 2. Run the backend

```bash
cd backend
python -m venv .venv && source .venv/bin/activate
pip install -r requirements-dev.txt
python -m app.seed.seed          # load the question bank, Word Test, and prompts
uvicorn app.main:app --reload    # http://localhost:8000  (docs at /docs)
```

### 3. Run the frontend

```bash
cd frontend
npm install
npm run dev                      # http://localhost:5173
```

Open <http://localhost:5173> and start studying. The backend connection string
can be overridden with the `GRE_DATABASE_URL` environment variable.

## API reference

All endpoints are namespaced under `/api`; interactive documentation is
generated automatically at `/docs`.

| Method | Path                          | Purpose                                                    |
| ------ | ----------------------------- | ---------------------------------------------------------- |
| `GET`  | `/questions/next?subgroup=`   | Next unsolved question at the current (or nearest) level; reports `max_level` |
| `POST` | `/answers`                    | Grade a submission; returns correctness, Korean explanation, and the new level |
| `GET`  | `/progress`                   | Per-section level (with its ceiling) and solved/total counts |
| `GET`  | `/writing/prompts`            | List essay prompts with how many essays were written       |
| `GET`  | `/writing/prompts/{id}`       | A prompt including its model answer                         |
| `POST` | `/writing/essays`             | Save an essay with a 0–6 self-grade                         |
| `GET`  | `/writing/essays`             | Essay history (optionally filtered by prompt)              |

Valid `subgroup` values: `se_tc`, `reading_reasoning`, `quant`, `vocabulary`.
`GET /questions/next` deliberately omits the answer key and explanation from its
response so the client cannot reveal the answer before the learner submits.

## Data model

| Table             | Key columns                                                              |
| ----------------- | ----------------------------------------------------------------------- |
| `questions`       | group, subgroup, level, question_type, select_count, passage, choices (JSON), answer (JSON), explanation_ko |
| `attempts`        | question_id, selected (JSON), correct, elapsed_seconds, created_at      |
| `progress`        | subgroup (PK), current_level                                            |
| `writing_prompts` | task_type, prompt_text, model_answer, suggested_minutes                 |
| `essays`          | prompt_id, essay_text, self_grade, elapsed_seconds, created_at          |

The content bank ships as JSON under `backend/app/seed/data/`, organized by
section and level, so it can grow without code changes. Every file is validated
(answer indices in range, `select_count` consistency, level within the section's
bounds, Korean explanations present) before it can be seeded or merged.

## Testing & CI

```bash
cd backend
python -m pytest                 # unit + API tests
python -m app.seed.validate      # validate the content bank
```

The test suite runs against in-memory SQLite via a FastAPI dependency override,
so the full API and the adaptive logic are exercised without a running server or
MySQL. [GitHub Actions](.github/workflows/ci.yml) runs the backend tests (with
seed-data validation) and the production frontend build on every push and pull
request.

## Engineering notes

A few decisions worth calling out:

- **Logic isolated from transport.** The leveling and selection rules live in a
  service module with no FastAPI or HTTP types, which is what makes them cheap to
  unit-test and easy to reason about.
- **One engine, two ladders.** Rather than special-casing vocabulary, the
  difficulty range is a parameter, so the 1–5 and 1–10 sections share a single
  tested code path.
- **Answer keys never leave the server early.** The next-question schema simply
  has no field for the answer or explanation; they are only returned *after* a
  submission. The grader also bounds-checks selected indices.
- **Derived mastery over mutable flags.** Whether a question is "solved" is
  computed from the attempts table rather than stored, avoiding a class of
  state-drift bugs.
- **Validated, data-driven content.** Questions are data, not code; a schema
  validator gates them so a malformed item fails fast in CI instead of at
  runtime.

## Roadmap

- Spaced-repetition scheduling for missed questions
- Section-level analytics (accuracy and pace over time)
- Optional accounts so multiple learners can keep separate progress
- LLM-assisted scoring for written essays

---

<sub>Built by Jun Heo as a full-stack engineering project. All question content
is original and intended for study practice.</sub>
