from typing import Generic

from sqlalchemy import update
from sqlalchemy.sql import Update

from repositories.mixins.get import GetMixin
from repositories.types import T_ID, T_UPDATE, T


class UpdateMixin(GetMixin[T, T_ID], Generic[T, T_ID, T_UPDATE]):
    """Update operations; reading is required to handle an empty patch."""

    async def update(
        self,
        identifier: T_ID,
        data: T_UPDATE,
        *,
        update_fields: set[str] | None = None,
    ) -> T | None:
        """Update explicitly set fields, optionally restricted to update_fields."""
        values = self._object_to_dict(data, include=update_fields, exclude_unset=True)
        if not values:
            return await self.get_or_none_by_id(identifier)

        query = self.update_by_id_query(identifier).values(**values).returning(self.model)

        async with self.session_factory.context_session() as active_session:
            result = await active_session.scalar(query)

        if result is None:
            return None
        return self._parse_object(result)

    def update_query(self) -> Update:
        return update(self.model)

    def update_by_id_query(self, identifier: T_ID) -> Update:
        return self.update_query().where(self.get_filter_by_id_expression(identifier))
