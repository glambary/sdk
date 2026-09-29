# sdk

Repository reads:

- `get_by_id(identifier)` and `get_by(field, value)` return the result schema or
  raise `repository.DoesNotExist` (an alias of `repositories.NotFoundInRepository`).
- `get_or_none_by_id(identifier)` and `get_or_none_by(field, value)` return `None`
  when the record does not exist.
- All read methods, including `get_all`, accept `for_update=False`. Set it to
  `True` to generate `SELECT ... FOR UPDATE`. `select_query` and
  `get_by_id_query` accept the same option.

Keep locking reads and subsequent writes in the same transaction/session context:

```python
async with repository.session_factory.context_session():
    user = await repository.get_by_id(user_id, for_update=True)
    updated = await repository.update(user.id, patch, update_fields={"name"})
```

`update_fields` optionally restricts the fields written by `update`; other fields
are excluded. Only explicitly set input fields are written, including explicit
`None` values. An empty set performs no write and reads the current record.
`update` returns `None` if the record is absent, including for an empty patch.

`_object_to_dict(obj, *, include=None, exclude_unset=False)` converts Pydantic
input schemas to dictionaries and is shared by `insert` and `update`.
`_parse_object` validates database objects using the repository's `_result_schema`.

The shared `ProjectError` is defined in `core.exceptions`. Repository-specific
errors live in `repositories.exceptions` and inherit from it:
`ProjectError → RepositoryError → NotFoundInRepository`.
Catch `ProjectError` for application failures, `RepositoryError` for repository
failures, or `repository.DoesNotExist` for a missing record. Database driver
exceptions are not automatically translated.

Each error has a stable `code` and a literal `message` (also returned by `str(error)`). Subclasses can override `code` and
`default_message`. Only `message=None` selects the default; an empty string is
preserved.

```python
from repositories.exceptions import RepositoryError

raise RepositoryError(
    "Could not save the record",
)
```

When translating another exception, use `raise RepositoryError(...) from exc`
to preserve its cause. Repository errors remain importable from `repositories`
and `repositories.exceptions`.

Other layers can define their own errors independently of repositories:

```python
from core.exceptions import ProjectError


class ServiceError(ProjectError):
    code = "service_error"
    default_message = "A service operation failed."
```
