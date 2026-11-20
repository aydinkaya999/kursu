from alembic import context
from sqlalchemy import create_engine, pool

from app.core.settings import Settings
from app.modules.accounts import models as accounts  # noqa: F401 (register tables)
from app.modules.commerce import models as commerce  # noqa: F401 (register tables)
from app.modules.content.models import metadata
from app.modules.mocks import models as mocks  # noqa: F401 (register tables)
from app.modules.notebook import models as notebook  # noqa: F401 (register tables)
from app.modules.photos import models as photos  # noqa: F401 (register tables)
from app.modules.placement import models as placement  # noqa: F401 (register tables)
from app.modules.plan import models as plan  # noqa: F401 (register tables)
from app.modules.practice import models as practice  # noqa: F401 (register tables)

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
