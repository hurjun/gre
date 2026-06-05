"""Pydantic schemas for the public API.

`QuestionOut` deliberately omits `answer` and `explanation_ko` so the client
never sees the answer key before submitting.
"""

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from .models import Subgroup, TaskType


class QuestionOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    group: str
    subgroup: str
    level: int
    question_type: str
    select_count: int
    passage: str | None
    question_text: str
    choices: list[str]


class NextQuestionOut(BaseModel):
    question: QuestionOut | None
    current_level: int
    max_level: int
    remaining_at_level: int
    exhausted: bool


class AnswerIn(BaseModel):
    question_id: int
    selected: list[int] = Field(min_length=1)
    elapsed_seconds: int = Field(default=0, ge=0)


class AnswerOut(BaseModel):
    correct: bool
    correct_answer: list[int]
    explanation_ko: str
    previous_level: int
    new_level: int


class SubgroupProgressOut(BaseModel):
    subgroup: Subgroup
    current_level: int
    max_level: int
    solved: int
    total: int


class ProgressOut(BaseModel):
    subgroups: list[SubgroupProgressOut]


class WritingPromptSummary(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    task_type: TaskType
    prompt_text: str
    suggested_minutes: int
    essay_count: int = 0


class WritingPromptOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    task_type: TaskType
    prompt_text: str
    model_answer: str
    suggested_minutes: int


class EssayIn(BaseModel):
    prompt_id: int
    essay_text: str = Field(min_length=1)
    self_grade: float = Field(ge=0, le=6)
    elapsed_seconds: int = Field(default=0, ge=0)


class EssayOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    prompt_id: int
    essay_text: str
    self_grade: float
    elapsed_seconds: int
    created_at: datetime
