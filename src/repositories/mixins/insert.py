from typing import Generic

from sqlalchemy import insert
from sqlalchemy.sql import Insert

from repositories.exceptions import RepositoryError
from repositories.mixins.core import RepositoryCore
from repositories.types import T_ID, T_INSERT, T


class InsertMixin(RepositoryCore[T, T_ID], Generic[T, T_ID, T_INSERT]):
    """Insert operations and their SQL query builders."""

    async def insert(
        self,
        data: T_INSERT,
    ) -> T:
        """Create a record and return it in the get schema."""
        values = self._object_to_dict(data)
        query = self.insert_query().values(**values).returning(self.model)

        async with self.session_factory.context_session() as active_session:
            result = await active_session.scalar(query)

        if result is None:
            raise RepositoryError(
                "INSERT ... RETURNING did not return the created row",
            )

        return self._parse_object(result)

    def insert_query(self) -> Insert:
        return insert(self.model)
