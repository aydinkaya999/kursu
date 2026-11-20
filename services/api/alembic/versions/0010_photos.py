"""Add private photo solutions and extend content reports to private submissions."""

from alembic import op

revision = "0010_photos"
down_revision = "0009_commerce"
branch_labels = depends_on = None


def upgrade() -> None:
    op.execute("""
        CREATE TABLE photo_solutions (
            id uuid PRIMARY KEY, user_id uuid NOT NULL REFERENCES users ON DELETE CASCADE,
            request_id uuid NOT NULL, result jsonb NOT NULL,
            expires_at timestamptz NOT NULL,
            CONSTRAINT uq_photo_request UNIQUE(user_id,request_id))
    """)
    op.create_index("ix_photo_solutions_expires_at", "photo_solutions", ["expires_at"])
    op.execute("""
        ALTER TABLE content_reports
            DROP CONSTRAINT content_reports_pkey,
            ADD COLUMN id uuid NOT NULL DEFAULT gen_random_uuid() PRIMARY KEY,
            ADD COLUMN photo_solution_id uuid REFERENCES photo_solutions ON DELETE CASCADE
    """)
    op.execute("""
        ALTER TABLE content_reports
            ALTER COLUMN question_id DROP NOT NULL,
            ADD CONSTRAINT uq_report_question UNIQUE(user_id,question_id),
            ADD CONSTRAINT uq_report_photo UNIQUE(user_id,photo_solution_id),
            ADD CONSTRAINT ck_report_target
                CHECK (num_nonnulls(question_id,photo_solution_id)=1)
    """)


def downgrade() -> None:
    op.execute("DELETE FROM content_reports WHERE photo_solution_id IS NOT NULL")
    op.execute("""
        ALTER TABLE content_reports DROP CONSTRAINT uq_report_question,
            DROP COLUMN photo_solution_id, DROP COLUMN id,
            ADD PRIMARY KEY(user_id,question_id)
    """)
    op.drop_table("photo_solutions")
