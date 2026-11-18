"""Guest profiles and placement attempts"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0003_placement"
down_revision: str | Sequence[str] | None = "0002_content"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "users",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("is_guest", sa.Boolean(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_table(
        "profiles",
        sa.Column("user_id", sa.Uuid(), nullable=False),
        sa.Column("field_id", sa.Text(), nullable=False),
        sa.Column("score_type", sa.Text(), nullable=False),
        sa.Column("daily_minutes", sa.Integer(), nullable=False),
        sa.Column("attempt_kind", sa.Text(), nullable=False),
        sa.CheckConstraint(
            "attempt_kind IN ('first','repeat')", name="ck_profiles_attempt"
        ),
        sa.CheckConstraint("score_type IN ('P1','P2','P3')", name="ck_profiles_score"),
        sa.CheckConstraint("daily_minutes IN (30,60,90)", name="ck_profiles_minutes"),
        sa.ForeignKeyConstraint(
            ["field_id"],
            ["fields.id"],
        ),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["users.id"],
        ),
        sa.PrimaryKeyConstraint("user_id"),
    )
    op.create_table(
        "refresh_tokens",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("user_id", sa.Uuid(), nullable=False),
        sa.Column("token_hash", sa.Text(), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("revoked_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["users.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("token_hash"),
    )
    op.create_index(
        op.f("ix_refresh_tokens_user_id"), "refresh_tokens", ["user_id"], unique=False
    )
    op.create_table(
        "placement_attempts",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("user_id", sa.Uuid(), nullable=False),
        sa.Column("kind", sa.Text(), nullable=False),
        sa.Column("state", sa.Text(), nullable=False),
        sa.Column("position", sa.Integer(), nullable=False),
        sa.Column("levels", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("current_question_id", sa.Text(), nullable=True),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "result",
            postgresql.JSONB(none_as_null=True, astext_type=sa.Text()),
            nullable=True,
        ),
        sa.CheckConstraint("kind IN ('full','short')", name="ck_placement_kind"),
        sa.CheckConstraint("state IN ('active','completed')", name="ck_placement_state"),
        sa.ForeignKeyConstraint(
            ["current_question_id"],
            ["questions.id"],
        ),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["users.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_placement_attempts_user_id"),
        "placement_attempts",
        ["user_id"],
        unique=False,
    )
    op.create_index(
        "uq_active_placement_user",
        "placement_attempts",
        ["user_id"],
        unique=True,
        postgresql_where=sa.text("state = 'active'"),
    )
    op.create_table(
        "answers",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("user_id", sa.Uuid(), nullable=False),
        sa.Column("placement_id", sa.Uuid(), nullable=False),
        sa.Column("position", sa.Integer(), nullable=False),
        sa.Column("question_id", sa.Text(), nullable=False),
        sa.Column("subtest_id", sa.Text(), nullable=False),
        sa.Column("topic_id", sa.Text(), nullable=False),
        sa.Column("selected_option", sa.Text(), nullable=True),
        sa.Column("is_correct", sa.Boolean(), nullable=True),
        sa.Column("not_sure", sa.Boolean(), nullable=False),
        sa.Column("client_answer_id", sa.Uuid(), nullable=False),
        sa.Column("answered_at", sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint(
            "selected_option IN ('A','B','C','D','E')", name="ck_answer_option"
        ),
        sa.ForeignKeyConstraint(
            ["placement_id"],
            ["placement_attempts.id"],
        ),
        sa.ForeignKeyConstraint(
            ["question_id"],
            ["questions.id"],
        ),
        sa.ForeignKeyConstraint(
            ["subtest_id"],
            ["subtests.id"],
        ),
        sa.ForeignKeyConstraint(
            ["topic_id"],
            ["topics.id"],
        ),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["users.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("placement_id", "position"),
        sa.UniqueConstraint("placement_id", "question_id"),
        sa.UniqueConstraint("user_id", "client_answer_id"),
    )
    op.create_index(op.f("ix_answers_user_id"), "answers", ["user_id"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_answers_user_id"), table_name="answers")
    op.drop_table("answers")
    op.drop_index(
        "uq_active_placement_user",
        table_name="placement_attempts",
        postgresql_where=sa.text("state = 'active'"),
    )
    op.drop_index(op.f("ix_placement_attempts_user_id"), table_name="placement_attempts")
    op.drop_table("placement_attempts")
    op.drop_index(op.f("ix_refresh_tokens_user_id"), table_name="refresh_tokens")
    op.drop_table("refresh_tokens")
    op.drop_table("profiles")
    op.drop_table("users")
