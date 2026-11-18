from alembic import context
from sqlalchemy import create_engine, pool

from app.core.settings import Settings
from app.modules.content.models import metadata

database_url = Settings().database_url

if context.is_offline_mode():
    context.configure(url=database_url, target_metadata=metadata, literal_binds=True)
    with context.begin_transaction():
        context.run_migrations()
else:
    engine = create_engine(database_url, poolclass=pool.NullPool)
    with engine.connect() as connection:
        context.configure(connection=connection, target_metadata=metadata)
        with context.begin_transaction():
            context.run_migrations()
    engine.dispose()
