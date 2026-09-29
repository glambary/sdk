from core.exceptions import ProjectError


class RepositoryError(ProjectError):
    """A repository operation could not be completed."""

    message = "A repository operation failed"


class NotFoundInRepositoryError(RepositoryError):
    """The requested record does not exist in the repository."""

    message = "The record was not found"
