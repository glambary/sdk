"""Static checks: mypy --warn-unused-ignores tests/typing/session_types.py."""

from contextlib import AbstractAsyncContextManager
from typing import assert_type

from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from db.session import BaseSessionManager, SessionFactoryProtocol
from repositories.mixins.core import RepositoryCore


def check_session_factory_types(
    manager: BaseSessionManager,
    factory: SessionFactoryProtocol,
) -> None:
    RepositoryCore[BaseModel, int](manager)
    RepositoryCore[BaseModel, int](factory)
    RepositoryCore[BaseModel, int](object())  # type: ignore[arg-type]
    RepositoryCore[BaseModel, int](manager.session_factory)  # type: ignore[arg-type]

    assert_type(factory.context_session(), AbstractAsyncContextManager[AsyncSession])
    assert_type(factory.context_session(None), AbstractAsyncContextManager[AsyncSession])
