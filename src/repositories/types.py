from typing import TypeVar

from pydantic import BaseModel


T = TypeVar("T", bound=BaseModel)
T_ID = TypeVar("T_ID")
T_INSERT = TypeVar("T_INSERT", bound=BaseModel, default=T)
T_UPDATE = TypeVar("T_UPDATE", bound=BaseModel, default=T)
