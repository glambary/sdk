import pytest

from sqlalchemy import select

from db.database import Database
from db.session import BaseSessionManager
from repositories.base import BaseRepository
from support import (
    CustomInsertRepository,
    CustomUpdateRepository,
    DefaultUserRepository,
    User,
    UserGet,
    UserInsert,
    UserRepository,
    UserUpdate,
)


async def test_insert_persists_row_and_returns_public_schema(database: Database, repository: UserRepository) -> None:
    result = await repository.insert(UserInsert(name="Ada", description="internal"))
    assert result == UserGet(id=1, name="Ada")
    assert "description" not in result.model_dump()
    async with database.session_factory() as session:
        row = await session.get(User, result.id)
        assert row is not None
        assert row.description == "internal"


async def test_update_preserves_unset_fields(database: Database, repository: UserRepository) -> None:
    user = await repository.insert(UserInsert(name="Ada", description="internal"))
    assert await repository.update(user.id, UserUpdate(name="Grace")) == UserGet(id=user.id, name="Grace")
    async with database.session_factory() as session:
        row = await session.get(User, user.id)
        assert row is not None
        assert row.description == "internal"


async def test_empty_update_reads_existing_row(repository: UserRepository) -> None:
    user = await repository.insert(UserInsert(name="Ada", description="internal"))
    assert await repository.update(user.id, UserUpdate()) == user
    assert await repository.update(999, UserUpdate()) is None


async def test_explicit_none_is_persisted(database: Database, repository: UserRepository) -> None:
    user = await repository.insert(UserInsert(name="Ada", description="internal"))
    await repository.update(user.id, UserUpdate(description=None))
    async with database.session_factory() as session:
        assert await session.scalar(select(User.description).where(User.id == user.id)) is None
        assert await session.get(User, user.id) is not None


@pytest.mark.parametrize(
    "repository_class", [DefaultUserRepository, CustomInsertRepository, CustomUpdateRepository, UserRepository]
)
async def test_input_defaults_and_overrides(database: Database, repository_class: type[BaseRepository]) -> None:
    repository = repository_class(BaseSessionManager(database.session_factory))
    create_data = (
        UserInsert(name="Ada", description="internal")
        if repository_class in (CustomInsertRepository, UserRepository)
        else UserGet(id=1, name="Ada")
    )
    update_data = (
        UserUpdate(name="Grace")
        if repository_class in (CustomUpdateRepository, UserRepository)
        else UserGet(id=1, name="Grace")
    )
    assert await repository.insert(create_data) == UserGet(id=1, name="Ada")
    assert await repository.update(1, update_data) == UserGet(id=1, name="Grace")
    async with database.session_factory() as session:
        row = await session.get(User, 1)
        assert row is not None
        assert row.name == "Grace"
        assert row.description == ("internal" if isinstance(create_data, UserInsert) else None)
