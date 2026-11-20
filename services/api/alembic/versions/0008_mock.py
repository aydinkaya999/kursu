"""Persist mock attempts, immutable question versions and submitted learning evidence."""

from alembic import op

revision = "0008_mock"
down_revision = "0007_notebook"
branch_labels = depends_on = None


def upgrade() -> None:
    op.execute("""
        CREATE TABLE mock_attempts (
            id uuid PRIMARY KEY, user_id uuid NOT NULL REFERENCES users ON DELETE CASCADE,
            mock_exam_id text NOT NULL REFERENCES mock_exams, title text NOT NULL,
            mode text NOT NULL, position integer NOT NULL, started_at timestamptz NOT NULL,
            deadline_at timestamptz, submitted_at timestamptz, result jsonb,
            CONSTRAINT ck_mock_mode CHECK (mode IN ('timed','practice'))
        )
    """)
    op.create_index("ix_mock_attempts_user_id", "mock_attempts", ["user_id"])
    op.create_index("ix_mock_expiry", "mock_attempts", ["submitted_at", "deadline_at"])
    op.execute("""
        CREATE TABLE mock_answers (
            attempt_id uuid REFERENCES mock_attempts ON DELETE CASCADE, position integer,
            question_id text NOT NULL REFERENCES questions, snapshot jsonb NOT NULL,
            selected_option text, flagged boolean NOT NULL DEFAULT false,
            updated_at timestamptz, PRIMARY KEY(attempt_id, position),
            CONSTRAINT uq_mock_question UNIQUE (attempt_id, question_id),
            CONSTRAINT ck_mock_answer CHECK (selected_option IN ('A','B','C','D','E'))
        )
    """)
    op.execute(
        "ALTER TABLE answers ADD COLUMN mock_id uuid REFERENCES mock_attempts "
        "ON DELETE CASCADE"
    )
    op.create_unique_constraint(
        "uq_graded_mock_position", "answers", ["mock_id", "position"]
    )
    op.drop_constraint("ck_answer_session", "answers")
    op.create_check_constraint(
        "ck_answer_session", "answers", "num_nonnulls(placement_id,practice_id,mock_id) = 1"
    )


def downgrade() -> None:
    op.drop_constraint("ck_answer_session", "answers")
    op.drop_constraint("uq_graded_mock_position", "answers")
    op.execute("DELETE FROM answers WHERE mock_id IS NOT NULL")
    op.drop_column("answers", "mock_id")
    op.create_check_constraint(
        "ck_answer_session", "answers", "num_nonnulls(placement_id, practice_id) = 1"
    )
    op.drop_table("mock_answers")
    op.drop_table("mock_attempts")
