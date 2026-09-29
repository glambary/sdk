from sqlalchemy import delete
from sqlalchemy.sql import Delete

from repositories.mixins.core import RepositoryCore
from repositories.types import T_ID, T


class DeleteMixin(RepositoryCore[T, T_ID]):
    """Delete operations and their SQL query builders."""

    async def delete(
        self,
        identifier: T_ID,
    ) -> bool:
        """Delete a record by its primary key; return whether the record existed."""
        query = self.delete_by_id_query(identifier).returning(
            getattr(self.model, self._id_attribute),
        )

        async with self.session_factory.context_session() as active_session:
            result = await active_session.scalar(query)

        return result is not None

    def delete_query(self) -> Delete:
        return delete(self.model)

    def delete_by_id_query(self, identifier: T_ID) -> Delete:
        return self.delete_query().where(self.get_filter_by_id_expression(identifier))
