import pytest

from sqlalchemy.exc import IntegrityError

from db.database import Database
from db.session import BaseSessionManager
from repositories.exceptions import NotFoundInRepositoryError
from support import User, UserGet, UserInsert, UserRepository, UserUpdate


async def test_crud_reuses_transaction_and_commits(
    database: Database,
    manager: BaseSessionManager,
    repository: UserRepository,
) -> None:
    async with manager.context_session() as session:
        user = await repository.insert(UserInsert(name="Ada"))
        assert await session.get(User, user.id) is not None
        assert await repository.get_by_id(user.id) == user
        assert await repository.get_by("name", "Ada") == user
        assert await repository.get_all() == [user]
        assert await repository.update(user.id, UserUpdate(name="Grace")) == UserGet(id=user.id, name="Grace")
        assert await repository.delete(user.id)
        assert not await repository.delete(user.id)
        assert await repository.get_all() == []
        saved = await repository.insert(UserInsert(name="Linus"))
    async with database.session_factory() as session:
        row = await session.get(User, saved.id)
        assert row is not None
        assert row.name == "Linus"
    assert manager._current_session.get() is None


async def test_real_database_error_rolls_back_entire_repository_transaction(
    manager: BaseSessionManager,
    repository: UserRepository,
) -> None:
    with pytest.raises(IntegrityError):
        async with manager.context_session():
            await repository.insert(UserInsert(name="Ada"))
            await repository.insert(UserInsert(name="Ada"))
    assert manager._current_session.get() is None
    assert await repository.get_all() == []
    assert (await repository.insert(UserInsert(name="Grace"))).name == "Grace"


@pytest.mark.parametrize("fail", [False, True])
async def test_repository_contexts_are_isolated_and_cleaned_up(
    database: Database,
    audit_database: Database,
    fail: bool,
) -> None:
    main = BaseSessionManager(database.session_factory)
    audit = BaseSessionManager(audit_database.session_factory)
    users, events = UserRepository(main), UserRepository(audit)
    user = await users.insert(UserInsert(name="Ada"))
    event = await events.insert(UserInsert(name="Grace"))

    async def run() -> None:
        async with main.context_session() as main_session:
            assert await users.get_by_id(user.id) == user
            assert await events.get_by_id(event.id) == event
            assert audit._current_session.get() is None
            async with audit.context_session() as audit_session:
                assert main_session is not audit_session
                assert await events.update(event.id, UserUpdate()) == event
                assert await users.get_by_id(user.id) == user
                if fail:
                    await users.get_by_id(999)

    if fail:
        with pytest.raises(NotFoundInRepositoryError):
            await run()
    else:
        await run()
    assert main._current_session.get() is None
    assert audit._current_session.get() is None
    assert await users.get_all() == [user]
    assert await events.get_all() == [event]
