import pickle

import pytest

from core.exceptions import ProjectError
from repositories.exceptions import NotFoundInRepositoryError, RepositoryError


@pytest.mark.parametrize(
    "error_type,expected",
    [
        (ProjectError, "ProjectError"),
        (RepositoryError, "A repository operation failed"),
        (NotFoundInRepositoryError, "The record was not found"),
    ],
)
@pytest.mark.parametrize("message", [None, ""])
def test_default_messages(
    error_type: type[ProjectError],
    expected: str,
    message: str | None,
) -> None:
    error = error_type(message)
    assert isinstance(error, ProjectError)
    assert str(error) == error.message == expected
    assert error.args == (expected,)


@pytest.mark.parametrize("error_type", [ProjectError, RepositoryError, NotFoundInRepositoryError])
@pytest.mark.parametrize("message", ["Invalid JSON: {data}", "Missing {key}"])
def test_custom_messages_are_literal(error_type: type[ProjectError], message: str) -> None:
    error = error_type(message)
    assert error.message == str(error) == message
    assert error.args == (message,)


def test_exception_hierarchy() -> None:
    assert issubclass(NotFoundInRepositoryError, RepositoryError)
    assert issubclass(RepositoryError, ProjectError)


@pytest.mark.parametrize("error_type", [ProjectError, RepositoryError, NotFoundInRepositoryError])
def test_exception_roundtrip_preserves_message(error_type: type[ProjectError]) -> None:
    error = error_type("Missing user")
    restored = pickle.loads(pickle.dumps(error))  # noqa: S301 -- roundtrip of a locally created exception
    assert type(restored) is error_type
    assert restored.args == error.args
    assert restored.message == error.message
