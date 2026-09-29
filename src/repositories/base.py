from typing import Generic

from repositories.mixins.delete import DeleteMixin
from repositories.mixins.get import GetMixin
from repositories.mixins.insert import InsertMixin
from repositories.mixins.update import UpdateMixin
from repositories.types import T_ID, T_INSERT, T_UPDATE, T


class BaseRepository(
    InsertMixin[T, T_ID, T_INSERT],
    UpdateMixin[T, T_ID, T_UPDATE],
    DeleteMixin[T, T_ID],
    GetMixin[T, T_ID],
    Generic[T, T_ID, T_INSERT, T_UPDATE],
):
    """CRUD with a required result schema and default input types T.

    Example:
    class UserRepository(BaseRepository[UserGet, int, UserCreate, UserUpdate]):
        _model = User

    """
