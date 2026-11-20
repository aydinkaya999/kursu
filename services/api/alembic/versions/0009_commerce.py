"""Migrate known study usage and introduce account-scoped pricing and purchases."""

from alembic import op

revision = "0009_commerce"
down_revision = "0008_mock"
branch_labels = depends_on = None


def upgrade() -> None:
    op.execute("""
        CREATE TABLE price_assignments (
            user_id uuid PRIMARY KEY REFERENCES users ON DELETE CASCADE,
            price_group integer NOT NULL, amount integer NOT NULL)
    """)
    op.execute("""
        CREATE TABLE usage_counters (
            user_id uuid REFERENCES users ON DELETE CASCADE, counter text, period text,
            items text[] NOT NULL,
            count integer GENERATED ALWAYS AS (cardinality(items)) STORED,
            PRIMARY KEY(user_id,counter,period))
    """)
    op.execute("""
        CREATE TABLE purchases (
            id uuid PRIMARY KEY, user_id uuid NOT NULL REFERENCES users ON DELETE CASCADE,
            provider text NOT NULL, provider_ref text NOT NULL, amount integer NOT NULL,
            currency text NOT NULL, state text NOT NULL, created_at timestamptz NOT NULL,
            season date NOT NULL,
            CONSTRAINT uq_purchase_receipt UNIQUE(provider,provider_ref),
            CONSTRAINT uq_purchase_season UNIQUE(user_id,season))
    """)
    op.execute("""
        INSERT INTO usage_counters (user_id,counter,period,items)
        SELECT user_id, counter, period, array_agg(DISTINCT item) FROM (
          SELECT user_id, 'mock_exams' AS counter,
            (SELECT value #>> '{}' FROM remote_config WHERE key='exam_date') AS period,
            id::text AS item FROM mock_attempts
          UNION ALL
          SELECT user_id,'lessons_per_day',
            (started_at AT TIME ZONE 'Europe/Istanbul')::date::text, lesson_id
            FROM practice_sessions WHERE lesson_id IS NOT NULL
          UNION ALL
          SELECT user_id,'lessons_per_day',
            (completed_at AT TIME ZONE 'Europe/Istanbul')::date::text, lesson_id
            FROM lesson_completions
          UNION ALL
          SELECT a.user_id,'questions_per_day',
            (a.answered_at AT TIME ZONE 'Europe/Istanbul')::date::text,
            a.practice_id::text || ':' || a.position
            FROM answers a JOIN practice_sessions p ON p.id=a.practice_id
            WHERE p.kind='topic_test'
          UNION ALL
          SELECT p.user_id,'questions_per_day',
            (COALESCE((SELECT max(a.answered_at) FROM answers a WHERE a.practice_id=p.id),
              p.started_at) AT TIME ZONE 'Europe/Istanbul')::date::text,
            p.id::text || ':' || p.position
            FROM practice_sessions p WHERE p.kind='topic_test' AND p.state='question'
        ) events WHERE period IS NOT NULL GROUP BY user_id,counter,period
    """)


def downgrade() -> None:
    op.drop_table("purchases")
    op.drop_table("usage_counters")
    op.drop_table("price_assignments")
