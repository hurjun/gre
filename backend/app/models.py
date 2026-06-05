"""ORM models for questions, attempts, progress, and writing practice."""

import enum
from datetime import datetime

from sqlalchemy import JSON, Boolean, DateTime, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from .database import Base


class Group(str, enum.Enum):
    VERBAL = "verbal"
    MATH = "math"


class Subgroup(str, enum.Enum):
    SE_TC = "se_tc"  # Sentence Equivalence + Text Completion
    READING_REASONING = "reading_reasoning"  # Reading Comprehension + Critical Reasoning
    QUANT = "quant"  # Quantitative Reasoning


class QuestionType(str, enum.Enum):
    SINGLE = "single"  # pick exactly one choice
    MULTI = "multi"  # pick multiple choices (e.g. Sentence Equivalence picks 2)


class TaskType(str, enum.Enum):
    ISSUE = "issue"
    ARGUMENT = "argument"


class Question(Base):
    """A gradable multiple-choice question in the adaptive bank."""

    __tablename__ = "questions"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    group: Mapped[str] = mapped_column(String(16), index=True)
    subgroup: Mapped[str] = mapped_column(String(32), index=True)
    level: Mapped[int] = mapped_column(Integer, index=True)
    question_type: Mapped[str] = mapped_column(String(8))
    select_count: Mapped[int] = mapped_column(Integer, default=1)
    passage: Mapped[str | None] = mapped_column(Text, default=None)
    question_text: Mapped[str] = mapped_column(Text)
    choices: Mapped[list[str]] = mapped_column(JSON)
    answer: Mapped[list[int]] = mapped_column(JSON)  # indices into choices
    explanation_ko: Mapped[str] = mapped_column(Text)


class Attempt(Base):
    """One answer submission. A correct attempt marks the question solved."""

    __tablename__ = "attempts"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    question_id: Mapped[int] = mapped_column(ForeignKey("questions.id"), index=True)
    selected: Mapped[list[int]] = mapped_column(JSON)
    correct: Mapped[bool] = mapped_column(Boolean, index=True)
    elapsed_seconds: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())


class SubgroupProgress(Base):
    """Current adaptive level for one subgroup (single-user app)."""

    __tablename__ = "progress"

    subgroup: Mapped[str] = mapped_column(String(32), primary_key=True)
    current_level: Mapped[int] = mapped_column(Integer, default=1)


class WritingPrompt(Base):
    """An Issue/Argument essay prompt with a model answer for self-grading."""

    __tablename__ = "writing_prompts"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    task_type: Mapped[str] = mapped_column(String(16))
    prompt_text: Mapped[str] = mapped_column(Text)
    model_answer: Mapped[str] = mapped_column(Text)
    suggested_minutes: Mapped[int] = mapped_column(Integer, default=30)


class Essay(Base):
    """A submitted essay with the user's self-assigned score (0-6 scale)."""

    __tablename__ = "essays"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    prompt_id: Mapped[int] = mapped_column(ForeignKey("writing_prompts.id"), index=True)
    essay_text: Mapped[str] = mapped_column(Text)
    self_grade: Mapped[float] = mapped_column(default=0.0)
    elapsed_seconds: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
