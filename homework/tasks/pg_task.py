from dataclasses import dataclass

import asyncpg


@dataclass
class ItemEntry:
    item_id: int
    user_id: int
    title: str
    description: str


class ItemStorage:
    def __init__(self):
        self._pool: asyncpg.Pool | None = None

    async def connect(self) -> None:
        # We initialize client here, because we need to connect it,
        # __init__ method doesn't support awaits.
        #
        # Pool will be configured using env variables.
        self._pool = await asyncpg.create_pool()

    async def disconnect(self) -> None:
        # Connections should be gracefully closed on app exit to avoid
        # resource leaks.
        await self._pool.close()

    async def create_tables_structure(self) -> None:
        """
        Создайте таблицу items со следующими колонками:
         item_id (int) - обязательное поле, значения должны быть уникальными
         user_id (int) - обязательное поле
         title (str) - обязательное поле
         description (str) - обязательное поле
        """
        # In production environment we will use migration tool
        # like https://github.com/pressly/goose
        await self._pool.execute(
            """
            CREATE TABLE IF NOT EXISTS items (
                item_id SERIAL PRIMARY KEY,
                user_id INT NOT NULL,
                title TEXT NOT NULL,
                description TEXT NOT NULL
            );
            """
        )

    async def save_items(self, items: list[ItemEntry]) -> None:
        """
        Напишите код для вставки записей в таблицу items одним запросом, цикл
        использовать нельзя.
        """
        # Don't use str-formatting, query args should be escaped to avoid
        # sql injections https://habr.com/ru/articles/148151/.

        item_ids = [i.item_id for i in items]
        user_ids = [i.user_id for i in items]
        titles = [i.title for i in items]
        descriptions = [i.description for i in items]

        await self._pool.execute(
            """
            INSERT INTO items (item_id, user_id, title, description)
            SELECT x.item_id, x.user_id, x.title, x.description
            FROM
                UNNEST($1::int[], $2::int[], $3::text[], $4::text[])
                    AS x(item_id, user_id, title, description);
            """,
            item_ids,
            user_ids,
            titles,
            descriptions,
        )


    async def find_similar_items(
        self, user_id: int, title: str, description: str
    ) -> list[ItemEntry]:
        """
        Напишите код для поиска записей, имеющих указанные user_id, title и description.
        """

        data = await self._pool.fetch(
            """
            SELECT item_id, user_id, title, description
            FROM items
            WHERE user_id = $1 AND title = $2 AND description = $3
            """,
            user_id,
            title,
            description,
        )
        return [ItemEntry(**item) for item in data]
