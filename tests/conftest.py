from collections.abc import AsyncIterator, Generator
from contextlib import asynccontextmanager
from uuid import uuid4

import asyncpg  # type: ignore[import-untyped]
import pytest

from sqlalchemy.engine import make_url
from testcontainers.community.postgres import PostgresContainer

from core.settings.postgres import ContainerSettings
from db.database import Database
from db.session import BaseSessionManager
from support import UserRepository


@pytest.fixture(scope="session")
def make_db() -> Generator[PostgresContainer, None, None]:
    settings = ContainerSettings()
    with PostgresContainer(f"postgres:{settings.VERSION}", driver="asyncpg") as postgres:
        yield postgres


async def _admin_connection(postgres: PostgresContainer) -> asyncpg.Connection:
    return await asyncpg.connect(
        host=postgres.get_container_host_ip(),
        port=int(postgres.get_exposed_port(5432)),
        user=postgres.username,
        password=postgres.password,
        database=postgres.dbname,
    )


@asynccontextmanager
async def _temporary_database(postgres: PostgresContainer) -> AsyncIterator[Database]:
    database_name = f"test_{uuid4().hex}"
    admin = await _admin_connection(postgres)
    try:
        await admin.execute(f'CREATE DATABASE "{database_name}"')
    finally:
        await admin.close()

    database_url = make_url(postgres.get_connection_url()).set(database=database_name)
    database = Database(database_url.render_as_string(hide_password=False))
    try:
        await database.create_database()
        yield database
    finally:
        await database.dispose()
        admin = await _admin_connection(postgres)
        try:
            await admin.execute(f'DROP DATABASE "{database_name}" WITH (FORCE)')
        finally:
            await admin.close()


@pytest.fixture
async def database(make_db: PostgresContainer) -> AsyncIterator[Database]:
    async with _temporary_database(make_db) as database:
        yield database


@pytest.fixture
async def audit_database(make_db: PostgresContainer) -> AsyncIterator[Database]:
    async with _temporary_database(make_db) as database:
        yield database


@pytest.fixture
def manager(database: Database) -> BaseSessionManager:
    return BaseSessionManager(database.session_factory)


@pytest.fixture
def repository(manager: BaseSessionManager) -> UserRepository:
    return UserRepository(manager)
