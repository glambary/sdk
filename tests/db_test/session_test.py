import asyncio

import pytest

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError

from db.database import Database
from db.session import BaseSessionManager
from support import User


async def test_inherited_session_is_reused(manager: BaseSessionManager) -> None:
    async with manager.context_session() as outer:
        async with manager.context_session() as nested:
            assert nested is outer
            assert manager._current_session.get() is outer
        assert manager._current_session.get() is outer
    assert manager._current_session.get() is None
    async with manager.context_session() as fresh:
        assert fresh is not outer


async def test_external_session_remains_in_its_transaction(
    database: Database,
    manager: BaseSessionManager,
) -> None:
    async with database.session_factory() as external:
        external.add(User(name="Ada"))
        await external.flush()
        transaction = external.get_transaction()
        async with manager.context_session(external) as current:
            assert current is external
            async with manager.context_session() as nested:
                assert nested is external
        assert external.get_transaction() is transaction
        assert transaction is not None and transaction.is_active
        external.add(User(name="Grace"))
        await external.flush()
        assert manager._current_session.get() is None
    async with database.session_factory() as session:
        assert await session.get(User, 1) is not None
        assert await session.get(User, 2) is not None


async def test_external_override_restores_outer_session(
    database: Database,
    manager: BaseSessionManager,
) -> None:
    async with manager.context_session() as outer, database.session_factory() as external:
        async with manager.context_session(external) as current:
            assert current is external
            async with manager.context_session(external) as repeated:
                assert repeated is external
        assert manager._current_session.get() is outer
    assert manager._current_session.get() is None


async def test_commit_failure_rolls_back_and_clears_context(
    database: Database,
    manager: BaseSessionManager,
) -> None:
    with pytest.raises(IntegrityError):
        async with manager.context_session() as session:
            session.add_all([User(name="Ada"), User(name="Ada")])
    assert manager._current_session.get() is None
    async with database.session_factory() as session:
        assert (await session.scalars(select(User))).all() == []
    async with manager.context_session() as session:
        session.add(User(name="Grace"))
    async with database.session_factory() as session:
        row = await session.scalar(select(User).where(User.name == "Grace"))
        assert row is not None
        assert row.name == "Grace"


async def test_concurrent_tasks_have_independent_sessions(manager: BaseSessionManager) -> None:
    barrier = asyncio.Barrier(2)

    async def open_session() -> int:
        async with manager.context_session() as session:
            await barrier.wait()
            async with manager.context_session() as nested:
                assert nested is session
            return id(session)

    first, second = await asyncio.gather(open_session(), open_session())
    assert first != second
    assert manager._current_session.get() is None
