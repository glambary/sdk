from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from db.models.base import Base


class Database:
    def __init__(
        self,
        db_url: str,
        echo: bool = False,
        **engine_options: Any,
    ) -> None:
        self._engine = create_async_engine(
            db_url,
            echo=echo,
            **engine_options,
        )
        self._session_factory = async_sessionmaker(
            autocommit=False,
            autoflush=False,
            expire_on_commit=False,
            bind=self._engine,
        )

    async def create_database(self) -> None:
        async with self._engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)

    @asynccontextmanager
    async def session_factory(
        self,
    ) -> AsyncIterator[AsyncSession]:
        session: AsyncSession = self._session_factory()
        try:
            yield session
            await session.commit()
        except BaseException:
            await session.rollback()
            raise
        finally:
            await session.close()

    async def dispose(self) -> None:
        """Close all pooled database connections owned by this instance."""
        await self._engine.dispose()
