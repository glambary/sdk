"""Static checks: mypy --follow-imports=silent tests/typing/repository_types.py."""

from typing import assert_type

from pydantic import BaseModel

from repositories.base import BaseRepository


class Read(BaseModel):
    id: int
    name: str


class Create(BaseModel):
    name: str


class Update(BaseModel):
    name: str | None = None


class ConcreteRepository(BaseRepository[Read, int, Create, Update]):
    pass


async def check_repository_types(
    defaults: BaseRepository[Read, int],
    custom_insert: BaseRepository[Read, int, Create],
    custom_update: BaseRepository[Read, int, Read, Update],
    custom_both: BaseRepository[Read, int, Create, Update],
    concrete: ConcreteRepository,
) -> None:
    read = Read(id=1, name="Ada")
    create = Create(name="Ada")
    update = Update(name="Grace")

    assert_type(await defaults.insert(read), Read)
    assert_type(await defaults.update(1, read), Read | None)
    assert_type(await custom_insert.insert(create), Read)
    assert_type(await custom_insert.update(1, read), Read | None)
    assert_type(await custom_update.insert(read), Read)
    assert_type(await custom_update.update(1, update), Read | None)
    assert_type(await custom_both.insert(create), Read)
    assert_type(await custom_both.update(1, update), Read | None)
    assert_type(await concrete.get_by_id(1), Read)
    assert_type(await concrete.get_by("name", "Ada"), Read)
    assert_type(await concrete.get_or_none_by_id(1), Read | None)
    assert_type(await concrete.get_or_none_by("name", "Ada"), Read | None)
    assert_type(await concrete.update(1, update, update_fields={"name"}), Read | None)
    assert_type(await concrete.get_all(), list[Read])
    assert_type(await concrete.insert(create), Read)
    assert_type(await concrete.update(1, update), Read | None)

    # These calls must be rejected; --warn-unused-ignores detects lost type safety.
    await defaults.insert(create)  # type: ignore[arg-type]
    await defaults.update(1, update)  # type: ignore[arg-type]
    await custom_insert.update(1, update)  # type: ignore[arg-type]
    await custom_update.insert(create)  # type: ignore[arg-type]
    await custom_both.insert(read)  # type: ignore[arg-type]
    await custom_both.update(1, read)  # type: ignore[arg-type]
    await custom_both.update("1", update)  # type: ignore[arg-type]
