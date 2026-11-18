"""Create the reference and content catalogue"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0002_content"
down_revision: str | Sequence[str] | None = "0001_baseline"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "fields",
        sa.Column("id", sa.Text(), nullable=False),
        sa.Column("name", sa.Text(), nullable=False),
        sa.Column("score_type", sa.Text(), nullable=False),
        sa.CheckConstraint("score_type IN ('P1', 'P2', 'P3')", name="ck_fields_score_type"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_table(
        "mock_exams",
        sa.Column("id", sa.Text(), nullable=False),
        sa.Column("title", sa.Text(), nullable=False),
        sa.Column(
            "status",
            sa.Enum(
                "draft",
                "prerelease",
                "published",
                "quarantined",
                "retired",
                name="content_status",
                native_enum=False,
                create_constraint=True,
            ),
            nullable=False,
        ),
        sa.Column("published_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "is_placeholder", sa.Boolean(), server_default=sa.text("false"), nullable=False
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_table(
        "remote_config",
        sa.Column("key", sa.Text(), nullable=False),
        sa.Column("value", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.PrimaryKeyConstraint("key"),
    )
    op.create_table(
        "subtests",
        sa.Column("id", sa.Text(), nullable=False),
        sa.Column("name", sa.Text(), nullable=False),
        sa.Column("short_name", sa.Text(), nullable=False),
        sa.Column("question_count", sa.Integer(), nullable=False),
        sa.Column("exam_order", sa.Integer(), nullable=False),
        sa.Column("weight_p1", sa.Integer(), nullable=False),
        sa.CheckConstraint(
            "exam_order > 0 AND question_count > 0 AND weight_p1 BETWEEN 0 AND 100",
            name="ck_subtests_exam_facts",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("exam_order", deferrable=True, initially="DEFERRED"),
    )
    op.create_table(
        "topics",
        sa.Column("id", sa.Text(), nullable=False),
        sa.Column("subtest_id", sa.Text(), nullable=False),
        sa.Column("name", sa.Text(), nullable=False),
        sa.Column("exam_weight", sa.Float(), nullable=True),
        sa.Column(
            "is_placeholder", sa.Boolean(), server_default=sa.text("false"), nullable=False
        ),
        sa.CheckConstraint("exam_weight >= 0", name="ck_topics_exam_weight"),
        sa.ForeignKeyConstraint(
            ["subtest_id"],
            ["subtests.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("id", "subtest_id"),
    )
    op.create_index(op.f("ix_topics_subtest_id"), "topics", ["subtest_id"], unique=False)
    op.create_table(
        "lessons",
        sa.Column("id", sa.Text(), nullable=False),
        sa.Column("topic_id", sa.Text(), nullable=False),
        sa.Column("title", sa.Text(), nullable=False),
        sa.Column("minutes", sa.Integer(), nullable=False),
        sa.Column("source", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column(
            "status",
            sa.Enum(
                "draft",
                "prerelease",
                "published",
                "quarantined",
                "retired",
                name="content_status",
                native_enum=False,
                create_constraint=True,
            ),
            nullable=False,
        ),
        sa.Column(
            "is_placeholder", sa.Boolean(), server_default=sa.text("false"), nullable=False
        ),
        sa.CheckConstraint("minutes BETWEEN 3 AND 5", name="ck_lessons_minutes"),
        sa.ForeignKeyConstraint(
            ["topic_id"],
            ["topics.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_lessons_source", "lessons", ["source"], unique=False, postgresql_using="gin"
    )
    op.create_index(op.f("ix_lessons_topic_id"), "lessons", ["topic_id"], unique=False)
    op.create_table(
        "misconceptions",
        sa.Column("id", sa.Text(), nullable=False),
        sa.Column("topic_id", sa.Text(), nullable=False),
        sa.Column("text", sa.Text(), nullable=False),
        sa.Column(
            "is_placeholder", sa.Boolean(), server_default=sa.text("false"), nullable=False
        ),
        sa.ForeignKeyConstraint(
            ["topic_id"],
            ["topics.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_table(
        "objectives",
        sa.Column("id", sa.Text(), nullable=False),
        sa.Column("topic_id", sa.Text(), nullable=False),
        sa.Column("text", sa.Text(), nullable=False),
        sa.Column(
            "is_placeholder", sa.Boolean(), server_default=sa.text("false"), nullable=False
        ),
        sa.ForeignKeyConstraint(
            ["topic_id"],
            ["topics.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("id", "topic_id"),
    )
    op.create_table(
        "lesson_cards",
        sa.Column("lesson_id", sa.Text(), nullable=False),
        sa.Column("position", sa.Integer(), nullable=False),
        sa.Column("kind", sa.Text(), nullable=False),
        sa.Column("title", sa.Text(), nullable=False),
        sa.Column("blocks", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("tip", sa.Text(), nullable=True),
        sa.CheckConstraint(
            "kind IN ('definition', 'example', 'confused', 'exam')",
            name="ck_lesson_cards_kind",
        ),
        sa.CheckConstraint("position BETWEEN 1 AND 6", name="ck_lesson_cards_position"),
        sa.ForeignKeyConstraint(
            ["lesson_id"],
            ["lessons.id"],
        ),
        sa.PrimaryKeyConstraint("lesson_id", "position"),
    )
    op.create_table(
        "questions",
        sa.Column("id", sa.Text(), nullable=False),
        sa.Column("subtest_id", sa.Text(), nullable=False),
        sa.Column("topic_id", sa.Text(), nullable=False),
        sa.Column("objective_id", sa.Text(), nullable=False),
        sa.Column("difficulty", sa.Integer(), nullable=False),
        sa.Column("stem", sa.Text(), nullable=False),
        sa.Column("options", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("correct_option", sa.Text(), nullable=False),
        sa.Column("rationales", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column(
            "solution_steps", postgresql.JSONB(astext_type=sa.Text()), nullable=False
        ),
        sa.Column("source", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("related_lesson_id", sa.Text(), nullable=True),
        sa.Column(
            "status",
            sa.Enum(
                "draft",
                "prerelease",
                "published",
                "quarantined",
                "retired",
                name="content_status",
                native_enum=False,
                create_constraint=True,
            ),
            nullable=False,
        ),
        sa.Column(
            "is_placeholder", sa.Boolean(), server_default=sa.text("false"), nullable=False
        ),
        sa.CheckConstraint(
            "NOT is_placeholder OR starts_with(stem, '[ÖRNEK]')",
            name="ck_questions_placeholder_stem",
        ),
        sa.CheckConstraint(
            "correct_option IN ('A', 'B', 'C', 'D', 'E')",
            name="ck_questions_correct_option",
        ),
        sa.CheckConstraint("difficulty BETWEEN 1 AND 3", name="ck_questions_difficulty"),
        sa.ForeignKeyConstraint(
            ["objective_id", "topic_id"],
            ["objectives.id", "objectives.topic_id"],
            initially="DEFERRED",
            deferrable=True,
        ),
        sa.ForeignKeyConstraint(
            ["related_lesson_id"],
            ["lessons.id"],
        ),
        sa.ForeignKeyConstraint(
            ["topic_id", "subtest_id"],
            ["topics.id", "topics.subtest_id"],
            initially="DEFERRED",
            deferrable=True,
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_questions_objective_id"), "questions", ["objective_id"], unique=False
    )
    op.create_index(
        "ix_questions_source", "questions", ["source"], unique=False, postgresql_using="gin"
    )
    op.create_index(
        "ix_questions_subtest_difficulty",
        "questions",
        ["subtest_id", "difficulty", "status"],
        unique=False,
    )
    op.create_table(
        "lesson_check_questions",
        sa.Column("lesson_id", sa.Text(), nullable=False),
        sa.Column("position", sa.Integer(), nullable=False),
        sa.Column("question_id", sa.Text(), nullable=False),
        sa.Column("card_position", sa.Integer(), nullable=False),
        sa.CheckConstraint("position BETWEEN 1 AND 2", name="ck_lesson_checks_position"),
        sa.ForeignKeyConstraint(
            ["lesson_id", "card_position"],
            ["lesson_cards.lesson_id", "lesson_cards.position"],
            initially="DEFERRED",
            deferrable=True,
        ),
        sa.ForeignKeyConstraint(
            ["question_id"],
            ["questions.id"],
        ),
        sa.PrimaryKeyConstraint("lesson_id", "position"),
        sa.UniqueConstraint(
            "lesson_id", "question_id", deferrable=True, initially="DEFERRED"
        ),
    )
    op.create_table(
        "mock_exam_questions",
        sa.Column("mock_exam_id", sa.Text(), nullable=False),
        sa.Column("position", sa.Integer(), nullable=False),
        sa.Column("question_id", sa.Text(), nullable=False),
        sa.CheckConstraint("position BETWEEN 1 AND 80", name="ck_mock_questions_position"),
        sa.ForeignKeyConstraint(
            ["mock_exam_id"],
            ["mock_exams.id"],
        ),
        sa.ForeignKeyConstraint(
            ["question_id"],
            ["questions.id"],
        ),
        sa.PrimaryKeyConstraint("mock_exam_id", "position"),
        sa.UniqueConstraint(
            "mock_exam_id", "question_id", deferrable=True, initially="DEFERRED"
        ),
    )
    op.create_index(
        op.f("ix_mock_exam_questions_question_id"),
        "mock_exam_questions",
        ["question_id"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(
        op.f("ix_mock_exam_questions_question_id"), table_name="mock_exam_questions"
    )
    op.drop_table("mock_exam_questions")
    op.drop_table("lesson_check_questions")
    op.drop_index("ix_questions_subtest_difficulty", table_name="questions")
    op.drop_index("ix_questions_source", table_name="questions", postgresql_using="gin")
    op.drop_index(op.f("ix_questions_objective_id"), table_name="questions")
    op.drop_table("questions")
    op.drop_table("lesson_cards")
    op.drop_table("objectives")
    op.drop_table("misconceptions")
    op.drop_index(op.f("ix_lessons_topic_id"), table_name="lessons")
    op.drop_index("ix_lessons_source", table_name="lessons", postgresql_using="gin")
    op.drop_table("lessons")
    op.drop_index(op.f("ix_topics_subtest_id"), table_name="topics")
    op.drop_table("topics")
    op.drop_table("subtests")
    op.drop_table("remote_config")
    op.drop_table("mock_exams")
    op.drop_table("fields")
