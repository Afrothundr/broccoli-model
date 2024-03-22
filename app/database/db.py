import datetime
import databases
import ormar
import sqlalchemy

from app.database.config import settings

database = databases.Database(settings.db_url)
metadata = sqlalchemy.MetaData()


class BaseMeta(ormar.ModelMeta):
    metadata = metadata
    database = database


class Receipt(ormar.Model):
    class Meta(BaseMeta):
        tablename = "receipts"

    id: int = ormar.Integer(primary_key=True)
    text: str = ormar.Text(unique=True)
    created_at: datetime.datetime = ormar.DateTime(
       default=datetime.datetime.now
    )


engine = sqlalchemy.create_engine(settings.db_url)
metadata.create_all(engine)