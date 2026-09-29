from typing import Any

from sqlalchemy import select
from sqlalchemy.sql import Select

from repositories.mixins.core import RepositoryCore
from repositories.types import T_ID, T


class GetMixin(RepositoryCore[T, T_ID]):
    """Read operations and their SQL query builders."""

    async def get_by_id(
        self,
        identifier: T_ID,
        *,
        for_update: bool = False,
    ) -> T:
        """Retrieve a record by its primary key or raise DoesNotExist."""
        result = await self.get_or_none_by_id(identifier, for_update=for_update)
        if result is None:
            raise self.DoesNotExist(f"{self.model.__name__} with {self._id_attribute}={identifier!r} not found")
        return result

    async def get_or_none_by_id(
        self,
        identifier: T_ID,
        *,
        for_update: bool = False,
    ) -> T | None:
        """Retrieve a record by its primary key, or None if absent."""
        query = self.get_by_id_query(identifier, for_update=for_update)

        async with self.session_factory.context_session() as active_session:
            result = await active_session.scalar(query)

        if result is None:
            return None

        return self._parse_object(result)

    async def get_by(
        self,
        field: str,
        value: Any,
        *,
        for_update: bool = False,
    ) -> T:
        """Retrieve a record by an attribute or raise DoesNotExist."""
        result = await self.get_or_none_by(field, value, for_update=for_update)
        if result is None:
            raise self.DoesNotExist(f"{self.model.__name__} with {field}={value!r} not found")
        return result

    async def get_or_none_by(
        self,
        field: str,
        value: Any,
        *,
        for_update: bool = False,
    ) -> T | None:
        """Retrieve a record by an attribute, or None if absent."""
        query = self.select_query(for_update=for_update).where(getattr(self.model, field) == value)

        async with self.session_factory.context_session() as active_session:
            result = await active_session.scalar(query)

        if result is None:
            return None

        return self._parse_object(result)

    async def get_all(
        self,
        *,
        for_update: bool = False,
    ) -> list[T]:
        """Retrieve all records in the get schema."""
        query = self.select_query(for_update=for_update)

        async with self.session_factory.context_session() as active_session:
            result = await active_session.scalars(query)
            models = result.all()

        return [self._parse_object(model) for model in models]

    def select_query(self, *, for_update: bool = False) -> Select:
        query = select(self.model)
        return query.with_for_update() if for_update else query

    def get_by_id_query(self, identifier: T_ID, *, for_update: bool = False) -> Select:
        return self.select_query(for_update=for_update).where(self.get_filter_by_id_expression(identifier))
