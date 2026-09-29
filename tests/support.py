from pydantic import BaseModel
from sqlalchemy.orm import Mapped, mapped_column

from db.models.base import Base
from repositories.base import BaseRepository


class User(Base):
    __tablename__ = "repository_test_users"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(unique=True)
    description: Mapped[str | None]


class UserInsert(BaseModel):
    name: str
    description: str | None = None


class UserUpdate(BaseModel):
    name: str | None = None
    description: str | None = None


class UserGet(BaseModel):
    id: int
    name: str


class UserRepository(BaseRepository[UserGet, int, UserInsert, UserUpdate]):
    _model = User


class DefaultUserRepository(BaseRepository[UserGet, int]):
    _model = User


class CustomInsertRepository(BaseRepository[UserGet, int, UserInsert]):
    _model = User


class CustomUpdateRepository(BaseRepository[UserGet, int, UserGet, UserUpdate]):
    _model = User
