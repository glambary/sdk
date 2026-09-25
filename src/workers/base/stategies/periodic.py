from datetime import time
from typing import Any


class PeriodicStrategy:
    """
    Периодическая стратегия.

    Example:
    Каждые 72 часа.
    PeriodicStrategy(period=72 * 60 * 60).
    """

    _period: float
    _start_time: time | None

    def __init__(self, period: float | int, start_time: time | None = None) -> None:
        self._period = float(period)
        self._start_time = start_time

    def next_delay(self, *_: tuple[Any, ...], **__: dict[str, Any]) -> float:
        return self._period
