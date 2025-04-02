import datetime
import databases
import ormar
import sqlalchemy

from app.database.config import settings

database = databases.Database(settings.db_url)
metadata = sqlalchemy.MetaData()

base_ormar_config = ormar.OrmarConfig(
    metadata=metadata,
    database=database
)


class Receipt(ormar.Model):
    ormar_config = base_ormar_config.copy(
        tablename="receipts"
    )

    id: int = ormar.Integer(primary_key=True)
    text: str = ormar.Text(unique=True)
    created_at: datetime.datetime = ormar.DateTime(
        default=datetime.datetime.now
    )


engine = sqlalchemy.create_engine(settings.db_url)
metadata.create_all(engine)
