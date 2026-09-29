import asyncio

from unittest.mock import Mock

import pytest

from sqlalchemy import text
from sqlalchemy.dialects import postgresql
from sqlalchemy.exc import DBAPIError, IntegrityError

from db.database import Database
from db.session import BaseSessionManager, SessionFactoryProtocol
from repositories.exceptions import NotFoundInRepositoryError, RepositoryError
from support import User, UserGet, UserInsert, UserRepository, UserUpdate


READS = [
    ("get_by_id", (1,)),
    ("get_or_none_by_id", (1,)),
    ("get_by", ("name", "Ada")),
    ("get_or_none_by", ("name", "Ada")),
    ("get_all", ()),
]


@pytest.mark.parametrize("method,args", READS)
@pytest.mark.parametrize("for_update", [None, False, True])
async def test_read_results(
    repository: UserRepository,
    method: str,
    args: tuple[object, ...],
    for_update: bool | None,
) -> None:
    expected = await repository.insert(UserInsert(name="Ada"))
    kwargs = {} if for_update is None else {"for_update": for_update}
    result = await getattr(repository, method)(*args, **kwargs)
    assert result == ([expected] if method == "get_all" else expected)


@pytest.mark.parametrize("for_update", [False, True])
def test_postgres_locking_queries(for_update: bool) -> None:
    repository = UserRepository(Mock(spec=SessionFactoryProtocol))
    query = repository.get_by_id_query(42, for_update=for_update)
    compiled = query.compile(dialect=postgresql.dialect())
    assert ("FOR UPDATE" in str(compiled)) == for_update
    assert compiled.params == {"id_1": 42}
    assert (
        "FOR UPDATE"
        in str(
            repository.select_query(for_update=for_update).compile(
                dialect=postgresql.dialect(),
            )
        )
    ) == for_update


async def test_for_update_locks_selected_row(
    database: Database,
    manager: BaseSessionManager,
    repository: UserRepository,
) -> None:
    user = await repository.insert(UserInsert(name="Ada"))
    contender_manager = BaseSessionManager(database.session_factory)
    contender = UserRepository(contender_manager)

    async with manager.context_session():
        assert await repository.get_by_id(user.id, for_update=True) == user

        async def try_to_lock_row() -> None:
            async with database.session_factory() as session:
                await session.execute(text("SET LOCAL lock_timeout = '250ms'"))
                async with contender_manager.context_session(session):
                    await contender.get_by_id(user.id, for_update=True)

        with pytest.raises(DBAPIError):
            await asyncio.create_task(try_to_lock_row())

    assert await contender.get_by_id(user.id, for_update=True) == user


@pytest.mark.parametrize("method,args", READS[:-1])
async def test_missing_record_contract(
    repository: UserRepository,
    method: str,
    args: tuple[object, ...],
) -> None:
    assert repository.DoesNotExist is NotFoundInRepositoryError
    if method.startswith("get_or_none"):
        assert await getattr(repository, method)(*args) is None
    else:
        with pytest.raises(NotFoundInRepositoryError, match="not found") as caught:
            await getattr(repository, method)(*args)
        assert isinstance(caught.value, RepositoryError)


@pytest.mark.parametrize(
    "data,fields,expected_name,expected_description",
    [
        (UserUpdate(name="Grace", description="new"), {"name"}, "Grace", "internal"),
        (UserUpdate(description=None), {"description"}, "Ada", None),
        (UserUpdate(name="Grace"), {"name", "description"}, "Grace", "internal"),
        (UserUpdate(name="Grace"), set(), "Ada", "internal"),
        (UserUpdate(name="Grace"), {"description"}, "Ada", "internal"),
        (UserUpdate(), None, "Ada", "internal"),
    ],
)
@pytest.mark.parametrize("exists", [False, True])
async def test_update_field_selection(
    database: Database,
    repository: UserRepository,
    data: UserUpdate,
    fields: set[str] | None,
    expected_name: str,
    expected_description: str | None,
    exists: bool,
) -> None:
    if exists:
        await repository.insert(UserInsert(name="Ada", description="internal"))
    result = await repository.update(1, data, update_fields=fields)
    assert result == (UserGet(id=1, name=expected_name) if exists else None)
    async with database.session_factory() as session:
        row = await session.get(User, 1)
        if exists:
            assert row is not None
            assert row.name == expected_name
            assert row.description == expected_description
        else:
            assert row is None


async def test_duplicate_insert_raises_real_database_error(repository: UserRepository) -> None:
    user = await repository.insert(UserInsert(name="Ada"))
    with pytest.raises(IntegrityError):
        await repository.insert(UserInsert(name="Ada"))
    assert await repository.get_all() == [user]
    assert (await repository.insert(UserInsert(name="Grace"))).name == "Grace"


async def test_null_required_field_rolls_back(repository: UserRepository) -> None:
    user = await repository.insert(UserInsert(name="Ada"))
    with pytest.raises(IntegrityError):
        await repository.update(user.id, UserUpdate(name=None))
    assert await repository.get_by_id(user.id) == user


async def test_missing_insert_result_raises_repository_error(
    database: Database,
    repository: UserRepository,
) -> None:
    async with database.session_factory() as session:
        await session.execute(
            text(
                """
                CREATE FUNCTION skip_user_insert() RETURNS trigger AS $$
                BEGIN
                    RETURN NULL;
                END;
                $$ LANGUAGE plpgsql
                """,
            )
        )
        await session.execute(
            text(
                """
                CREATE TRIGGER skip_user
                BEFORE INSERT ON repository_test_users
                FOR EACH ROW EXECUTE FUNCTION skip_user_insert()
                """,
            )
        )
    with pytest.raises(RepositoryError, match="INSERT"):
        await repository.insert(UserInsert(name="Ada"))
    assert await repository.get_all() == []


def test_object_to_dict() -> None:
    assert UserRepository._object_to_dict(UserInsert(name="Ada", description="internal")) == {
        "name": "Ada",
        "description": "internal",
    }
    assert UserRepository._object_to_dict(UserUpdate()) == {"name": None, "description": None}
    assert UserRepository._object_to_dict(UserUpdate(), exclude_unset=True) == {}
    assert UserRepository._object_to_dict(
        UserUpdate(name="Ada", description=None),
        include={"description"},
        exclude_unset=True,
    ) == {"description": None}
