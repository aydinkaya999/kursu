"""accounts"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0004_accounts"
down_revision: str | Sequence[str] | None = "0003_placement"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.drop_constraint("ck_placement_state", "placement_attempts", type_="check")
    op.create_check_constraint(
        "ck_placement_state",
        "placement_attempts",
        "state IN ('active','completed','paused')",
    )

    op.create_table(
        "email_codes",
        sa.Column("email", sa.Text(), nullable=False),
        sa.Column("user_id", sa.Uuid(), nullable=False),
        sa.Column("code_hash", sa.Text(), nullable=False),
        sa.Column("attempts", sa.Integer(), nullable=False),
        sa.Column("sent_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("email", "user_id"),
    )
    op.create_table(
        "identities",
        sa.Column("provider", sa.Text(), nullable=False),
        sa.Column("subject", sa.Text(), nullable=False),
        sa.Column("user_id", sa.Uuid(), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("provider", "subject"),
    )
    op.create_index(op.f("ix_identities_user_id"), "identities", ["user_id"], unique=False)
    op.create_table(
        "provider_challenges",
        sa.Column("state", sa.Text(), nullable=False),
        sa.Column("provider", sa.Text(), nullable=False),
        sa.Column("user_id", sa.Uuid(), nullable=False),
        sa.Column("platform", sa.Text(), nullable=False),
        sa.Column("nonce", sa.Text(), nullable=False),
        sa.Column("pkce_verifier", sa.Text(), nullable=False),
        sa.Column("subject", sa.Text(), nullable=True),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("state"),
    )
    op.create_index(
        op.f("ix_provider_challenges_user_id"),
        "provider_challenges",
        ["user_id"],
        unique=False,
    )
    op.add_column("profiles", sa.Column("notification_time", sa.Time(), nullable=True))
    op.add_column(
        "refresh_tokens",
        sa.Column(
            "family_id",
            sa.Uuid(),
            server_default=sa.text("gen_random_uuid()"),
            nullable=False,
        ),
    )
    op.create_index(
        op.f("ix_refresh_tokens_family_id"), "refresh_tokens", ["family_id"], unique=False
    )
    op.add_column(
        "users",
        sa.Column("legacy_access", sa.Boolean(), server_default="true", nullable=False),
    )


def downgrade() -> None:
    op.drop_constraint("ck_placement_state", "placement_attempts", type_="check")
    op.create_check_constraint(
        "ck_placement_state", "placement_attempts", "state IN ('active','completed')"
    )

    op.drop_column("users", "legacy_access")
    op.drop_index(op.f("ix_refresh_tokens_family_id"), table_name="refresh_tokens")
    op.drop_column("refresh_tokens", "family_id")
    op.drop_column("profiles", "notification_time")
    op.drop_index(op.f("ix_provider_challenges_user_id"), table_name="provider_challenges")
    op.drop_table("provider_challenges")
    op.drop_index(op.f("ix_identities_user_id"), table_name="identities")
    op.drop_table("identities")
    op.drop_table("email_codes")
