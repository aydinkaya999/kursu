"""practice"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0006_practice"
down_revision: str | Sequence[str] | None = "0005_daily_plan"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "mastery",
        sa.Column("user_id", sa.Uuid(), nullable=False),
        sa.Column("topic_id", sa.Text(), nullable=False),
        sa.Column("value", sa.Float(), nullable=False),
        sa.Column("answers_count", sa.Integer(), nullable=False),
        sa.CheckConstraint(
            "value BETWEEN 0 AND 1 AND answers_count >= 0", name="ck_mastery_value"
        ),
        sa.ForeignKeyConstraint(
            ["topic_id"],
            ["topics.id"],
        ),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("user_id", "topic_id"),
    )
    op.create_table(
        "lesson_completions",
        sa.Column("user_id", sa.Uuid(), nullable=False),
        sa.Column("lesson_id", sa.Text(), nullable=False),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(
            ["lesson_id"],
            ["lessons.id"],
        ),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("user_id", "lesson_id"),
    )
    op.create_table(
        "practice_sessions",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("user_id", sa.Uuid(), nullable=False),
        sa.Column("kind", sa.Text(), nullable=False),
        sa.Column("topic_id", sa.Text(), nullable=False),
        sa.Column("lesson_id", sa.Text(), nullable=True),
        sa.Column("task_id", sa.Uuid(), nullable=True),
        sa.Column("question_ids", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("position", sa.Integer(), nullable=False),
        sa.Column("state", sa.Text(), nullable=False),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.CheckConstraint(
            "(kind = 'lesson_check') = (lesson_id IS NOT NULL)", name="ck_practice_lesson"
        ),
        sa.CheckConstraint(
            "kind IN ('lesson_check','topic_test')", name="ck_practice_kind"
        ),
        sa.CheckConstraint(
            "state IN ('question','feedback','ready','completed')", name="ck_practice_state"
        ),
        sa.CheckConstraint(
            "position >= 1 AND position <= jsonb_array_length(question_ids)",
            name="ck_practice_position",
        ),
        sa.ForeignKeyConstraint(
            ["lesson_id"],
            ["lessons.id"],
        ),
        sa.ForeignKeyConstraint(["task_id"], ["plan_tasks.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(
            ["topic_id"],
            ["topics.id"],
        ),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_practice_sessions_task_id"), "practice_sessions", ["task_id"], unique=False
    )
    op.create_index(
        op.f("ix_practice_sessions_user_id"), "practice_sessions", ["user_id"], unique=False
    )
    op.create_table(
        "content_reports",
        sa.Column("user_id", sa.Uuid(), nullable=False),
        sa.Column("question_id", sa.Text(), nullable=False),
        sa.Column("text", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(
            ["question_id"],
            ["questions.id"],
        ),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("user_id", "question_id"),
    )
    op.create_index(
        op.f("ix_content_reports_question_id"),
        "content_reports",
        ["question_id"],
        unique=False,
    )
    op.add_column("answers", sa.Column("practice_id", sa.Uuid(), nullable=True))
    op.add_column("answers", sa.Column("misconception_id", sa.Text(), nullable=True))
    op.add_column(
        "answers",
        sa.Column(
            "feedback",
            postgresql.JSONB(none_as_null=True, astext_type=sa.Text()),
            nullable=True,
        ),
    )
    op.alter_column("answers", "placement_id", existing_type=sa.UUID(), nullable=True)
    op.create_unique_constraint(
        "uq_practice_question", "answers", ["practice_id", "question_id"]
    )
    op.create_unique_constraint(
        "uq_practice_position", "answers", ["practice_id", "position"]
    )
    op.create_foreign_key(
        "fk_answer_practice",
        "answers",
        "practice_sessions",
        ["practice_id"],
        ["id"],
        ondelete="CASCADE",
    )
    op.create_foreign_key(
        "fk_answer_misconception", "answers", "misconceptions", ["misconception_id"], ["id"]
    )
    op.create_check_constraint(
        "ck_answer_session", "answers", "num_nonnulls(placement_id, practice_id) = 1"
    )
    op.execute("""
        INSERT INTO lesson_completions(user_id, lesson_id, completed_at)
        SELECT p.user_id, l.id, min(t.completed_at) FROM plan_tasks t
        JOIN daily_plans p ON p.id=t.plan_id JOIN lessons l ON l.id=t.ref->>'content_id'
        WHERE t.type='lesson' AND t.state='done' GROUP BY p.user_id, l.id
    """)
    op.execute("""
        UPDATE answers a SET misconception_id=
            q.rationales->a.selected_option->>'misconception_id'
        FROM questions q WHERE q.id=a.question_id AND a.is_correct=false
    """)
    op.execute("""
        DO $$ DECLARE event record; score double precision; BEGIN
        FOR event IN
            SELECT user_id,topic_id,answered_at AS at, is_correct,not_sure,
                   placement_id,position,id FROM answers WHERE is_correct IS NOT NULL
            UNION ALL
            SELECT c.user_id,l.topic_id,c.completed_at,NULL,NULL,NULL,NULL,NULL
            FROM lesson_completions c JOIN lessons l ON l.id=c.lesson_id
            ORDER BY at, placement_id NULLS LAST, position, id
        LOOP
            score := CASE WHEN event.is_correct IS NULL THEN NULL
                          WHEN NOT event.is_correct THEN 0
                          WHEN event.not_sure THEN 0.5 ELSE 1 END;
            INSERT INTO mastery VALUES (event.user_id,event.topic_id,
                                        coalesce(0.2*score,0.3),
                                        (score IS NOT NULL)::int)
            ON CONFLICT (user_id,topic_id) DO UPDATE SET
                value=CASE WHEN score IS NULL THEN greatest(mastery.value,0.3)
                           ELSE mastery.value+0.2*(score-mastery.value) END,
                answers_count=mastery.answers_count+(score IS NOT NULL)::int;
        END LOOP; END $$;
    """)


def downgrade() -> None:
    op.execute("DELETE FROM answers WHERE practice_id IS NOT NULL")
    op.drop_constraint("ck_answer_session", "answers", type_="check")
    op.drop_constraint("fk_answer_misconception", "answers", type_="foreignkey")
    op.drop_constraint("fk_answer_practice", "answers", type_="foreignkey")
    op.drop_constraint("uq_practice_position", "answers", type_="unique")
    op.drop_constraint("uq_practice_question", "answers", type_="unique")
    op.alter_column("answers", "placement_id", existing_type=sa.UUID(), nullable=False)
    op.drop_column("answers", "feedback")
    op.drop_column("answers", "misconception_id")
    op.drop_column("answers", "practice_id")
    op.drop_index(op.f("ix_content_reports_question_id"), table_name="content_reports")
    op.drop_table("content_reports")
    op.drop_index(op.f("ix_practice_sessions_user_id"), table_name="practice_sessions")
    op.drop_index(op.f("ix_practice_sessions_task_id"), table_name="practice_sessions")
    op.drop_table("practice_sessions")
    op.drop_table("lesson_completions")
    op.drop_table("mastery")
