from collections.abc import AsyncIterator, Callable
from contextlib import AbstractAsyncContextManager, asynccontextmanager
from contextvars import ContextVar
from typing import Protocol

from sqlalchemy.ext.asyncio import AsyncSession


class SessionFactoryProtocol(Protocol):
    """Provide an existing or newly created session within an async context."""

    def context_session(
        self,
        session: AsyncSession | None = None,
    ) -> AbstractAsyncContextManager[AsyncSession]:
        """Reuse the supplied/current session, or manage a new session's lifetime."""
        ...


class BaseSessionManager:
    def __init__(
        self,
        session_factory: Callable[..., AbstractAsyncContextManager[AsyncSession]],
    ) -> None:
        self.session_factory = session_factory
        self._current_session: ContextVar[AsyncSession | None] = ContextVar("db_session", default=None)

    @asynccontextmanager
    async def context_session(self, session: AsyncSession | None = None) -> AsyncIterator[AsyncSession]:
        current_session = self._current_session.get()

        if session is None and current_session is not None:
            yield current_session
            return

        if session is not None:
            if session is current_session:
                yield session
                return

            token = self._current_session.set(session)
            try:
                yield session
            finally:
                self._current_session.reset(token)
            return

        async with self.session_factory() as created_session:
            token = self._current_session.set(created_session)
            try:
                yield created_session
            finally:
                self._current_session.reset(token)
