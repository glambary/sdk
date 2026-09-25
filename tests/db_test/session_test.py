from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from contextvars import ContextVar, Token
from typing import cast

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from db import session as session_module
from db.session import BaseSessionManager


class TrackingContextVar:
    def __init__(self) -> None:
        self._value: ContextVar[object | None] = session_module._current_session
        self.set_count = 0

    def get(self) -> object | None:
        return self._value.get()

    def set(self, value: object) -> Token[object | None]:
        self.set_count += 1
        return self._value.set(value)

    def reset(self, token: Token[object | None]) -> None:
        self._value.reset(token)


class FalseySession:
    def __bool__(self) -> bool:
        return False


async def test_inherited_session_is_reused_without_setting_context(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    context = TrackingContextVar()
    monkeypatch.setattr(session_module, "_current_session", context)
    external_session = cast(AsyncSession, object())

    @asynccontextmanager
    async def session_factory() -> AsyncIterator[AsyncSession]:
        raise AssertionError("session factory should not be called")
        yield cast(AsyncSession, object())

    manager = BaseSessionManager(session_factory)

    async with (
        manager.context_session(external_session) as outer_session,
        manager.context_session() as nested_session,
    ):
        assert outer_session is external_session
        assert nested_session is external_session
        assert context.set_count == 1

    assert context.set_count == 1
    assert context.get() is None


async def test_external_session_is_not_closed() -> None:
    factory_calls = 0
    external_session = cast(AsyncSession, FalseySession())

    @asynccontextmanager
    async def session_factory() -> AsyncIterator[AsyncSession]:
        nonlocal factory_calls
        factory_calls += 1
        raise AssertionError("session factory should not be called")
        yield cast(AsyncSession, object())

    manager = BaseSessionManager(session_factory)

    async with manager.context_session(external_session) as session:
        assert session is external_session

    assert factory_calls == 0


@pytest.mark.asyncio
async def test_created_session_is_reused_and_factory_closes_it(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    context = TrackingContextVar()
    monkeypatch.setattr(session_module, "_current_session", context)
    session = cast(AsyncSession, object())
    factory_calls = 0
    factory_closed = False

    @asynccontextmanager
    async def session_factory() -> AsyncIterator[AsyncSession]:
        nonlocal factory_calls, factory_closed
        factory_calls += 1
        try:
            yield session
        finally:
            factory_closed = True

    manager = BaseSessionManager(session_factory)

    async with (
        manager.context_session() as outer_session,
        manager.context_session() as nested_session,
    ):
        assert outer_session is session
        assert nested_session is session
        assert factory_calls == 1

    assert factory_calls == 1
    assert factory_closed
    assert context.set_count == 1
    assert context.get() is None
