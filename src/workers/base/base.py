import asyncio
import logging
from typing import Any, Self

logger = logging.getLogger(__name__)


class BaseWorker:
    name: str
    __items: dict[str, type[Self]] = {}

    def __init__(self) -> None:
        self._on_started = asyncio.Event()
        self._on_stopped = asyncio.Event()

    def __init_subclass__(cls, **kwargs: Any) -> None:
        BaseWorker.__items[cls.name] = cls

    def start(self) -> None:
        if self._is_start_allowed():
            self._on_started.set()

        asyncio.run(self._run_async())

    def stop(self) -> None:
        self._on_stopped.set()

    @classmethod
    def get_worker_class(cls, name: str) -> type[Self] | None:
        return cls.__items.get(name)

    @classmethod
    def get_worker_names(cls) -> list[str]:
        return list(cls.__items)

    async def _run_async(self) -> None:
        try:
            await self._run_loop()
        except Exception as exc:
            logger.exception(f"Exception during periodic task: {exc=}")

    # to set -----------------------------------------------------------------
    def _is_start_allowed(self) -> bool:
        raise NotImplementedError

    async def _run_loop(self) -> None:
        raise NotImplementedError
