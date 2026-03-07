import asyncpg

from app.database.config import settings


async def fetch_item_types() -> list[dict]:
    conn = await asyncpg.connect(settings.core_db_url)
    try:
        rows = await conn.fetch(
            'SELECT id, name, category, storage_advice, suggested_life_span_seconds FROM "ItemType" ORDER BY name ASC'
        )
        return [dict(row) for row in rows]
    finally:
        await conn.close()
