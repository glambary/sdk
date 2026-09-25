from collections.abc import AsyncIterator, Callable
from contextlib import AbstractAsyncContextManager, asynccontextmanager
from contextvars import ContextVar

from sqlalchemy.ext.asyncio import AsyncSession

_current_session: ContextVar[AsyncSession | None] = ContextVar(
    "db_session",
    default=None,
)


class BaseSessionManager:
    def __init__(
        self,
        session_factory: Callable[..., AbstractAsyncContextManager[AsyncSession]],
    ) -> None:
        self.session_factory = session_factory

    def use_or_create_session(
        self,
        session: AsyncSession | None = None,
    ) -> AbstractAsyncContextManager[AsyncSession]:
        return self.context_session(session)

    @asynccontextmanager
    async def context_session(
        self, session: AsyncSession | None = None
    ) -> AsyncIterator[AsyncSession]:
        current_session = _current_session.get()

        if session is None and current_session is not None:
            yield current_session
            return

        if session is not None:
            session: AsyncSession

            if session is current_session:
                yield session
                return

            token = _current_session.set(session)
            try:
                yield session
            finally:
                _current_session.reset(token)
            return

        async with self.session_factory() as created_session:
            token = _current_session.set(created_session)
            try:
                yield created_session
            finally:
                _current_session.reset(token)
