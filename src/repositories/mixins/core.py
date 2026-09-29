from typing import Any, Generic, get_args

from pydantic import BaseModel
from sqlalchemy.sql.elements import ColumnElement

from db.models.base import Base
from db.session import SessionFactoryProtocol
from repositories.exceptions import NotFoundInRepositoryError
from repositories.types import T_ID, T


class RepositoryCore(Generic[T, T_ID]):
    """Shared model, session management and result validation for CRUD mixins."""

    DoesNotExist = NotFoundInRepositoryError

    _id_attribute = "id"
    _model: type[Base]
    _result_schema: type[T]

    def __init_subclass__(cls, **kwargs: Any) -> None:
        super().__init_subclass__(**kwargs)
        for base in getattr(cls, "__orig_bases__", ()):
            args = get_args(base)
            if args and isinstance(args[0], type):
                cls._result_schema = args[0]
                break

    def __init__(
        self,
        session_factory: SessionFactoryProtocol,
    ) -> None:
        self.session_factory: SessionFactoryProtocol = session_factory

    @property
    def model(self) -> type[Base]:
        return self._model

    def get_filter_by_id_expression(self, identifier: T_ID) -> ColumnElement[bool]:
        return getattr(self.model, self._id_attribute) == identifier

    def _parse_object(self, model: Base) -> T:
        return self._result_schema.model_validate(model, from_attributes=True)

    @staticmethod
    def _object_to_dict(
        obj: BaseModel,
        *,
        include: set[str] | None = None,
        exclude_unset: bool = False,
    ) -> dict[str, Any]:
        """Convert an input schema to values for a database write."""
        return obj.model_dump(include=include, exclude_unset=exclude_unset)
