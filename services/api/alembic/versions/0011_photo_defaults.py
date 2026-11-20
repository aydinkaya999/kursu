"""Provision the photo policy for already configured installations."""

from alembic import op

revision = "0011_photo_defaults"
down_revision = "0010_photos"
branch_labels = depends_on = None


def upgrade() -> None:
    # Fresh installations import config.json. An existing season may have custom prices
    # and limits, so only supply missing photo keys when upgrading it.
    op.execute("""
        INSERT INTO remote_config (key, value)
        SELECT defaults.key, defaults.value FROM (VALUES
            ('photo_limits', '{"free_total": 3, "pass_daily": 10}'::jsonb),
            ('photo_min_confidence', '0.75'::jsonb),
            ('photo_retention_days', '30'::jsonb)
        ) AS defaults(key,value)
        WHERE EXISTS (SELECT 1 FROM remote_config WHERE key='free_limits')
        ON CONFLICT (key) DO NOTHING
    """)


def downgrade() -> None:
    # Operators may already have customized these keys. Older versions ignore them.
    pass
